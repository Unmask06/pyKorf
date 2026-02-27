"""KdfParser – low-level reader / writer for KORF .kdf files.

The parser preserves the exact line order found in the file so that a
round-trip ``load → save`` produces an identical file (modulo any values
that were explicitly changed).

Internal representation
-----------------------
Each file line is stored as a ``KdfRecord``::

    KdfRecord(
        element_type = "PIPE"   # e.g. GEN, PIPE, PUMP …
        index        = 1        # element instance index (0 = template/default)
        param        = "TFLOW"  # parameter keyword
        values       = ["50;55;20", 20, "t/h"]   # remaining CSV tokens
        raw_line     = ...      # original text line (for comments / unknown lines)
    )

Lines that do not match the ``"\\ETYPE",idx,"PARAM",... `` pattern (such as
the version header ``"KORF_2.0"``) are stored as *verbatim* records with
``element_type=None``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from pykorf.exceptions import ParseError
from pykorf.utils import format_line, parse_line

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class KdfRecord:
    """Represents one parsed line of a .kdf file."""

    element_type: str | None  # None for verbatim / header lines
    index: int | None
    param: str | None
    values: list  # token list after element/index/param
    raw_line: str = field(default="", repr=False)  # original text

    # ------------------------------------------------------------------
    def key(self) -> tuple | None:
        """Return ``(element_type, index, param)`` or None for verbatim lines."""
        if self.element_type is None:
            return None
        return (self.element_type, self.index, self.param)

    def to_line(self) -> str:
        """Serialise back to a KDF text line."""
        if self.element_type is None:
            return self.raw_line
        # Re-build: "\TYPE",idx,"PARAM",...
        parts: list = [f"\\{self.element_type}", self.index, self.param] + self.values
        return format_line(parts)


# Matches the opening backslash element type token: \PIPE, \PUMP etc.
# Note: quotes are already stripped by the csv.reader.
_ETYPE_RE = re.compile(r'^\\([A-Z]+)$', re.IGNORECASE)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class KdfParser:
    """Read and write KORF .kdf files.

    Parameters
    ----------
    path:
        File-system path to the .kdf file.
    encoding:
        File encoding (default ``"latin-1"`` which covers all Korf files).
    """

    ENCODING = "latin-1"

    def __init__(self, path: str | Path, encoding: str = ENCODING):
        self.path = Path(path)
        self.encoding = encoding
        self._records: list[KdfRecord] = []

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load(self) -> list[KdfRecord]:
        """Parse the .kdf file and return the list of :class:`KdfRecord`."""
        if not self.path.exists():
            raise ParseError(f"File not found: {self.path}")
        self._records = []
        with self.path.open(encoding=self.encoding, errors="replace") as fh:
            for lineno, raw in enumerate(fh, 1):
                stripped = raw.rstrip("\r\n")
                record = self._parse_line(stripped, lineno)
                self._records.append(record)
        return self._records

    def _parse_line(self, line: str, lineno: int) -> KdfRecord:
        if not line.strip():
            return KdfRecord(None, None, None, [], raw_line=line)

        tokens = parse_line(line)
        if not tokens:
            return KdfRecord(None, None, None, [], raw_line=line)

        # Check for element-type token  e.g. "\PIPE"
        m = _ETYPE_RE.match(tokens[0])
        if m and len(tokens) >= 3:
            etype = m.group(1).upper()
            try:
                idx = int(tokens[1])
            except (ValueError, IndexError):
                # Not a structured line – store verbatim
                return KdfRecord(None, None, None, [], raw_line=line)
            param = tokens[2].strip('"').upper()
            values = tokens[3:]
            return KdfRecord(etype, idx, param, values, raw_line=line)

        # Verbatim line (version header, blank, unknown)
        return KdfRecord(None, None, None, [], raw_line=line)

    # ------------------------------------------------------------------
    # Saving
    # ------------------------------------------------------------------

    def save(self, path: str | Path | None = None) -> None:
        """Write the (possibly modified) records back to a .kdf file.

        Parameters
        ----------
        path:
            Destination path; if *None*, overwrites the source file.
        """
        dest = Path(path) if path else self.path
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("w", encoding=self.encoding, newline="\r\n") as fh:
            for rec in self._records:
                fh.write(rec.to_line() + "\r\n")

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    @property
    def records(self) -> list[KdfRecord]:
        return self._records

    def get(
        self,
        element_type: str,
        index: int,
        param: str,
    ) -> KdfRecord | None:
        """Return the first matching record, or *None*."""
        et = element_type.upper()
        p = param.upper()
        for rec in self._records:
            if rec.element_type == et and rec.index == index and rec.param == p:
                return rec
        return None

    def get_all(self, element_type: str, index: int) -> list[KdfRecord]:
        """Return all records for a given ``(element_type, index)``."""
        et = element_type.upper()
        return [r for r in self._records if r.element_type == et and r.index == index]

    def set_value(
        self,
        element_type: str,
        index: int,
        param: str,
        values: list,
    ) -> bool:
        """Replace the ``values`` list of an existing record.

        Returns *True* if the record was found & updated, *False* otherwise.
        """
        rec = self.get(element_type, index, param)
        if rec is None:
            return False
        rec.values = values
        rec.raw_line = ""  # mark as dirty – will be re-serialised
        return True

    def num_instances(self, element_type: str) -> int:
        """Return the NUM value for *element_type* (from the index-0 record)."""
        rec = self.get(element_type, 0, "NUM")
        if rec and rec.values:
            try:
                return int(rec.values[0])
            except (ValueError, TypeError):
                pass
        return 0

    def version(self) -> str:
        """Return the KORF file version string (e.g. ``'KORF_2.0'``)."""
        for rec in self._records:
            if rec.element_type is None and rec.raw_line.strip().startswith('"KORF'):
                return rec.raw_line.strip().strip('"')
        return "KORF_2.0"

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return f"KdfParser(path={self.path!r}, records={len(self._records)})"
