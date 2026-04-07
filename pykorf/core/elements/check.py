r"""Check valve element (``\\CHECK``)."""

from __future__ import annotations

from pykorf.core.elements.base import BaseElement


class CheckValve(BaseElement):
    """Represents a KORF check valve."""

    ETYPE = "CHECK"
    ENAME = "Check Valve"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/check.py)
    # ------------------------------------------------------------------
    XY = "XY"  # [icon_x, icon_y, conn_x, conn_y] - 2 coordinate pairs (icon anchor + connection point)
    ELEV = "ELEV"  # [elevation, unit]
    DP = "DP"  # [dp_str, dp_num, unit]
    PIN = "PIN"  # [pres_in_str, pres_in_num, unit]
    POUT = "POUT"  # [pres_out_str, pres_out_num, unit]
    LD = "LD"  # [loss_diameter]

    ALL = (
        "NUM",
        "NAME",
        "XY",
        "ROT",
        "FLIP",
        "LBL",
        "COLOR",
        "CON",
        ELEV,
        DP,
        PIN,
        POUT,
        LD,
    )

    def __init__(self, parser, index: int):
        super().__init__(parser, "CHECK", index)

    @property
    def dp_kPag(self) -> float:
        try:
            return float(self._scalar(CheckValve.DP, 1))
        except (TypeError, ValueError):
            return 0.0

    @property
    def loss_diameter(self) -> float:
        """L/D equivalent loss."""
        try:
            return float(self._scalar(CheckValve.LD, 0))
        except (TypeError, ValueError):
            return 100.0

    @loss_diameter.setter
    def loss_diameter(self, value: float) -> None:
        self.set_param(CheckValve.LD, [value])

    @property
    def connection(self) -> tuple[int, int]:
        vals = self._values(self.CON)
        try:
            return (int(vals[0]), int(vals[1]))
        except (IndexError, TypeError, ValueError):
            return (0, 0)
