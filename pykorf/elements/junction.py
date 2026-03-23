r"""Junction element (``\\JUNC``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class Junction(BaseElement):
    """Multi-connection junction node."""

    ETYPE = "JUNC"
    ENAME = "Junction"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/junc.py)
    # ------------------------------------------------------------------
    PRES = "PRES"  # [pres_str, pres_num, unit]
    LBL = "LBL"  # [on/off, x-offset, y-offset]

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
            return float(self._scalar(Junction.PRES, 1))
        except (TypeError, ValueError):
            return 0.0
