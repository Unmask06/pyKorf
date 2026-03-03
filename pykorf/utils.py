"""Shared CSV / value utilities for pyKorf.

KDF format notes
----------------
* Each line is a comma-separated list of quoted / unquoted tokens.
* String tokens are wrapped in double-quotes.
* Numeric tokens are unquoted (and may use VB6-style scientific notation
  such as ``2.22736E-02``).
* Multi-case values are packed into a single quoted string with semicolons
  as the separator: ``"50;55;20"`` means case-1=50, case-2=55, case-3=20.
* A value of ``";C"`` indicates *calculated* – KORF filled it in during a run.
* Index 0 of every element type is the *default template*; actual instances
  start at index 1.
* ``"\\ELEMENT",0,"NUM",n`` stores the count of actual instances.
"""

from __future__ import annotations

import csv
import io

# ---------------------------------------------------------------------------
# CSV tokenisation
# ---------------------------------------------------------------------------


def _unescape_korf_chars(value: str) -> str:
    """Convert KORF HTML entity encoding back to normal characters.

    KORF uses HTML-style entities for special characters:
    - <CHR34> -> " (double quote)
    - <CHR60> -> < (less than)
    - <CHR62> -> > (greater than)
    """
    return value.replace("<CHR34>", '"').replace("<CHR60>", "<").replace("<CHR62>", ">")


def parse_line(line: str) -> list[str]:
    """Parse a single KDF CSV line into a list of string tokens.

    The KDF format uses standard CSV with double-quote strings, so the
    stdlib :mod:`csv` reader handles it correctly.

    Also converts KORF HTML entity encoding (<CHR34>, etc.) back to normal characters.
    """
    reader = csv.reader(io.StringIO(line.strip()))
    for row in reader:
        return [_unescape_korf_chars(token) for token in row]
    return []


def _escape_korf_chars(value: str) -> str:
    """Convert special characters to KORF HTML entity encoding.

    KORF uses HTML-style entities for special characters:
    - " -> <CHR34> (double quote)
    - < -> <CHR60> (less than)
    - > -> <CHR62> (greater than)

    Note: Must escape < and > first to avoid double-escaping entity codes.
    """
    # Escape in order: first < and >, then "
    # This prevents <CHR34> from becoming <CHR60>CHR34<CHR62>
    return value.replace("<", "<CHR60>").replace(">", "<CHR62>").replace('"', "<CHR34>")


def format_line(tokens: list) -> str:
    """Serialize a list of tokens back to a KDF CSV line.

    * Strings (detected as containing non-numeric chars or empty) are quoted.
    * Numbers are written without quotes.
    * Special characters are converted to KORF HTML entity encoding.
    """
    raw_tokens: list[str] = []
    for t in tokens:
        if isinstance(t, str) and _is_numeric_str(t):
            raw_tokens.append(t)  # write unquoted
        elif isinstance(t, (int, float)):
            raw_tokens.append(_fmt_number(t))
        else:
            # Convert special chars to KORF entity encoding
            escaped = _escape_korf_chars(str(t))
            raw_tokens.append(f'"{escaped}"')  # quoted string with KORF encoding
    return ",".join(raw_tokens)


def _is_numeric_str(s: str) -> bool:
    """Return True if *s* looks like a bare number (int, float, sci-notation)."""
    s = s.strip()
    if not s:
        return False
    try:
        float(s)
        return True
    except ValueError:
        return False


def _fmt_number(v: float | int) -> str:
    """Format a number as KORF would write it (no unnecessary trailing zeros)."""
    if isinstance(v, int):
        return str(v)
    # Use %g for compact representation; keep enough precision.
    formatted = f"{v:.15g}"
    return formatted


# ---------------------------------------------------------------------------
# Multi-case value helpers
# ---------------------------------------------------------------------------


def split_cases(value: str) -> list[str]:
    """Split a semicolon-delimited case string into individual case values.

    Example::

        >>> split_cases("50;55;20")
        ['50', '55', '20']
        >>> split_cases(";C")          # calculated – treat as single item
        [';C']
        >>> split_cases("100")
        ['100']
    """
    if not value or value == ";C":
        return [value]
    return value.split(";")


def join_cases(values: list[str | float | int]) -> str:
    """Join individual case values into a semicolon-delimited string.

    Example::

        >>> join_cases([50, 55, 20])
        '50;55;20'
        >>> join_cases(['50', '55', '20'])
        '50;55;20'
    """
    return ";".join(str(v) for v in values)


def is_calculated(value: str) -> bool:
    """Return True if *value* is a KORF-calculated marker (``";C"``)."""
    return str(value).strip() == ";C"


# ---------------------------------------------------------------------------
# Key helpers
# ---------------------------------------------------------------------------


def element_key(element_type: str, index: int, param: str) -> tuple[str, int, str]:
    """Canonical (etype, idx, param) key used in the raw record store."""
    return (element_type.upper(), int(index), param.upper())
