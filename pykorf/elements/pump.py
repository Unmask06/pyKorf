r"""Pump element (``\\PUMP``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class Pump(BaseElement):
    """Represents a centrifugal / positive-displacement pump.

    Key parameters
    --------------
    * ``dp_string``        - specified differential pressure
    * ``efficiency``       - pump hydraulic efficiency (fraction)
    * ``power_kW``         - absorbed shaft power (calculated)
    * ``head_m``           - actual operating head (calculated)
    * ``curve_q / curve_h / curve_eff / curve_npsh`` - performance curves

    Example::

        pump = model.pumps[1]
        print(pump.power_kW)  # 24.16
        print(pump.head_m)  # 155.6
        pump.set_efficiency(0.72)  # override efficiency (bypasses curve)
    """

    ETYPE = "PUMP"
    ENAME = "Pump"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/pump.py)
    # ------------------------------------------------------------------
    ELEV = "ELEV"  # [elevation, unit]
    DP = "DP"  # [dp_str, dp_num, unit]
    PIN = "PIN"  # [pres_in_str, pres_in_num, unit]
    POUT = "POUT"  # [pres_out_str, pres_out_num, unit]
    TYPE = "TYPE"  # ["pump_type"]
    EFFP = "EFFP"  # [eff_str, eff_num]
    EFFS = "EFFS"  # [eff_str, eff_num]
    POW = "POW"  # [power, unit]
    HQACT = "HQACT"  # [head, unit, flow, unit]
    CURRPM = "CURRPM"  # [rpm_str, rpm_num, unit]
    CURDIA = "CURDIA"  # [dia_str, dia_num, unit]
    CURVSD = "CURVSD"  # [vsd_bool]
    CURC1 = "CURC1"  # [curve_const]
    CURNP = "CURNP"  # [num_points]
    CURQ = "CURQ"  # [q1, q2, ..., q10, unit]
    CURH = "CURH"  # [h1, h2, ..., h10, unit]
    CUREFF = "CUREFF"  # [eff1, eff2, ..., eff10, unit]
    CURNPSH = "CURNPSH"  # [npsh1, npsh2, ..., npsh10, unit]
    NPSHA13 = "NPSHA13"  # [npsha_str, npsha_num, unit]
    NPSHR13 = "NPSHR13"  # [npshr_str, npshr_num, unit]
    NPSHAF = "NPSHAF"  # [npshaf1, npshaf2, npshaf3, npshaf4, unit, npshaf6, unit]
    NPSHRE = "NPSHRE"  # [npshre1, npshre2, unit, npshre4]
    NPSHVV = "NPSHVV"  # [npshvv_bool]
    NPSHVT = "NPSHVT"  # ["npshvt_type"]
    PZPRES = "PZPRES"  # [pz_dp, pz_suc, pz_dis, unit]
    PZRAT = "PZRAT"  # ["dp Method", dPshutoff/dpCalc, dp margin]
    PZVES = "PZVES"  # [vessel_pres, unit, vessel_level, unit]

    ALL = (
        BaseElement.NUM,
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
        TYPE,
        EFFP,
        EFFS,
        POW,
        HQACT,
        CURRPM,
        CURDIA,
        CURVSD,
        CURC1,
        CURNP,
        CURQ,
        CURH,
        CUREFF,
        CURNPSH,
        NPSHA13,
        NPSHR13,
        NPSHAF,
        NPSHRE,
        NPSHVV,
        NPSHVT,
        PZPRES,
        PZRAT,
        PZVES,
        "NOTES",
    )

    def __init__(self, parser, index: int):
        super().__init__(parser, "PUMP", index)

    # ------------------------------------------------------------------
    # CON - Connections
    # ------------------------------------------------------------------

    @property
    def inlet_pipe(self) -> int:
        try:
            return int(self._scalar(self.CON, 0))
        except (TypeError, ValueError):
            return 0

    @property
    def outlet_pipe(self) -> int:
        try:
            return int(self._scalar(self.CON, 1))
        except (TypeError, ValueError):
            return 0

    # ------------------------------------------------------------------
    # ELEV - Elevation
    # ------------------------------------------------------------------

    @property
    def elevation_m(self) -> float:
        try:
            return float(self._scalar(Pump.ELEV, 0))
        except (TypeError, ValueError):
            return 0.0

    # ------------------------------------------------------------------
    # DP - Specified / Calculated ΔP
    # ------------------------------------------------------------------

    @property
    def dp_string(self) -> str:
        return str(self._scalar(Pump.DP, 0))

    @property
    def dp_kPag(self) -> float:
        """Calculated differential pressure [kPag]."""
        try:
            return float(self._scalar(Pump.DP, 1))
        except (TypeError, ValueError):
            return 0.0

    def set_dp(self, value: str | float) -> None:
        """Override the pump differential pressure.

        Pass an empty string ``""`` to let KORF calculate via the curve.
        """
        rec = self.get_param(Pump.DP)
        if rec:
            new_vals = [str(value), *rec.values[1:]]
            self.set_param(Pump.DP, new_vals)

    # ------------------------------------------------------------------
    # PIN / POUT - Pressures
    # ------------------------------------------------------------------

    @property
    def inlet_pressure_kPag(self) -> float:
        """Calculated suction pressure [kPag]."""
        try:
            return float(self._scalar(Pump.PIN, 1))
        except (TypeError, ValueError):
            return 0.0

    @property
    def outlet_pressure_kPag(self) -> float:
        """Calculated discharge pressure [kPag]."""
        try:
            return float(self._scalar(Pump.POUT, 1))
        except (TypeError, ValueError):
            return 0.0

    # ------------------------------------------------------------------
    # TYPE - Pump Type
    # ------------------------------------------------------------------

    @property
    def pump_type(self) -> str:
        return str(self._scalar(Pump.TYPE, 0))

    # ------------------------------------------------------------------
    # EFFP - Efficiency
    # ------------------------------------------------------------------

    @property
    def efficiency_string(self) -> str:
        return str(self._scalar(Pump.EFFP, 0))

    @property
    def efficiency(self) -> float:
        """Pump hydraulic efficiency (fraction, 0-1)."""
        try:
            v = self._scalar(Pump.EFFP, 1)
            return float(v)
        except (TypeError, ValueError):
            return 0.0

    def set_efficiency(self, value: float) -> None:
        """Override pump efficiency (friction).

        Parameters
        ----------
        value:
            Fraction, e.g. ``0.72`` for 72 %.
            Pass ``""`` to restore curve-based calculation.
        """
        rec = self.get_param(Pump.EFFP)
        if rec:
            self.set_param(Pump.EFFP, [str(value), *rec.values[1:]])

    # ------------------------------------------------------------------
    # POW - Power
    # ------------------------------------------------------------------

    @property
    def power_kW(self) -> float:
        """Calculated absorbed power [kW]."""
        try:
            return float(self._scalar(Pump.POW, 0))
        except (TypeError, ValueError):
            return 0.0

    # ------------------------------------------------------------------
    # HQACT - Head and Flow
    # ------------------------------------------------------------------

    @property
    def head_m(self) -> float:
        """Calculated operating head [m]."""
        try:
            return float(self._scalar(Pump.HQACT, 0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def flow_m3h(self) -> float:
        """Calculated operating flow [m³/h]."""
        try:
            return float(self._scalar(Pump.HQACT, 2))
        except (TypeError, ValueError):
            return 0.0

    # ------------------------------------------------------------------
    # Performance curves (CURRPM, CURDIA, CURVSD, CURC1, CURNP, CURQ, CURH, CUREFF, CURNPSH)
    # ------------------------------------------------------------------

    @property
    def curve_q(self) -> list[str]:
        """Flow points on the pump curve [m³/h]."""
        vals = self._values(Pump.CURQ)
        return vals[:-1] if vals else []  # last token is unit

    @property
    def curve_h(self) -> list[str]:
        """Head points on the pump curve [m]."""
        vals = self._values(Pump.CURH)
        return vals[:-1] if vals else []

    @property
    def curve_eff(self) -> list[str]:
        """Efficiency points on the pump curve [fraction]."""
        vals = self._values(Pump.CUREFF)
        return vals[:-1] if vals else []

    @property
    def curve_npsh(self) -> list[str]:
        """NPSH required points [m]."""
        vals = self._values(Pump.CURNPSH)
        return vals[:-1] if vals else []

    @property
    def has_curve(self) -> bool:
        """True if a performance curve has been defined."""
        return bool(self.curve_q and self.curve_q[0])

    def set_curve(
        self,
        q: list,
        h: list,
        eff: list,
        npsh: list | None = None,
        q_unit: str = "m3/h",
        h_unit: str = "m",
    ) -> None:
        """Set the pump performance curve.

        Parameters
        ----------
        q:        Flow points (list of floats or strings).
        h:        Head points (matching length to *q*).
        eff:      Efficiency points (fraction, matching length to *q*).
        npsh:     NPSH-required points (optional, matching length to *q*).
        q_unit:   Unit for flow (default ``'m3/h'``).
        h_unit:   Unit for head (default ``'m'``).
        """
        self.set_param(Pump.CURQ, [str(v) for v in q] + [q_unit])
        self.set_param(Pump.CURH, [str(v) for v in h] + [h_unit])
        self.set_param(Pump.CUREFF, [str(v) for v in eff] + ["fraction"])
        if npsh is not None:
            self.set_param(Pump.CURNPSH, [str(v) for v in npsh] + ["m"])
        self.set_param(Pump.CURNP, [len(q)])

    # ------------------------------------------------------------------
    # NPSHA13 / NPSHR13 - NPSH
    # ------------------------------------------------------------------

    @property
    def npsha_calc_m(self) -> float:
        """Calculated NPSH available [m]."""
        try:
            return float(self._scalar(Pump.NPSHA13, 1))
        except (TypeError, ValueError):
            return 0.0

    @property
    def npshr_calc_m(self) -> float:
        """Calculated NPSH required [m]."""
        try:
            return float(self._scalar(Pump.NPSHR13, 1))
        except (TypeError, ValueError):
            return 0.0

    @property
    def npsh_required_m(self) -> float:
        """Alias for npshr_calc_m for backward compatibility."""
        return self.npshr_calc_m

    # ------------------------------------------------------------------
    # PZPRES - Shut-off Pressures
    # ------------------------------------------------------------------

    @property
    def shutoff_dp_kPa(self) -> float:
        """Differential pressure at shut-off [kPa]."""
        try:
            return float(self._scalar(Pump.PZPRES, 0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def suction_max_pressure_kPag(self) -> float:
        """Maximum suction pressure [kPag]."""
        try:
            return float(self._scalar(Pump.PZPRES, 1))
        except (TypeError, ValueError):
            return 0.0

    @property
    def discharge_shutoff_pressure_kPag(self) -> float:
        """Discharge pressure at shut-off [kPag]."""
        try:
            return float(self._scalar(Pump.PZPRES, 2))
        except (TypeError, ValueError):
            return 0.0

    # ------------------------------------------------------------------
    # PZRAT - Margin
    # ------------------------------------------------------------------

    @property
    def shutoff_margin(self) -> float:
        """Shut-off margin (multiplier)."""
        try:
            return float(self._scalar(Pump.PZRAT, 1))
        except (TypeError, ValueError):
            return 1.25

    # ------------------------------------------------------------------
    # PZVES - Vessel Info
    # ------------------------------------------------------------------

    @property
    def suction_vessel_max_pressure_kPag(self) -> float:
        """Suction vessel maximum pressure [kPag]."""
        try:
            return float(self._scalar(Pump.PZVES, 0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def suction_vessel_max_level_m(self) -> float:
        """Suction vessel maximum level [m]."""
        try:
            return float(self._scalar(Pump.PZVES, 2))
        except (TypeError, ValueError):
            return 0.0

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def summary(self, export: bool = False) -> dict:
        if export:
            suc_val, suc_unit = self.get_value_and_unit(Pump.PIN, val_index=1, unit_index=-1)
            dis_val, dis_unit = self.get_value_and_unit(Pump.POUT, val_index=1, unit_index=-1)

            flow_val, flow_unit = self.get_value_and_unit(Pump.HQACT, val_index=2, unit_index=-1)
            head_val, head_unit = self.get_value_and_unit(Pump.HQACT, val_index=0, unit_index=1)
            dp_val, dp_unit = self.get_value_and_unit(Pump.DP, val_index=1, unit_index=-1)

            npsha_val, npsh_unit = self.get_value_and_unit(Pump.NPSHA13, val_index=1, unit_index=-1)
            npshr_val, _ = self.get_value_and_unit(Pump.NPSHR13, val_index=1, unit_index=-1)

            pow_val, pow_unit = self.get_value_and_unit(Pump.POW, val_index=0, unit_index=-1)

            pz_dp_val, pz_unit = self.get_value_and_unit(Pump.PZPRES, val_index=0, unit_index=-1)
            pz_suc_val, _ = self.get_value_and_unit(Pump.PZPRES, val_index=1, unit_index=-1)
            pz_dis_val, _ = self.get_value_and_unit(Pump.PZPRES, val_index=2, unit_index=-1)

            margin_val, _ = self.get_value_and_unit(Pump.PZRAT, val_index=1, unit_index=-1)

            ves_pres_val, ves_p_unit = self.get_value_and_unit(
                Pump.PZVES, val_index=0, unit_index=1
            )
            ves_lvl_val, ves_l_unit = self.get_value_and_unit(Pump.PZVES, val_index=2, unit_index=3)

            return {
                "Pump Name": self.name,
                self.format_export_header("Suction Pressure", suc_unit): suc_val,
                self.format_export_header("Discharge Pressure", dis_unit): dis_val,
                self.format_export_header("Shut-Off Margin", ""): margin_val,
                self.format_export_header("Suc Vessel Max Pressure", ves_p_unit): ves_pres_val,
                self.format_export_header("Suc Vessel Max Level", ves_l_unit): ves_lvl_val,
                self.format_export_header("Volumetric Flow", flow_unit): flow_val,
                self.format_export_header("Head", head_unit): head_val,
                self.format_export_header("Differential Pressure", dp_unit): dp_val,
                self.format_export_header("Hydraulic Power", pow_unit): pow_val,
                self.format_export_header("NPSH Available", npsh_unit): npsha_val,
                self.format_export_header("NPSH Required", npsh_unit): npshr_val,
                self.format_export_header("Shut-Off DP", pz_unit): pz_dp_val,
                self.format_export_header("Suction Max Pressure", pz_unit): pz_suc_val,
                self.format_export_header("Discharge Shut-Off Pressure", pz_unit): pz_dis_val,
            }

        return {
            "name": self.name,
            "type": self.pump_type,
            "head_m": self.head_m,
            "flow_m3h": self.flow_m3h,
            "power_kW": self.power_kW,
            "efficiency": self.efficiency,
            "npsh_required_m": self.npsh_required_m,
            "has_curve": self.has_curve,
        }
