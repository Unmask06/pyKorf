r"""Pipe element (``\\PIPE``)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykorf.elements.base import BaseElement
from pykorf.utils import join_cases, split_cases

if TYPE_CHECKING:
    from pykorf.fluid import Fluid


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
    BEND = "BEND"
    LBL = "LBL"
    COLOR = "COLOR"
    STRM = "STRM"
    LOCK = "LOCK"
    TEMP = "TEMP"
    PRES = "PRES"
    LF = "LF"
    H = "H"
    HAMB = "HAMB"
    S = "S"
    FT = "FT"
    Q = "Q"
    UI = "UI"
    TAMB = "TAMB"
    DAMB = "DAMB"
    TSUR = "TSUR"
    QFAC = "QFAC"
    QNTU = "QNTU"
    QAIR = "QAIR"
    QPIP = "QPIP"
    QINS = "QINS"
    REFLINE = "REFLINE"
    OUTIN = "OUTIN"
    LVFLOW = "LVFLOW"
    LIQDEN = "LIQDEN"
    LIQVISC = "LIQVISC"
    LIQSUR = "LIQSUR"
    LIQCON = "LIQCON"
    LIQCP = "LIQCP"
    LIQMW = "LIQMW"
    VAPDEN = "VAPDEN"
    VAPVISC = "VAPVISC"
    VAPMW = "VAPMW"
    VAPZ = "VAPZ"
    VAPK = "VAPK"
    VAPCON = "VAPCON"
    VAPCP = "VAPCP"
    TFLOW = "TFLOW"
    TPROP = "TPROP"
    TOTCON = "TOTCON"
    TOTCP = "TOTCP"
    TOTMW = "TOTMW"
    PSAT = "PSAT"
    OMEGA = "OMEGA"
    RS = "RS"
    YW = "YW"
    MAT = "MAT"
    DIA = "DIA"
    ID = "ID"
    IDH = "IDH"
    ODF = "ODF"
    SCH = "SCH"
    LEN = "LEN"
    EQLEN = "EQLEN"
    FITK = "FITK"
    FITLD = "FITLD"
    FITLR = "FITLR"
    FIT1 = "FIT1"
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
    SELEV = "SELEV"
    DPELEV = "DPELEV"
    DPFRIC = "DPFRIC"
    DPACCEL = "DPACCEL"
    ELEV = "ELEV"
    DP_DES_FAC = "FAC"
    ROUGHNESS = "EPS"
    F = "F"
    RE = "RE"
    SIZ = "SIZ"
    DPL = "DPL"
    VEL = "VEL"
    HUP = "HUP"
    REG = "REG"
    REGA = "REGA"
    MTP = "MTP"
    DUK = "DUK"
    LM = "LM"
    EQN = "EQN"
    FILES = "FILES"

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
        return str(self._scalar(Pipe.TFLOW, 0, ""))

    @property
    def flow_unit(self) -> str:
        return str(self._scalar(Pipe.TFLOW, 2, "t/h"))

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

        rec = self._get(Pipe.TFLOW)
        if rec is None:
            return
        # values layout: [input_string, calc_numeric, unit]
        new_vals = [flow_str, *rec.values[1:]]
        self._set(Pipe.TFLOW, new_vals)

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------

    @property
    def diameter_inch(self) -> str:
        """Nominal pipe diameter (inch string as stored in the KDF)."""
        return str(self._scalar(Pipe.DIA, 0, ""))

    @property
    def schedule(self) -> str:
        return str(self._scalar(Pipe.SCH, 0, ""))

    @property
    def length_m(self) -> float:
        try:
            return float(self._scalar(Pipe.LEN, 0, 0))
        except (TypeError, ValueError):
            return 0.0

    @length_m.setter
    def length_m(self, value: float) -> None:
        self._set(Pipe.LEN, [value, "m"])

    @property
    def material(self) -> str:
        return str(self._scalar(Pipe.MAT, 0, "Steel"))

    @property
    def roughness_m(self) -> float:
        """Pipe wall roughness in metres."""
        try:
            return float(self._scalar(Pipe.ROUGHNESS, 1, 0.0000457))
        except (TypeError, ValueError):
            return 0.0000457

    @property
    def id_m(self) -> float:
        """Internal diameter in metres (calculated / set)."""
        try:
            return float(self._scalar(Pipe.ID, 1, 0.0))
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
            return float(self._scalar(Pipe.DPL, 0, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def reynolds_number(self) -> float:
        try:
            return float(self._scalar(Pipe.RE, 0, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def flow_regime(self) -> list[str]:
        return self._values(Pipe.REG)

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
            self._set(param, values)

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
            return float(self._scalar(Pipe.EQLEN, 0, 0.0))
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

    def summary(self) -> dict:
        """Return a dict of key pipe properties (useful for display)."""
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
