r"""Compressor element (``\\COMP``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class Compressor(BaseElement):
    """Represents a KORF compressor.

    Very similar interface to :class:`Pump` but for gas service.
    """

    ETYPE = "COMP"
    ENAME = "Compressor"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/comp.py)
    # ------------------------------------------------------------------
    ELEV = "ELEV"  # [elevation, unit]
    DP = "DP"  # [dp_str, dp_num, unit]
    PIN = "PIN"  # [pres_in_str, pres_in_num, unit]
    POUT = "POUT"  # [pres_out_str, pres_out_num, unit]
    PRAT = "PRAT"  # [prat_str, prat_num, prat3]
    QACT = "QACT"  # [flow_str, flow_num, unit]
    TYPE = "TYPE"  # ["comp_type"]
    EFFC = "EFFC"  # [eff_str, eff_num]
    EFFS = "EFFS"  # [eff_str, eff_num]
    POW = "POW"  # [power, unit]
    FHAD = "FHAD"  # [fhad_str, fhad_num]
    HQACT = "HQACT"  # [head, unit, flow, unit]
    CURRPM = "CURRPM"  # [rpm_str, rpm_num, unit]
    CURDIA = "CURDIA"  # [dia_str, dia_num, unit]
    CURNP = "CURNP"  # [num_points]
    CURQ = "CURQ"  # [q1, q2, ..., q10, unit]
    CURH = "CURH"  # [h1, h2, ..., h10, unit]
    CUREFF = "CUREFF"  # [eff1, eff2, ..., eff10, unit]

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
        PRAT,
        QACT,
        TYPE,
        EFFC,
        EFFS,
        POW,
        FHAD,
        HQACT,
        CURRPM,
        CURDIA,
        CURNP,
        CURQ,
        CURH,
        CUREFF,
        "NOTES",
    )

    def __init__(self, parser, index: int):
        super().__init__(parser, "COMP", index)

    @property
    def comp_type(self) -> str:
        return str(self._scalar(Compressor.TYPE, 0))

    @property
    def efficiency(self) -> float:
        try:
            return float(self._scalar(Compressor.EFFC, 1))
        except (TypeError, ValueError):
            return 0.0

    def set_efficiency(self, value: float) -> None:
        rec = self.get_param(Compressor.EFFC)
        if rec:
            self.set_param(Compressor.EFFC, [str(value), *rec.values[1:]])

    @property
    def power_kW(self) -> float:
        try:
            return float(self._scalar(Compressor.POW, 0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def head_m(self) -> float:
        try:
            return float(self._scalar(Compressor.HQACT, 0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def dp_kPag(self) -> float:
        try:
            return float(self._scalar(Compressor.DP, 1))
        except (TypeError, ValueError):
            return 0.0

    @property
    def connection(self) -> tuple[int, int]:
        vals = self._values(self.CON)
        try:
            return (int(vals[0]), int(vals[1]))
        except (IndexError, TypeError, ValueError):
            return (0, 0)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def summary(self, export: bool = False) -> dict:
        if export:
            flow_val, flow_unit = self.get_value_and_unit(
                Compressor.QACT, val_index=0, unit_index=-1
            )
            dp_val, dp_unit = self.get_value_and_unit(Compressor.DP, val_index=1, unit_index=-1)

            return {
                "Compressor Name": self.name,
                self.format_export_header("Gas Volumetric Flow", flow_unit): flow_val,
                self.format_export_header("Differential Pressure", dp_unit): dp_val,
            }

        return {
            "name": self.name,
            "type": self.comp_type,
            "head_m": self.head_m,
            "power_kW": self.power_kW,
            "efficiency": self.efficiency,
        }
