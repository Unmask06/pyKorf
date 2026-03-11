"""Flow orifice element (``\\FO``)."""

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
    TYPE = "TYPE"
    ELEV = "ELEV"
    DP = "DP"
    DPF = "DPF"
    PIN = "PIN"
    POUT = "POUT"
    PSAT = "PSAT"
    HOLES = "HOLES"
    THICK = "THICK"
    BORE = "BORE"
    BETA = "BETA"
    BETAO = "BETAO"
    CD = "CD"
    YIN = "YIN"
    CHOKE = "CHOKE"
    OMEGA = "OMEGA"
    RS = "RS"
    RC = "RC"
    NDS = "NDS"
    MDEN = "MDEN"

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
        return str(self._scalar(FlowOrifice.TYPE, 0, "Orifice"))

    @property
    def dp_string(self) -> str:
        return str(self._scalar(FlowOrifice.DP, 0, ""))

    @property
    def dp_kPag(self) -> float:
        try:
            return float(self._scalar(FlowOrifice.DP, 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    def set_dp(self, value: str | float | list) -> None:
        if isinstance(value, (list, tuple)):
            value = join_cases(value)
        rec = self._get(FlowOrifice.DP)
        if rec:
            self._set(FlowOrifice.DP, [str(value), *rec.values[1:]])

    @property
    def beta(self) -> float:
        """Beta ratio (bore/pipe ID)."""
        try:
            return float(self._scalar(FlowOrifice.BETA, 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def bore_m(self) -> float:
        try:
            return float(self._scalar(FlowOrifice.BORE, 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def discharge_coeff(self) -> float:
        try:
            return float(self._scalar(FlowOrifice.CD, 0, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def num_holes(self) -> int:
        try:
            return int(self._scalar(FlowOrifice.HOLES, 0, 1))
        except (TypeError, ValueError):
            return 1

    @property
    def connection(self) -> tuple[int, int]:
        vals = self._values(self.CON)
        try:
            return (int(vals[0]), int(vals[1]))
        except (IndexError, TypeError, ValueError):
            return (0, 0)
