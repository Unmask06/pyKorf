r"""Control valve element (``\\VALVE``)."""

from __future__ import annotations

from pykorf.core.elements.base import BaseElement
from pykorf.core.utils import join_cases


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
    XY = "XY"  # [icon_x, icon_y, conn_x, conn_y] - 2 coordinate pairs (icon anchor + connection point)
    ELEV = "ELEV"  # [elevation, unit]
    DP = "DP"  # [dp_str, dp_num, unit]
    PIN = "PIN"  # [pres_in_str, pres_in_num, unit]
    POUT = "POUT"  # [pres_out_str, pres_out_num, unit]
    DPP = "DPP"  # [dpp1, dpp2, unit]
    PSAT = "PSAT"  # [psat_str, psat_num, unit]
    PCRIT = "PCRIT"  # [pcrit, unit]
    THICK = "THICK"  # [thickness, unit]
    K = "K"  # [k_factor_str]
    CV = "CV"  # [cv_str, cv_num]
    DIA = "DIA"  # ["dia_type"]
    TYPE2 = "TYPE2"  # ["valve_category"]
    TYPE = "TYPE"  # ["valve_type"]
    OPEN = "OPEN"  # [opening_str, opening_num]
    OPENCV = "OPENCV"  # [percent_cv]
    XT = "XT"  # [xt_factor]
    FL = "FL"  # [fl_factor]
    YIN = "YIN"  # [expansion_factor]
    FP2 = "FP2"  # [fp2_factor]
    CHOKE = "CHOKE"  # [choke_bool]
    OMEGA = "OMEGA"  # [omega_str, omega_num]
    RS = "RS"  # [rs_factor]
    XC = "XC"  # [xc_factor]
    NDS = "NDS"  # [nds_factor]
    MDEN = "MDEN"  # ["mden_str"]

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
        return str(self._scalar(Valve.TYPE, 0))

    @property
    def cv(self) -> float:
        try:
            return float(self._scalar(Valve.CV, 1))
        except (TypeError, ValueError):
            return 0.0

    @property
    def dp_string(self) -> str:
        return str(self._scalar(Valve.DP, 0))

    @property
    def dp_kPag(self) -> float:
        try:
            return float(self._scalar(Valve.DP, 1))
        except (TypeError, ValueError):
            return 0.0

    def set_dp(self, value: str | float | list) -> None:
        if isinstance(value, (list, tuple)):
            value = join_cases(value)
        rec = self.get_param(Valve.DP)
        if rec:
            self.set_param(Valve.DP, [str(value), *rec.values[1:]])

    @property
    def opening_string(self) -> str:
        return str(self._scalar(Valve.OPEN, 0))

    def set_opening(self, value: str | float | list) -> None:
        """Set valve opening (% open, per case)."""
        if isinstance(value, (list, tuple)):
            value = join_cases(value)
        rec = self.get_param(Valve.OPEN)
        if rec:
            self.set_param(Valve.OPEN, [str(value), *rec.values[1:]])

    @property
    def inlet_pressure_kPag(self) -> float:
        try:
            return float(self._scalar(Valve.PIN, 1))
        except (TypeError, ValueError):
            return 0.0

    @property
    def outlet_pressure_kPag(self) -> float:
        try:
            return float(self._scalar(Valve.POUT, 1))
        except (TypeError, ValueError):
            return 0.0

    @property
    def connection(self) -> tuple[int, int]:
        """(inlet_pipe_index, outlet_pipe_index)"""
        vals = self._values(self.CON)
        try:
            return (int(vals[0]), int(vals[1]))
        except (IndexError, TypeError, ValueError):
            return (0, 0)

    def summary(self, export: bool = False) -> dict:
        if export:
            dp_val, dp_unit = self.get_value_and_unit(Valve.DP, val_index=1, unit_index=-1)
            pin_val, pin_unit = self.get_value_and_unit(Valve.PIN, val_index=1, unit_index=-1)
            pout_val, pout_unit = self.get_value_and_unit(Valve.POUT, val_index=1, unit_index=-1)

            return {
                "Valve Name": self.name,
                "Type": self.valve_type,
                "CV": self.cv,
                self.format_export_header("Differential Pressure", dp_unit): dp_val,
                self.format_export_header("Inlet Pressure", pin_unit): pin_val,
                self.format_export_header("Outlet Pressure", pout_unit): pout_val,
                "Opening [%]": self.opening_string,
            }

        return {
            "name": self.name,
            "type": self.valve_type,
            "cv": self.cv,
            "dp_kPag": self.dp_kPag,
            "inlet_pressure_kPag": self.inlet_pressure_kPag,
            "outlet_pressure_kPag": self.outlet_pressure_kPag,
            "opening": self.opening_string,
        }
