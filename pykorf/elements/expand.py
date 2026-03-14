r"""Expander / reducer element (``\\EXPAND``)."""

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
    TYPE = "TYPE"  # [expand_type_int]
    ELEV = "ELEV"  # [elevation, unit]
    DP = "DP"  # [dp_str, dp_num, unit]
    PIN = "PIN"  # [pres_in_str, pres_in_num, unit]
    POUT = "POUT"  # [pres_out_str, pres_out_num, unit]
    DPP = "DPP"  # [dpp_num, unit]
    CHOKE = "CHOKE"  # [choke_bool]
    K = "K"  # [k_factor]
    ANGLE = "ANGLE"  # [angle_deg]

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
        try:
            return int(self._scalar(Expander.TYPE, 0))
        except (TypeError, ValueError):
            return 1

    @property
    def dp_kPag(self) -> float:
        try:
            return float(self._scalar(Expander.DP, 1))
        except (TypeError, ValueError):
            return 0.0

    @property
    def k_factor(self) -> float:
        try:
            return float(self._scalar(Expander.K, 0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def angle_deg(self) -> float:
        try:
            return float(self._scalar(Expander.ANGLE, 0))
        except (TypeError, ValueError):
            return 180.0

    @property
    def connection(self) -> tuple[int, int]:
        vals = self._values(self.CON)
        try:
            return (int(vals[0]), int(vals[1]))
        except (IndexError, TypeError, ValueError):
            return (0, 0)
