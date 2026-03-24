r"""Pipe element (``\\PIPE``)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykorf.elements.base import BaseElement
from pykorf.utils import join_cases, split_cases

if TYPE_CHECKING:
    from pykorf.fluid import Fluid
    from pykorf.model import Model


class Pipe(BaseElement):
    """Represents a single KORF pipe / process line instance.

    Carries all PIPE parameter string constants as class attributes
    so that callers can write ``Pipe.TFLOW`` instead of a bare string.

    Multi-case values (flow, pressure, temperature ...) are exposed as
    plain Python lists indexed 0 ... (n_cases-1).

    Example::

        pipe = model.pipes[1]
        pipe.set_flow([50, 55, 20])  # sets 3 cases
        print(pipe.diameter_inch)  # '6'
        print(pipe.schedule)  # '40'
        print(pipe.velocity)  # [0.298, 0.298, 0.298, 0.0]
    """

    ETYPE = "PIPE"
    ENAME = "Pipe"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/pipe.py)
    # ------------------------------------------------------------------
    BEND = "BEND"  # [angle_deg]
    LBL = "LBL"  # [on/off, x-offset, y-offset]
    COLOR = "COLOR"  # [color_int]
    STRM = "STRM"  # ["stream_name"]
    LOCK = "LOCK"  # [lock_bool]
    TEMP = "TEMP"  # [temp_c1, temp_c2, temp_c3, unit]
    PRES = "PRES"  # [pres_c1, pres_c2, pres_c3, unit]
    LF = "LF"  # [liq_frac_c1, liq_frac_c2, liq_frac_c3]
    H = "H"  # [enthalpy_c1, enthalpy_c2, unit]
    HAMB = "HAMB"  # [amb_enthalpy, unit]
    S = "S"  # [entropy_c1, entropy_c2, unit]
    FT = "FT"  # [fit_type, fit_count]
    Q = "Q"  # [heat_duty_str, heat_duty_num, unit]
    UI = "UI"  # [overall_u_str, overall_u_num, unit]
    TAMB = "TAMB"  # [amb_temp, unit]
    DAMB = "DAMB"  # [amb_density, unit]
    TSUR = "TSUR"  # [surface_temp, unit]
    QFAC = "QFAC"  # [heat_factor]
    QNTU = "QNTU"  # [ntu_multiplier]
    QAIR = "QAIR"  # ["air_type", vel, unit]
    QPIP = "QPIP"  # [emissivity, conductivity, unit]
    QINS = "QINS"  # [thickness, unit, conductivity, unit]
    REFLINE = "REFLINE"  # [reference_line_index]
    OUTIN = "OUTIN"  # [direction_flag]
    LVFLOW = "LVFLOW"  # [mass_flow, liq_mass_flow, unit]
    LIQDEN = "LIQDEN"  # [den_c1, den_c2, den_c3, unit]
    LIQVISC = "LIQVISC"  # [visc_c1, visc_c2, visc_c3, unit]
    LIQSUR = "LIQSUR"  # [surface_tension_c1, surface_tension_c2, surface_tension_c3, unit]
    LIQCON = "LIQCON"  # [cond_c1, cond_c2, cond_c3, unit]
    LIQCP = "LIQCP"  # [cp_c1, cp_c2, cp_c3, unit]
    LIQMW = "LIQMW"  # [mw_c1, mw_c2, mw_c3]
    VAPDEN = "VAPDEN"  # [den_c1, den_c2, den_c3, unit]
    VAPVISC = "VAPVISC"  # [visc_c1, visc_c2, visc_c3, unit]
    VAPMW = "VAPMW"  # [mw_c1, mw_c2, mw_c3]
    VAPZ = "VAPZ"  # [z_c1, z_c2, z_c3]
    VAPK = "VAPK"  # [k_c1, k_c2, k_c3]
    VAPCON = "VAPCON"  # [cond_c1, cond_c2, cond_c3, unit]
    VAPCP = "VAPCP"  # [cp_c1, cp_c2, cp_c3, unit]
    TFLOW = "TFLOW"  # [flow_str, flow_num, unit]
    TPROP = "TPROP"  # [prop1, prop2, prop3, prop4, den_unit, prop6, visc_unit]
    TOTCON = "TOTCON"  # [cond_str1, cond_str2, cond_num, unit]
    TOTCP = "TOTCP"  # [cp_str1, cp_str2, cp_num, unit]
    TOTMW = "TOTMW"  # [total_mw]
    PSAT = "PSAT"  # [psat_str, psat_num, unit]
    OMEGA = "OMEGA"  # [omega_str, omega_num]
    RS = "RS"  # [rs_factor]
    YW = "YW"  # [yw_factor]
    MAT = "MAT"  # ["material_name"]
    DIA = "DIA"  # [nom_dia, custom_dia_str, unit]
    ID = "ID"  # [id_str, id_num, unit]
    IDH = "IDH"  # [idh_str, idh_num, unit]
    ODF = "ODF"  # [od_str, od_num, unit]
    SCH = "SCH"  # ["schedule_name"]
    LEN = "LEN"  # [length, unit]
    EQLEN = "EQLEN"  # [equivalent_length, unit]
    FITK = "FITK"  # [total_k]
    FITLD = "FITLD"  # [total_ld]
    FITLR = "FITLR"  # [lr_factor]
    FIT1 = "FIT1"  # ["name", count, k, ld, ..., ...]
    FIT2 = "FIT2"
    FIT3 = "FIT3"
    FIT4 = "FIT4"
    FIT5 = "FIT5"
    FIT6 = "FIT6"
    FIT7 = "FIT7"
    FIT8 = "FIT8"
    FIT9 = "FIT9"
    FIT10 = "FIT10"
    FIT11 = "FIT11"
    SELEV = "SELEV"  # [static_head, unit]
    DPELEV = "DPELEV"  # [elevation_dp, unit]
    DPFRIC = "DPFRIC"  # [frictional_dp, unit]
    DPACCEL = "DPACCEL"  # [acceleration_dp, unit]
    ELEV = "ELEV"  # [elev_in, elev_out, unit]
    DP_DES_FAC = "FAC"  # [design_factor]
    ROUGHNESS = "EPS"  # [roughness_str, roughness_num, unit]
    F = "F"  # [fric_factor, ...]
    RE = "RE"  # [reynolds_number]
    SIZ = "SIZ"  # [sizing_str, dp_crit, unit, vel_crit, ..., ..., ..., unit]
    DPL = "DPL"  # [dp_per_100m, unit]
    VEL = "VEL"  # [vel_c1, vel_c2, vel_c3, vel_c4, unit]
    HUP = "HUP"  # [liquid_holdup]
    REG = "REG"  # [regime_c1, regime_c2, regime_c3]
    REGA = "REGA"  # [regime_a1, regime_a2, unit]
    MTP = "MTP"  # ["two_phase_model"]
    DUK = "DUK"  # [duk1, duk2, unit]
    LM = "LM"  # [lm1, lm2, lm3, lm4, lm5, lm6, lm7]
    EQN = "EQN"  # [eqn_type, ..., ..., ..., ...]
    FILES = "FILES"  # ["file1", "file2", ...]

    ALL = (
        "NUM",
        "NAME",
        BEND,
        "XY",
        LBL,
        COLOR,
        STRM,
        LOCK,
        TEMP,
        PRES,
        LF,
        H,
        HAMB,
        S,
        FT,
        Q,
        UI,
        TAMB,
        DAMB,
        TSUR,
        QFAC,
        QNTU,
        QAIR,
        QPIP,
        QINS,
        REFLINE,
        OUTIN,
        LVFLOW,
        LIQDEN,
        LIQVISC,
        LIQSUR,
        LIQCON,
        LIQCP,
        LIQMW,
        VAPDEN,
        VAPVISC,
        VAPMW,
        VAPZ,
        VAPK,
        VAPCON,
        VAPCP,
        TFLOW,
        TPROP,
        TOTCON,
        TOTCP,
        TOTMW,
        PSAT,
        OMEGA,
        RS,
        YW,
        MAT,
        DIA,
        ID,
        IDH,
        ODF,
        SCH,
        LEN,
        EQLEN,
        FITK,
        FITLD,
        FITLR,
        FIT1,
        FIT2,
        FIT3,
        FIT4,
        FIT5,
        FIT6,
        FIT7,
        FIT8,
        FIT9,
        FIT10,
        FIT11,
        SELEV,
        DPELEV,
        DPFRIC,
        DPACCEL,
        ELEV,
        DP_DES_FAC,
        ROUGHNESS,
        F,
        RE,
        SIZ,
        DPL,
        VEL,
        HUP,
        REG,
        REGA,
        MTP,
        DUK,
        LM,
        EQN,
        "NOTES",
        FILES,
    )

    def __init__(self, parser, index: int):
        super().__init__(parser, "PIPE", index)

    # ------------------------------------------------------------------
    # Flow
    # ------------------------------------------------------------------

    @property
    def flow_string(self) -> str:
        """Raw ``TFLOW`` input string as stored in the KDF (e.g. ``'50;55;20'``)."""
        return str(self._scalar(Pipe.TFLOW, 0))

    @property
    def flow_unit(self) -> str:
        return str(self._scalar(Pipe.TFLOW, 2))

    def get_flow(self) -> list[str]:
        """Return the input flow for each case."""
        return split_cases(self.flow_string)

    def set_flow(self, flow: list[str | float | int] | str) -> None:
        """Set the pipe total flow for one or more cases.

        Parameters
        ----------
        flow:
            Either a semicolon-delimited string ``"50;55;20"`` or a list
            ``[50, 55, 20]``.  A single scalar sets all cases to the
            same value.

        Example::

            pipe.set_flow("60;65;25")
            pipe.set_flow([60, 65, 25])
            pipe.set_flow(70)  # all cases → 70
        """
        if isinstance(flow, (list, tuple)):
            flow_str = join_cases(flow)
        elif isinstance(flow, (int, float)):
            flow_str = str(flow)
        else:
            flow_str = str(flow)

        rec = self.get_param(Pipe.TFLOW)
        if rec is None:
            return
        # values layout: [input_string, calc_numeric, unit]
        new_vals = [flow_str, *rec.values[1:]]
        self.set_param(Pipe.TFLOW, new_vals)

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------

    @property
    def diameter_inch(self) -> str:
        """Nominal pipe diameter (inch string as stored in the KDF)."""
        return str(self._scalar(Pipe.DIA, 0))

    @property
    def schedule(self) -> str:
        return str(self._scalar(Pipe.SCH, 0))

    @property
    def length_m(self) -> float:
        try:
            return float(self._scalar(Pipe.LEN, 0))
        except (TypeError, ValueError):
            return 0.0

    @length_m.setter
    def length_m(self, value: float) -> None:
        self.set_param(Pipe.LEN, [value, "m"])

    @property
    def material(self) -> str:
        return str(self._scalar(Pipe.MAT, 0))

    @property
    def roughness_m(self) -> float:
        """Pipe wall roughness in metres."""
        try:
            return float(self._scalar(Pipe.ROUGHNESS, 1))
        except (TypeError, ValueError):
            return 0.0000457

    @property
    def id_m(self) -> float:
        """Internal diameter in metres (calculated / set)."""
        try:
            return float(self._scalar(Pipe.ID, 1))
        except (TypeError, ValueError):
            return 0.0

    # ------------------------------------------------------------------
    # Fluid properties (liquid)
    # ------------------------------------------------------------------

    @property
    def liquid_density(self) -> list[float]:
        """Liquid density per case [kg/m³]."""
        vals = self._values(Pipe.LIQDEN)
        nums = vals[:-1] if vals and isinstance(vals[-1], str) else vals
        return [float(v) for v in nums if _is_num(v)]

    @property
    def liquid_viscosity(self) -> list[float]:
        """Liquid viscosity per case [cP]."""
        vals = self._values(Pipe.LIQVISC)
        nums = vals[:-1] if vals and isinstance(vals[-1], str) else vals
        return [float(v) for v in nums if _is_num(v)]

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    @property
    def pressure(self) -> list[float]:
        """Calculated pressures per case [kPag]."""
        vals = self._values(Pipe.PRES)
        nums = vals[:-1] if vals and isinstance(vals[-1], str) else vals
        return [float(v) for v in nums if _is_num(v)]

    @property
    def velocity(self) -> list[float]:
        """Calculated velocities [m/s]."""
        vals = self._values(Pipe.VEL)
        nums = vals[:-1] if vals and isinstance(vals[-1], str) else vals
        return [float(v) for v in nums if _is_num(v)]

    @property
    def pressure_drop_per_100m(self) -> float:
        """Calculated ΔP/100 m [kPa/100m]."""
        try:
            return float(self._scalar(Pipe.DPL, 0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def reynolds_number(self) -> float:
        try:
            return float(self._scalar(Pipe.RE, 0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def flow_regime(self) -> list[str]:
        return self._values(Pipe.REG)

    @property
    def sizing_dp_criteria(self) -> float | str:
        """Sizing criteria for Pressure Drop (DPL)."""
        val = self._scalar(Pipe.SIZ, 1)
        try:
            return float(val) if val is not None else "N/A"
        except (TypeError, ValueError):
            return val if val is not None else "N/A"

    @property
    def sizing_velocity_criteria(self) -> float | str:
        """Sizing criteria for Velocity."""
        val = self._scalar(Pipe.SIZ, 3)
        try:
            return float(val) if val is not None else "N/A"
        except (TypeError, ValueError):
            return val if val is not None else "N/A"

    def check_criteria(self) -> str:
        """Check if calculated results meet sizing criteria.

        Returns 'PASS' if DP/DL and Velocity are within criteria, otherwise 'FAIL'.
        """
        dp_crit = self.sizing_dp_criteria
        vel_crit = self.sizing_velocity_criteria
        dp_calc = self.pressure_drop_per_100m
        vel_calc = self.velocity[0] if self.velocity else 0.0

        # Logic for PASS/FAIL
        dp_pass = True
        if isinstance(dp_crit, (int, float)):
            dp_pass = dp_calc <= dp_crit

        vel_pass = True
        if isinstance(vel_crit, (int, float)):
            vel_pass = vel_calc <= vel_crit

        return "PASS" if dp_pass and vel_pass else "FAIL"

    # ------------------------------------------------------------------
    # Fluid properties
    # ------------------------------------------------------------------

    def set_fluid(self, fluid: Fluid) -> None:
        """Apply fluid properties to this pipe.

        This method updates fluid-related parameters in the KDF file
        directly, eliminating the need for intermediate text file imports.
        Only properties that were explicitly set on the Fluid instance
        will be written; unset properties are left unchanged.

        Args:
            fluid: A :class:`Fluid` instance containing fluid properties to update.

        Example::

            from pykorf.fluid import Fluid

            # Update only LVFLOW (partial update)
            fluid = Fluid(lvflow=13470)
            pipe.set_fluid(fluid)

            # Update multiple properties
            fluid = Fluid(temp=52.25, pres=398.7, liqden=570.24)
            pipe.set_fluid(fluid)

        Note:
            This updates the in-memory model. Call ``model.save()`` to
            persist changes to disk.
        """
        records = fluid.to_kdf_records()

        # Only update parameters that are present in the records
        for param, values in records.items():
            self.set_param(param, values)

    def get_fluid(self) -> Fluid:
        """Extract fluid properties from this pipe.

        Returns:
            A :class:`Fluid` instance populated with the pipe's
            current fluid properties.

        Example::

            fluid = pipe.get_fluid()
            print(f"Temperature: {fluid.temp[0]}°C (inlet)")
            print(f"Density: {fluid.liqden[0]}kg/m³")
        """
        from pykorf.fluid import Fluid

        # Helper to extract values - returns None if not present in model
        def get_values(param: str):
            vals = self._values(param)
            if not vals:
                return None
            # Remove unit if present (last element is string)
            if vals and isinstance(vals[-1], str):
                return [float(v) for v in vals[:-1] if _is_num(v)]
            return [float(v) for v in vals if _is_num(v)]

        return Fluid(
            temp=get_values(Pipe.TEMP),
            pres=get_values(Pipe.PRES),
            lf=get_values(Pipe.LF),
            liqden=get_values(Pipe.LIQDEN),
            liqvisc=get_values(Pipe.LIQVISC),
            liqsur=get_values(Pipe.LIQSUR),
            liqcon=get_values(Pipe.LIQCON),
            liqcp=get_values(Pipe.LIQCP),
            liqmw=get_values(Pipe.LIQMW),
            vapden=get_values(Pipe.VAPDEN),
            vapvisc=get_values(Pipe.VAPVISC),
            vapcon=get_values(Pipe.VAPCON),
            vapcp=get_values(Pipe.VAPCP),
            vapmw=get_values(Pipe.VAPMW),
            vapz=get_values(Pipe.VAPZ),
            vapk=get_values(Pipe.VAPK),
        )

    @property
    def elevation_m(self) -> list[float]:
        """[inlet_elevation, outlet_elevation] in metres."""
        vals = self._values(Pipe.ELEV)
        nums = vals[:-1] if vals and isinstance(vals[-1], str) else vals
        return [float(v) for v in nums if _is_num(v)]

    # ------------------------------------------------------------------
    # Fittings summary
    # ------------------------------------------------------------------

    @property
    def equivalent_length_m(self) -> float:
        try:
            return float(self._scalar(Pipe.EQLEN, 0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def fittings(self) -> list[dict]:
        """List of fittings defined for this pipe.

        Each fitting is a dict with: name, count, k, ld, etc.
        """
        results = []
        for i in range(1, 12):
            vals = self._values(getattr(Pipe, f"FIT{i}"))
            if vals and vals[0] and vals[0] != "None":
                results.append(
                    {
                        "name": str(vals[0]),
                        "count": vals[1],
                        "k": vals[2],
                        "ld": vals[3],
                    }
                )
        return results

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def summary(self, export: bool = False) -> dict:
        """Return a dict of key pipe properties (useful for display or export)."""
        if export:
            # Local import to avoid circular dependency with use_case module
            from pykorf.use_case.line_number import LineNumber

            dp_crit_val, dp_crit_unit = self.get_value_and_unit(Pipe.SIZ, val_index=1, unit_index=2)
            vel_crit_val, vel_crit_unit = self.get_value_and_unit(
                Pipe.SIZ, val_index=3, unit_index=-1
            )

            dp_calc_val, dp_calc_unit = self.get_value_and_unit(
                Pipe.DPL, val_index=0, unit_index=-1
            )
            vel_calc_val, vel_calc_unit = self.get_value_and_unit(
                Pipe.VEL, val_index=0, unit_index=-1
            )

            parsed_line = LineNumber.parse(self.notes)
            return {
                "Pipe Name": self.name,
                "Line Number": parsed_line.raw_line_number if parsed_line else "",
                self.format_export_header("DP / DL Criteria", dp_crit_unit): dp_crit_val,
                self.format_export_header("Velocity Criteria", vel_crit_unit): vel_crit_val,
                self.format_export_header("DP / DL", dp_calc_unit): dp_calc_val,
                self.format_export_header("Velocity", vel_calc_unit): vel_calc_val,
                "Criteria Check": self.check_criteria(),
            }
        return {
            "name": self.name,
            "diameter_inch": self.diameter_inch,
            "schedule": self.schedule,
            "length_m": self.length_m,
            "material": self.material,
            "flow": self.get_flow(),
            "velocity_m_s": self.velocity,
            "dP_kPa_100m": self.pressure_drop_per_100m,
            "Re": self.reynolds_number,
        }


def _is_num(v) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def propagate_pipe_rename(model: Model, old_name: str, new_name: str) -> list[str]:
    """Update EQN references across all pipes when a pipe is renamed.

    EQN records reference other pipes by name (e.g. ``"EQN",1,"L3",0,"",0,0,1,0``).
    When a pipe is renamed, any pipe whose EQN contains the old name must be
    updated to use the new name to keep the hydraulic equations consistent.

    Args:
        model: Loaded KDF model (in-memory).
        old_name: The pipe name before renaming.
        new_name: The pipe name after renaming.

    Returns:
        List of pipe names whose EQN record was updated.

    Example::

        from pykorf.elements.pipe import propagate_pipe_rename
        updated = propagate_pipe_rename(model, "L3", "VCL17-806")
        # ["L5", "L9"]  — pipes that referenced L3 in their EQN
    """
    updated: list[str] = []

    for idx, pipe in model.pipes.items():
        if idx == 0:
            continue

        eqn_rec = pipe.get_param(Pipe.EQN)
        if eqn_rec is None or not eqn_rec.values:
            continue

        new_values = [new_name if v == old_name else v for v in eqn_rec.values]
        if new_values != list(eqn_rec.values):
            pipe.set_param(Pipe.EQN, new_values)
            updated.append(pipe.name)

    return updated
