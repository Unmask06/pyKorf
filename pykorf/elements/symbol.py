r"""Symbol element (``\\SYMBOL``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class Symbol(BaseElement):
    r"""Wraps ``\\SYMBOL`` records - annotation symbols on the flow-sheet.

    This is a lightweight stub carrying only the KDF parameter constants.
    """

    ETYPE = "SYMBOL"
    ENAME = "Symbol"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/symbol.py)
    # ------------------------------------------------------------------
    TYPE = "TYPE"
    TEXT = "TEXT"
    STYLL = "STYLL"
    STYLA = "STYLA"
    ANGL = "ANGL"
    FSIZ = "FSIZ"

    ALL = (
        "NUM",
        TYPE,
        "XY",
        TEXT,
        "COLOR",
        STYLL,
        STYLA,
        ANGL,
        FSIZ,
    )
