r"""Compressor element (``\\COMP``)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykorf.core.elements.base import BaseElement

if TYPE_CHECKING:
    from pykorf.core.model import Model


class Compressor(BaseElement):
    """Represents a KORF compressor.

    Very similar interface to :class:`Pump` but for gas service.
    """

    ETYPE = "COMP"
    ENAME = "Compressor"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/comp.py)
    # ------------------------------------------------------------------
    XY = "XY"  # [icon_x, icon_y, conn_x, conn_y] - 2 coordinate pairs (icon anchor + connection point)
    ELEV = "ELEV"  # [elevation, unit]
    CON = "CON"  # [suction_pipe_idx, discharge_pipe_idx]
    DP = "DP"  # [dp_str, dp_num, unit]
    PIN = "PIN"  # [pres_in_spec, pres_in_calc, unit]
    POUT = "POUT"  # [pres_out_spec, pres_out_calc, unit]
    PRAT = "PRAT"  # [prat_str, prat_num, prat3]
    QACT = "QACT"  # [flow_str, vol_flow_calc, unit]
    TYPE = "TYPE"  # ["comp_type"]
    EFFC = "EFFC"  # [eff_str, eff_num]
    EFFS = "EFFS"  # [eff_str, eff_num]
    POW = "POW"  # [shaft_power, unit]
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

    def summary(self, export: bool = False, model: Model | None = None) -> dict:
        from pykorf.core.elements.pipe import Pipe

        inlet_idx = self.connection[0]
        density_in: float | None = None
        density_unit = "kg/m³"
        mass_flow: float | None = None
        mass_flow_unit = "kg/h"

        if model and inlet_idx > 0 and inlet_idx in model.pipes:
            inlet_pipe = model.pipes[inlet_idx]
            try:
                density_in = float(inlet_pipe._scalar(Pipe.TPROP, 0))
                density_unit = str(inlet_pipe._scalar(Pipe.TPROP, 4))
            except (TypeError, ValueError, IndexError):
                pass
            try:
                mass_flow = float(inlet_pipe._scalar(Pipe.TFLOW, 1))
                mass_flow_unit = str(inlet_pipe._scalar(Pipe.TFLOW, 2))
            except (TypeError, ValueError, IndexError):
                pass

        if export:
            flow_val, flow_unit = self.get_value_and_unit(
                Compressor.QACT, val_index=1, unit_index=-1
            )
            dp_val, dp_unit = self.get_value_and_unit(Compressor.DP, val_index=1, unit_index=-1)
            suc_val, suc_unit = self.get_value_and_unit(Compressor.PIN, val_index=1, unit_index=-1)
            dis_val, dis_unit = self.get_value_and_unit(Compressor.POUT, val_index=1, unit_index=-1)
            head_val, head_unit = self.get_value_and_unit(
                Compressor.HQACT, val_index=0, unit_index=1
            )
            pow_val, pow_unit = self.get_value_and_unit(Compressor.POW, val_index=0, unit_index=-1)

            elev: float | None = None
            try:
                elev = float(self._scalar(Compressor.ELEV, 0))
            except (TypeError, ValueError):
                pass

            eff = self.efficiency
            eff_display = round(eff * 100, 1) if eff is not None else None

            hydraulic_power: float | None = None
            try:
                p_kW = self.power_kW
                if p_kW and eff:
                    hydraulic_power = p_kW * eff
            except (TypeError, ValueError):
                pass

            display_name = f"{self.name} , {self.description}" if self.description else self.name
            return {
                "Compressor Name": display_name,
                **self.section_marker("Fluid Properties"),
                self.format_export_header("Density", density_unit): density_in,
                **self.section_marker("Operating Conditions"),
                self.format_export_header("Compressor Datum Elevation", "m"): elev,
                self.format_export_header("Mass Flow", mass_flow_unit): mass_flow,
                self.format_export_header("Volumetric Flow", flow_unit): flow_val,
                self.format_export_header("Discharge Pressure", dis_unit): dis_val,
                self.format_export_header("Suction Pressure", suc_unit): suc_val,
                self.format_export_header("Differential Pressure", dp_unit): dp_val,
                self.format_export_header("Shaft Power", pow_unit): pow_val,
                self.format_export_header("Efficiency", "%"): eff_display,
                self.format_export_header("Hydraulic Power", pow_unit): hydraulic_power,
            }

        return {
            "name": self.name,
            "type": self.comp_type,
            "head_m": self.head_m,
            "power_kW": self.power_kW,
            "efficiency": self.efficiency,
        }
