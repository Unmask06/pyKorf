r"""Vessel element (``\\VESSEL``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class Vessel(BaseElement):
    """Represents a KORF pressure vessel / separator."""

    ETYPE = "VESSEL"
    ENAME = "Vessel"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/vessel.py)
    # ------------------------------------------------------------------
    TYPE = "TYPE"  # ["vessel_type"]
    PRES = "PRES"  # [pres_str, pres_num, unit]
    WSPEC = "WSPEC"  # [wspec_int]
    VF = "VF"  # [vf_str, vf_num]
    LLF = "LLF"  # [llf_str, llf_num]
    HLF = "HLF"  # [hlf_str, hlf_num]
    ELEV = "ELEV"  # [elevation, unit]
    LEVELL = "LEVELL"  # [level_l1, level_l2, unit, level_l4, unit, level_l6]
    LEVELM = "LEVELM"  # [level_m1, level_m2, unit, level_m4, unit, level_m6]
    LEVELH = "LEVELH"  # [level_h1, level_h2, unit, level_h4, unit, level_h6]
    NOZN = "NOZN"  # [num_nozzles]
    NOZLI = "NOZLI"  # [id, x, y, unit, z, unit, ...]
    NOZLO = "NOZLO"  # [id, x, y, unit, z, unit, ...]

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
        return str(self._scalar(Vessel.TYPE, 0))

    @property
    def pressure_string(self) -> str:
        return str(self._scalar(Vessel.PRES, 0))

    @property
    def pressure_kPag(self) -> float:
        try:
            return float(self._scalar(Vessel.PRES, 1))
        except (TypeError, ValueError):
            return 0.0

    def set_pressure(self, value: str | float) -> None:
        rec = self.get_param(Vessel.PRES)
        if rec:
            self.set_param(Vessel.PRES, [str(value), *rec.values[1:]])

    @property
    def elevation_m(self) -> float:
        try:
            return float(self._scalar(Vessel.ELEV, 0))
        except (TypeError, ValueError):
            return 0.0
