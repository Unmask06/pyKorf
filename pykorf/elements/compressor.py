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
    ELEV = "ELEV"
    DP = "DP"
    PIN = "PIN"
    POUT = "POUT"
    PRAT = "PRAT"
    QACT = "QACT"
    TYPE = "TYPE"
    EFFC = "EFFC"
    EFFS = "EFFS"
    POW = "POW"
    FHAD = "FHAD"
    HQACT = "HQACT"
    CURRPM = "CURRPM"
    CURDIA = "CURDIA"
    CURNP = "CURNP"
    CURQ = "CURQ"
    CURH = "CURH"
    CUREFF = "CUREFF"

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
