"""Junction element (``\\JUNC``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class Junction(BaseElement):
    """Multi-connection junction node."""

    ETYPE = "JUNC"
    ENAME = "Junction"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/junc.py)
    # ------------------------------------------------------------------
    PRES = "PRES"

    ALL = (
        "NUM",
        "NAME",
        "XY",
        "ROT",
        "FLIP",
        "LBL",
        "COLOR",
        PRES,
        "NOZI",
        "NOZO",
    )

    def __init__(self, parser, index: int):
        super().__init__(parser, "JUNC", index)

    @property
    def pressure_kPag(self) -> float:
        return self._safe_float(Junction.PRES, 1, 0.0)
