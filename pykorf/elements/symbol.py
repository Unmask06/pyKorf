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
    XY = "XY"  # [icon_x, icon_y, pad_x, pad_y] - 2 coordinate pairs (icon anchor + padding)
    TYPE = "TYPE"  # ["symbol_type"]
    TEXT = "TEXT"  # ["text_content"]
    STYLL = "STYLL"  # [style_l]
    STYLA = "STYLA"  # [style_a]
    ANGL = "ANGL"  # [angle, ???]
    FSIZ = "FSIZ"  # [font_size]

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
