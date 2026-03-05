"""Control valve element (``\\VALVE``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement
from pykorf.utils import join_cases


class Valve(BaseElement):
    """Represents a KORF control valve.

    Example::

        valve = model.valves[1]
        print(valve.dp_kPag)  # 565.3
        valve.set_dp("175;200;100")  # multi-case
        valve.set_opening("80;90;60")  # % open per case
    """

    ETYPE = "VALVE"
    ENAME = "Valve"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/valve.py)
    # ------------------------------------------------------------------
    ELEV = "ELEV"
    DP = "DP"
    PIN = "PIN"
    POUT = "POUT"
    DPP = "DPP"
    PSAT = "PSAT"
    PCRIT = "PCRIT"
    THICK = "THICK"
    K = "K"
    CV = "CV"
    DIA = "DIA"
    TYPE2 = "TYPE2"
    TYPE = "TYPE"
    OPEN = "OPEN"
    OPENCV = "OPENCV"
    XT = "XT"
    FL = "FL"
    YIN = "YIN"
    FP2 = "FP2"
    CHOKE = "CHOKE"
    OMEGA = "OMEGA"
    RS = "RS"
    XC = "XC"
    NDS = "NDS"
    MDEN = "MDEN"

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
        DPP,
        PSAT,
        PCRIT,
        THICK,
        K,
        CV,
        DIA,
        TYPE2,
        TYPE,
        OPEN,
        OPENCV,
        XT,
        FL,
        YIN,
        FP2,
        CHOKE,
        OMEGA,
        RS,
        XC,
        NDS,
        MDEN,
        "NOTES",
    )

    def __init__(self, parser, index: int):
        super().__init__(parser, "VALVE", index)

    @property
    def valve_type(self) -> str:
        return str(self._scalar(Valve.TYPE, 0, "Linear"))

    @property
    def cv(self) -> float:
        return self._safe_float(Valve.CV, 1, 0.0)

    @property
    def dp_string(self) -> str:
        return str(self._scalar(Valve.DP, 0, ""))

    @property
    def dp_kPag(self) -> float:
        return self._safe_float(Valve.DP, 1, 0.0)

    def set_dp(self, value: str | float | list) -> None:
        if isinstance(value, (list, tuple)):
            value = join_cases(value)
        rec = self._get(Valve.DP)
        if rec:
            self._set(Valve.DP, [str(value)] + rec.values[1:])

    @property
    def opening_string(self) -> str:
        return str(self._scalar(Valve.OPEN, 0, "100"))

    def set_opening(self, value: str | float | list) -> None:
        """Set valve opening (% open, per case)."""
        if isinstance(value, (list, tuple)):
            value = join_cases(value)
        rec = self._get(Valve.OPEN)
        if rec:
            self._set(Valve.OPEN, [str(value)] + rec.values[1:])

    @property
    def inlet_pressure_kPag(self) -> float:
        return self._safe_float(Valve.PIN, 1, 0.0)

    @property
    def outlet_pressure_kPag(self) -> float:
        return self._safe_float(Valve.POUT, 1, 0.0)

    @property
    def connection(self) -> tuple[int, int]:
        """(inlet_pipe_index, outlet_pipe_index)"""
        vals = self._values(self.CON)
        try:
            return (int(vals[0]), int(vals[1]))
        except (IndexError, TypeError, ValueError):
            return (0, 0)
