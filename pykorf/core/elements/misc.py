r"""Miscellaneous equipment element (``\\MISC``)."""

from __future__ import annotations

from pykorf.core.elements.base import BaseElement


class MiscEquipment(BaseElement):
    """Generic pressure-drop equipment (filter, separator, etc.)."""

    ETYPE = "MISC"
    ENAME = "Misc Equipment"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/misc.py)
    # ------------------------------------------------------------------
    XY = "XY"  # [icon_x, icon_y, conn_x, conn_y] - 2 coordinate pairs (icon anchor + connection point)
    DP = "DP"  # [dp_str, dp_num, unit]
    PIN = "PIN"  # [pres_in_str, pres_in_num, unit]
    POUT = "POUT"  # [pres_out_str, pres_out_num, unit]
    PRAT = "PRAT"  # [prat_str, unit, prat3, unit, prat5, unit, prat7, unit]
    K = "K"  # [k_factor_str]
    LD = "LD"  # [ld_str]
    DPELEV = "DPELEV"  # [elevation_dp, unit]
    VOLBAL = "VOLBAL"  # [vol_balance_bool]
    MASBAL = "MASBAL"  # [mass_balance_bool]

    ALL = (
        "NUM",
        "NAME",
        "XY",
        "ROT",
        "FLIP",
        "LBL",
        "COLOR",
        "NOZI",
        "NOZO",
        DP,
        PIN,
        POUT,
        PRAT,
        K,
        LD,
        DPELEV,
        VOLBAL,
        MASBAL,
        "NOTES",
    )

    def __init__(self, parser, index: int):
        super().__init__(parser, "MISC", index)

    @property
    def dp_string(self) -> str:
        return str(self._scalar(MiscEquipment.DP, 0))

    @property
    def dp_kPag(self) -> float:
        try:
            return float(self._scalar(MiscEquipment.DP, 1))
        except (TypeError, ValueError):
            return 0.0

    def set_dp(self, value: str | float) -> None:
        rec = self.get_param(MiscEquipment.DP)
        if rec:
            self.set_param(MiscEquipment.DP, [str(value), *rec.values[1:]])

    def summary(self, export: bool = False) -> dict:
        if export:
            dp_val, dp_unit = self.get_value_and_unit(MiscEquipment.DP, val_index=1, unit_index=-1)
            display_name = f"{self.name} , {self.description}" if self.description else self.name
            return {
                "Equipment Name": display_name,
                self.format_export_header("Pressure Drop", dp_unit): dp_val,
            }

        return {
            "name": self.name,
            "dp_kPag": self.dp_kPag,
        }
