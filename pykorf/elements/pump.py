"""Pump element (``\\PUMP``)."""

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
    ELEV = "ELEV"
    DP = "DP"
    PIN = "PIN"
    POUT = "POUT"
    TYPE = "TYPE"
    EFFP = "EFFP"
    EFFS = "EFFS"
    POW = "POW"
    HQACT = "HQACT"
    CURRPM = "CURRPM"
    CURDIA = "CURDIA"
    CURVSD = "CURVSD"
    CURC1 = "CURC1"
    CURNP = "CURNP"
    CURQ = "CURQ"
    CURH = "CURH"
    CUREFF = "CUREFF"
    CURNPSH = "CURNPSH"
    NPSHA13 = "NPSHA13"
    NPSHR13 = "NPSHR13"
    NPSHAF = "NPSHAF"
    NPSHRE = "NPSHRE"
    NPSHVV = "NPSHVV"
    NPSHVT = "NPSHVT"
    PZPRES = "PZPRES"
    PZRAT = "PZRAT"
    PZVES = "PZVES"

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
    # Connections
    # ------------------------------------------------------------------

    @property
    def inlet_pipe(self) -> int:
        try:
            return int(self._scalar(self.CON, 0, 0))
        except (TypeError, ValueError):
            return 0

    @property
    def outlet_pipe(self) -> int:
        try:
            return int(self._scalar(self.CON, 1, 0))
        except (TypeError, ValueError):
            return 0

    @property
    def pump_type(self) -> str:
        return str(self._scalar(Pump.TYPE, 0, "Centrifugal"))

    # ------------------------------------------------------------------
    # Specified ΔP
    # ------------------------------------------------------------------

    @property
    def dp_string(self) -> str:
        return str(self._scalar(Pump.DP, 0, ""))

    @property
    def dp_kPag(self) -> float:
        """Calculated differential pressure [kPag]."""
        try:
            return float(self._scalar(Pump.DP, 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    def set_dp(self, value: str | float) -> None:
        """Override the pump differential pressure.

        Pass an empty string ``""`` to let KORF calculate via the curve.
        """
        rec = self._get(Pump.DP)
        if rec:
            new_vals = [str(value)] + rec.values[1:]
            self._set(Pump.DP, new_vals)

    # ------------------------------------------------------------------
    # Efficiency
    # ------------------------------------------------------------------

    @property
    def efficiency_string(self) -> str:
        return str(self._scalar(Pump.EFFP, 0, ""))

    @property
    def efficiency(self) -> float:
        """Pump hydraulic efficiency (fraction, 0-1)."""
        try:
            v = self._scalar(Pump.EFFP, 1, 0.0)
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
        rec = self._get(Pump.EFFP)
        if rec:
            self._set(Pump.EFFP, [str(value)] + rec.values[1:])

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    @property
    def power_kW(self) -> float:
        """Calculated absorbed power [kW]."""
        try:
            return float(self._scalar(Pump.POW, 0, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def head_m(self) -> float:
        """Calculated operating head [m]."""
        try:
            return float(self._scalar(Pump.HQACT, 0, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def flow_m3h(self) -> float:
        """Calculated operating flow [m³/h]."""
        try:
            return float(self._scalar(Pump.HQACT, 2, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def npsh_required_m(self) -> float:
        try:
            return float(self._scalar(Pump.NPSHR13, 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    # ------------------------------------------------------------------
    # Performance curves
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
        self._set(Pump.CURQ, [str(v) for v in q] + [q_unit])
        self._set(Pump.CURH, [str(v) for v in h] + [h_unit])
        self._set(Pump.CUREFF, [str(v) for v in eff] + ["fraction"])
        if npsh is not None:
            self._set(Pump.CURNPSH, [str(v) for v in npsh] + ["m"])
        self._set(Pump.CURNP, [len(q)])

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def summary(self) -> dict:
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
