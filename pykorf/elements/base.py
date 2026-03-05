"""
BaseElement – abstract foundation for all KORF element objects.

Every element holds a live reference to the :class:`KdfParser` so that
get/set operations immediately affect the underlying record list that will
be serialised on save.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from pykorf.exceptions import ErrorContext, ParameterError

if TYPE_CHECKING:
    from pykorf.parser import KdfParser, KdfRecord


# ---------------------------------------------------------------------------
# Parameter schema – expected value counts derived from New.kdf (index-0)
# ---------------------------------------------------------------------------

_ETYPE_RE = re.compile(r"^\\([A-Z]+)$", re.IGNORECASE)


@lru_cache(maxsize=1)
def _load_param_schema() -> dict[tuple[str, str], tuple[int, list]]:
    """Parse ``New.kdf`` (index-0 records) and return expected value counts.

    Returns a dict mapping ``(ETYPE, PARAM)`` to a tuple of:
    - count: number of values that parameter carries in the default template
    - template_values: the actual default values from the template

    This is loaded once and cached for the lifetime of the process.
    """
    from pykorf.utils import parse_line

    schema: dict[tuple[str, str], tuple[int, list]] = {}
    template = Path(__file__).resolve().parent.parent / "library" / "New.kdf"
    if not template.exists():
        return schema

    with template.open(encoding="latin-1") as fh:
        for line in fh:
            tokens = parse_line(line.rstrip("\r\n"))
            if not tokens or len(tokens) < 3:
                continue
            m = _ETYPE_RE.match(tokens[0])
            if not m:
                continue
            etype = m.group(1).upper()
            try:
                idx = int(tokens[1])
            except (ValueError, IndexError):
                continue
            if idx != 0:
                continue
            param = tokens[2].strip('"').upper()
            values = tokens[3:]
            schema[(etype, param)] = (len(values), values)
    return schema


def validate_param_values(etype: str, param: str, values: list) -> None:
    """Validate that *values* has the expected length for *(etype, param)*.

    Compares against the default template structure in ``New.kdf``.
    Raises :class:`ParameterError` if the count does not match.

    This function is a no-op for ``(etype, param)`` pairs not found
    in the template (e.g. custom or version-specific parameters).

    Args:
        etype: Element type keyword (e.g. ``"PIPE"``).
        param: Parameter keyword (e.g. ``"TEMP"``).
        values: The value list being set.

    Raises:
        ParameterError: If ``len(values)`` does not match the expected count.
    """
    schema = _load_param_schema()
    key = (etype.upper(), param.upper())
    schema_entry = schema.get(key)
    if schema_entry is None:
        return  # unknown param – skip validation
    expected_count, template_values = schema_entry
    actual = len(values)
    if actual != expected_count:
        raise ParameterError(
            f"{etype}.{param} expects {expected_count} values, got {actual}. "
            f"Template values from New.kdf: {template_values}",
            context=ErrorContext(
                element_type=etype,
                parameter=param,
                additional_data={
                    "expected_count": expected_count,
                    "actual": actual,
                    "template_values": template_values,
                },
            ),
            suggestion=f"Provide exactly {expected_count} values for {param}. "
            f"Example: {template_values}",
        )


class BaseElement:
    """
    Base class wrapping a single KORF element instance.

    Subclasses carry their own parameter string constants as class-level
    attributes (e.g. ``Pipe.TFLOW == "TFLOW"``).  Common parameters that
    appear on most element types are defined here on the base class.

    Args:
        parser: The :class:`KdfParser` that owns this file's records.
        etype: KDF element-type keyword string (e.g. ``"PIPE"``).
        index: Instance index (>= 1 for real instances; 0 = default template).
    """

    #: KDF element-type keyword (override in subclasses)
    ETYPE: str = ""

    #: Human-readable element name (override in subclasses)
    ENAME: str = ""

    # ------------------------------------------------------------------
    # Common parameter constants (shared across most element types)
    # ------------------------------------------------------------------
    NAME = "NAME"
    NUM = "NUM"
    XY = "XY"
    NOTES = "NOTES"
    CON = "CON"
    NOZI = "NOZI"
    NOZO = "NOZO"
    NOZ = "NOZ"
    NOZL = "NOZL"
    X = "X"
    Y = "Y"
    ROT = "ROT"
    FLIP = "FLIP"
    LBL = "LBL"
    COLOR = "COLOR"

    def __init__(self, parser: "KdfParser", etype: str, index: int):
        self._parser = parser
        self._etype = etype.upper()
        self._index = index

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def index(self) -> int:
        return self._index

    @property
    def etype(self) -> str:
        return self._etype

    @property
    def name(self) -> str:
        """Element name tag (e.g. ``'L1'``, ``'P1'``)."""
        rec = self._get(self.NAME)
        return rec.values[0] if rec and rec.values else ""

    @property
    def description(self) -> str:
        """Optional description (second value of the NAME record)."""
        rec = self._get(self.NAME)
        return rec.values[1] if rec and len(rec.values) > 1 else ""

    @description.setter
    def description(self, value: str) -> None:
        rec = self._get(self.NAME)
        if rec:
            if len(rec.values) > 1:
                rec.values[1] = value
            else:
                rec.values.append(value)
            rec.raw_line = ""

    @property
    def notes(self) -> str:
        rec = self._get(self.NOTES)
        return rec.values[0] if rec and rec.values else ""

    @notes.setter
    def notes(self, value: str) -> None:
        self._set(self.NOTES, [value])

    # ------------------------------------------------------------------
    # Internal record access
    # ------------------------------------------------------------------

    def _get(self, param: str) -> Optional["KdfRecord"]:
        return self._parser.get(self._etype, self._index, param)

    def get_param(self, param: str) -> Optional["KdfRecord"]:
        """Return the record for a given parameter, or *None* if missing.

        Example:
            ```python
            from pykorf.elements import Feed
            rec = model.feeds[1].get_param(Feed.NAME)
            rec.update(["EXP DRUM", "FEED"])
            ```
        """
        return self._get(param)

    def _values(self, param: str) -> list:
        rec = self._get(param)
        return rec.values if rec else []

    def _set(self, param: str, values: list) -> None:
        """Update an existing record's values list in-place.

        Validates the value count against the default template before writing.
        """
        validate_param_values(self._etype, param, values)
        self._parser.set_value(self._etype, self._index, param, values)

    def set_param(self, param: str, values: list) -> bool:
        """Set values for a given parameter.

        Validates the value count against the default template (``New.kdf``)
        before writing.  Raises :class:`ParameterError` if the count does
        not match.

        Returns:
            ``True`` if parameter exists and was updated, otherwise ``False``.

        Raises:
            ParameterError: If the number of values does not match the
                expected structure from the KDF template.
        """
        validate_param_values(self._etype, param, values)
        return self._parser.set_value(self._etype, self._index, param, values)

    def _scalar(self, param: str, pos: int = 0, default: Any = None) -> Any:
        """Return a single value from a record's value list."""
        v = self._values(param)
        return v[pos] if len(v) > pos else default

    def _safe_float(self, param: str, pos: int = 0, default: float = 0.0) -> float:
        """Return a float from a record value, returning *default* on failure."""
        try:
            return float(self._scalar(param, pos, default))
        except (TypeError, ValueError):
            return default

    def _safe_int(self, param: str, pos: int = 0, default: int = 0) -> int:
        """Return an int from a record value, returning *default* on failure."""
        try:
            return int(self._scalar(param, pos, default))
        except (TypeError, ValueError):
            return default

    # ------------------------------------------------------------------
    # Raw record list
    # ------------------------------------------------------------------

    def records(self) -> list["KdfRecord"]:
        """All KDF records belonging to this element instance."""
        return self._parser.get_all(self._etype, self._index)

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(index={self._index}, name={self.name!r})"
