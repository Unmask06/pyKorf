"""Check valve element (``\\CHECK``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class CheckValve(BaseElement):
    """Represents a KORF check valve."""

    ETYPE = "CHECK"
    ENAME = "Check Valve"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/check.py)
    # ------------------------------------------------------------------
    ELEV = "ELEV"
    DP = "DP"
    PIN = "PIN"
    POUT = "POUT"
    LD = "LD"

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
        return self._safe_float(CheckValve.DP, 1, 0.0)

    @property
    def loss_diameter(self) -> float:
        """L/D equivalent loss."""
        return self._safe_float(CheckValve.LD, 0, 100.0)

    @loss_diameter.setter
    def loss_diameter(self, value: float) -> None:
        self._set(CheckValve.LD, [value])

    @property
    def connection(self) -> tuple[int, int]:
        vals = self._values(self.CON)
        try:
            return (int(vals[0]), int(vals[1]))
        except (IndexError, TypeError, ValueError):
            return (0, 0)
