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
        try:
            return float(self._scalar(Junction.PRES, 1, 0.0))
        except (TypeError, ValueError):
            return 0.0
