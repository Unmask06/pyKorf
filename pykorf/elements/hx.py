r"""Heat exchanger element (``\\HX``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class HeatExchanger(BaseElement):
    """Represents a KORF heat exchanger (Shell-and-Tube or other).

    Example::

        hx = model.exchangers[1]
        print(hx.dp_kPag)  # pressure drop across HX
        hx.set_dp(60)
    """

    ETYPE = "HX"
    ENAME = "Heat Exchanger"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/hx.py)
    # ------------------------------------------------------------------
    TYPE = "TYPE"  # ["hx_type"]
    SIDE = "SIDE"  # ["modeled_side"]
    DP = "DP"  # [dp_str, dp_num, unit]
    PIN = "PIN"  # [pres_in_str, pres_in_num, unit]
    POUT = "POUT"  # [pres_out_str, pres_out_num, unit]
    PRAT = "PRAT"  # [prat_str, unit, prat3, unit, prat5, unit, prat7, unit]
    K = "K"  # [k_factor_str]
    DPELEV = "DPELEV"  # [elevation_dp, unit]
    Q = "Q"  # [heat_duty_str, heat_duty_num, unit]

    ALL = (
        "NUM",
        "NAME",
        "XY",
        "ROT",
        "FLIP",
        "LBL",
        "COLOR",
        TYPE,
        SIDE,
        "NOZI",
        "NOZO",
        DP,
        PIN,
        POUT,
        PRAT,
        K,
        DPELEV,
        Q,
        "NOTES",
    )

    def __init__(self, parser, index: int):
        super().__init__(parser, "HX", index)

    @property
    def hx_type(self) -> str:
        """Exchanger type, e.g. ``'S-T'`` (shell-and-tube)."""
        return str(self._scalar(HeatExchanger.TYPE, 0))

    @property
    def side(self) -> str:
        """Hydraulic side modelled (``'Tube'`` or ``'Shell'``)."""
        return str(self._scalar(HeatExchanger.SIDE, 0))

    @property
    def dp_string(self) -> str:
        return str(self._scalar(HeatExchanger.DP, 0))

    @property
    def dp_kPag(self) -> float:
        try:
            return float(self._scalar(HeatExchanger.DP, 1))
        except (TypeError, ValueError):
            return 0.0

    def set_dp(self, value: str | float) -> None:
        rec = self.get_param(HeatExchanger.DP)
        if rec:
            self.set_param(HeatExchanger.DP, [str(value), *rec.values[1:]])

    @property
    def inlet_pressure_kPag(self) -> float:
        try:
            return float(self._scalar(HeatExchanger.PIN, 1))
        except (TypeError, ValueError):
            return 0.0

    @property
    def outlet_pressure_kPag(self) -> float:
        try:
            return float(self._scalar(HeatExchanger.POUT, 1))
        except (TypeError, ValueError):
            return 0.0

    @property
    def heat_duty_kJh(self) -> float:
        try:
            return float(self._scalar(HeatExchanger.Q, 1))
        except (TypeError, ValueError):
            return 0.0

    @property
    def nozzle_in(self) -> int:
        try:
            return int(self._scalar(self.NOZI, 0))
        except (TypeError, ValueError):
            return 0

    @property
    def nozzle_out(self) -> int:
        try:
            return int(self._scalar(self.NOZO, 0))
        except (TypeError, ValueError):
            return 0

    def summary(self, export: bool = False) -> dict:
        if export:
            dp_val, dp_unit = self.get_value_and_unit(HeatExchanger.DP, val_index=1, unit_index=-1)
            pin_val, pin_unit = self.get_value_and_unit(
                HeatExchanger.PIN, val_index=1, unit_index=-1
            )
            pout_val, pout_unit = self.get_value_and_unit(
                HeatExchanger.POUT, val_index=1, unit_index=-1
            )

            return {
                "Heat Exchanger Name": self.name,
                "Type": self.hx_type,
                "Side": self.side,
                self.format_export_header("Pressure Drop", dp_unit): dp_val,
                self.format_export_header("Inlet Pressure", pin_unit): pin_val,
                self.format_export_header("Outlet Pressure", pout_unit): pout_val,
            }

        return {
            "name": self.name,
            "type": self.hx_type,
            "side": self.side,
            "dp_kPag": self.dp_kPag,
            "inlet_pressure_kPag": self.inlet_pressure_kPag,
            "outlet_pressure_kPag": self.outlet_pressure_kPag,
        }
