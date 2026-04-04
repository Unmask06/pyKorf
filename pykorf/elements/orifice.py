r"""Flow orifice element (``\\FO``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement
from pykorf.utils import join_cases


class FlowOrifice(BaseElement):
    """Represents a KORF flow orifice / restriction.

    Example::

        orifice = model.orifices[1]
        print(orifice.beta)  # 0.65
        orifice.set_dp("10;12;8")
    """

    ETYPE = "FO"
    ENAME = "Flow Orifice"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/orifice.py)
    # ------------------------------------------------------------------
    XY = "XY"  # [icon_x, icon_y, conn_x, conn_y] - 2 coordinate pairs (icon anchor + connection point)
    TYPE = "TYPE"  # ["orifice_type"]
    ELEV = "ELEV"  # [elevation, unit]
    DP = "DP"  # [dp_str, dp_num, unit]
    DPF = "DPF"  # [dpf_str, dpf_num, unit]
    PIN = "PIN"  # [pres_in_str, pres_in_num, unit]
    POUT = "POUT"  # [pres_out_str, pres_out_num, unit]
    PSAT = "PSAT"  # [psat_str, psat_num, unit]
    HOLES = "HOLES"  # [num_holes]
    THICK = "THICK"  # [thickness, unit]
    BORE = "BORE"  # [bore_str, bore_num]
    BETA = "BETA"  # [beta_str, beta_num]
    BETAO = "BETAO"  # [betao]
    CD = "CD"  # [cd_str, cd_num]
    YIN = "YIN"  # [expansion_factor]
    CHOKE = "CHOKE"  # [choke_bool]
    OMEGA = "OMEGA"  # [omega_str, omega_num]
    RS = "RS"  # [rs_factor]
    RC = "RC"  # [rc_factor]
    NDS = "NDS"  # [nds_factor]
    MDEN = "MDEN"  # ["mden_str"]

    ALL = (
        "NUM",
        "NAME",
        "XY",
        "COLOR",
        TYPE,
        "ROT",
        "FLIP",
        "LBL",
        "CON",
        ELEV,
        DP,
        DPF,
        PIN,
        POUT,
        PSAT,
        HOLES,
        THICK,
        BORE,
        BETA,
        BETAO,
        CD,
        YIN,
        CHOKE,
        OMEGA,
        RS,
        RC,
        NDS,
        MDEN,
        "NOTES",
    )

    def __init__(self, parser, index: int):
        super().__init__(parser, "FO", index)

    @property
    def orifice_type(self) -> str:
        return str(self._scalar(FlowOrifice.TYPE, 0))

    @property
    def dp_string(self) -> str:
        return str(self._scalar(FlowOrifice.DP, 0))

    @property
    def dp_kPag(self) -> float:
        try:
            return float(self._scalar(FlowOrifice.DP, 1))
        except (TypeError, ValueError):
            return 0.0

    def set_dp(self, value: str | float | list) -> None:
        if isinstance(value, (list, tuple)):
            value = join_cases(value)
        rec = self.get_param(FlowOrifice.DP)
        if rec:
            self.set_param(FlowOrifice.DP, [str(value), *rec.values[1:]])

    @property
    def beta(self) -> float:
        """Beta ratio (bore/pipe ID)."""
        try:
            return float(self._scalar(FlowOrifice.BETA, 1))
        except (TypeError, ValueError):
            return 0.0

    @property
    def bore_m(self) -> float:
        try:
            return float(self._scalar(FlowOrifice.BORE, 1))
        except (TypeError, ValueError):
            return 0.0

    @property
    def discharge_coeff(self) -> float:
        try:
            return float(self._scalar(FlowOrifice.CD, 0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def num_holes(self) -> int:
        try:
            return int(self._scalar(FlowOrifice.HOLES, 0))
        except (TypeError, ValueError):
            return 1

    @property
    def connection(self) -> tuple[int, int]:
        vals = self._values(self.CON)
        try:
            return (int(vals[0]), int(vals[1]))
        except (IndexError, TypeError, ValueError):
            return (0, 0)
