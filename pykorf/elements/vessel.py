"""Vessel element (``\\VESSEL``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class Vessel(BaseElement):
    """Represents a KORF pressure vessel / separator."""

    ETYPE = "VESSEL"
    ENAME = "Vessel"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/vessel.py)
    # ------------------------------------------------------------------
    TYPE = "TYPE"
    PRES = "PRES"
    WSPEC = "WSPEC"
    VF = "VF"
    LLF = "LLF"
    HLF = "HLF"
    ELEV = "ELEV"
    LEVELL = "LEVELL"
    LEVELM = "LEVELM"
    LEVELH = "LEVELH"
    NOZN = "NOZN"
    NOZLI = "NOZLI"
    NOZLO = "NOZLO"

    ALL = (
        "NUM",
        "NAME",
        "XY",
        "ROT",
        "FLIP",
        "LBL",
        "COLOR",
        TYPE,
        PRES,
        WSPEC,
        VF,
        LLF,
        HLF,
        ELEV,
        LEVELL,
        LEVELM,
        LEVELH,
        NOZN,
        NOZLI,
        NOZLO,
        "NOTES",
    )

    def __init__(self, parser, index: int):
        super().__init__(parser, "VESSEL", index)

    @property
    def vessel_type(self) -> str:
        return str(self._scalar(Vessel.TYPE, 0, "Vertical"))

    @property
    def pressure_string(self) -> str:
        return str(self._scalar(Vessel.PRES, 0, ""))

    @property
    def pressure_kPag(self) -> float:
        try:
            return float(self._scalar(Vessel.PRES, 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    def set_pressure(self, value: str | float) -> None:
        rec = self._get(Vessel.PRES)
        if rec:
            self._set(Vessel.PRES, [str(value), *rec.values[1:]])

    @property
    def elevation_m(self) -> float:
        try:
            return float(self._scalar(Vessel.ELEV, 0, 0.0))
        except (TypeError, ValueError):
            return 0.0
