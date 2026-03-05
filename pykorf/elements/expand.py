"""Expander / reducer element (``\\EXPAND``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class Expander(BaseElement):
    """Represents a KORF expander or reducer fitting.

    Example::

        exp = model.expanders[1]
        print(exp.dp_kPag)
    """

    ETYPE = "EXPAND"
    ENAME = "Expander"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/expand.py)
    # ------------------------------------------------------------------
    TYPE = "TYPE"
    ELEV = "ELEV"
    DP = "DP"
    PIN = "PIN"
    POUT = "POUT"
    DPP = "DPP"
    CHOKE = "CHOKE"
    K = "K"
    ANGLE = "ANGLE"

    ALL = (
        "NUM",
        "NAME",
        "XY",
        "ROT",
        "FLIP",
        "LBL",
        "COLOR",
        TYPE,
        "CON",
        ELEV,
        DP,
        PIN,
        POUT,
        DPP,
        CHOKE,
        K,
        ANGLE,
    )

    def __init__(self, parser, index: int):
        super().__init__(parser, "EXPAND", index)

    @property
    def expand_type(self) -> int:
        """1 = expander (enlargement), 2 = reducer (contraction)."""
        return self._safe_int(Expander.TYPE, 0, 1)

    @property
    def dp_kPag(self) -> float:
        return self._safe_float(Expander.DP, 1, 0.0)

    @property
    def k_factor(self) -> float:
        return self._safe_float(Expander.K, 0, 0.0)

    @property
    def angle_deg(self) -> float:
        return self._safe_float(Expander.ANGLE, 0, 180.0)

    @property
    def connection(self) -> tuple[int, int]:
        vals = self._values(self.CON)
        try:
            return (int(vals[0]), int(vals[1]))
        except (IndexError, TypeError, ValueError):
            return (0, 0)
