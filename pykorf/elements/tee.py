r"""Tee piece element (``\\TEE``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class Tee(BaseElement):
    """Represents a 3-way tee piece."""

    ETYPE = "TEE"
    ENAME = "Tee"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/tee.py)
    # ------------------------------------------------------------------
    TYPE = "TYPE"
    ELEV = "ELEV"
    PRES = "PRES"
    DPP = "DPP"
    KCM = "KCM"
    KCB = "KCB"
    SPAC = "SPAC"
    C = "C"
    M = "M"
    B = "B"

    ALL = (
        "NUM",
        "NAME",
        "XY",
        "ROT",
        "FLIP",
        "LBL",
        "COLOR",
        TYPE,
        "CON",
        ELEV,
        PRES,
        DPP,
        KCM,
        KCB,
        SPAC,
        C,
        M,
        B,
        "NOTES",
    )

    def __init__(self, parser, index: int):
        super().__init__(parser, "TEE", index)

    @property
    def tee_type(self) -> int:
        try:
            return int(self._scalar(Tee.TYPE, 0))
        except (TypeError, ValueError):
            return 0

    @property
    def pressures_kPag(self) -> list[float]:
        vals = self._values(Tee.PRES)
        nums = vals[:-1] if vals and isinstance(vals[-1], str) else vals
        result = []
        for v in nums:
            try:
                result.append(float(v))
            except (TypeError, ValueError):
                pass
        return result
