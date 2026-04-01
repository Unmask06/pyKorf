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
    XY = "XY"  # [icon_x, icon_y, conn1_x, conn1_y, ..., conn3_x, conn3_y] - 6 coordinate pairs (icon + 3 connection points)
    TYPE = "TYPE"  # [tee_type_int]
    ELEV = "ELEV"  # [elevation, unit]
    PRES = "PRES"  # [p1, p2, p3, unit]
    DPP = "DPP"  # [dp1, dp2, dp3, unit]
    KCM = "KCM"  # [kcm_str, kcm_num]
    KCB = "KCB"  # [kcb_str, kcb_num]
    SPAC = "SPAC"  # [spacing]
    C = "C"  # [c1, c2, c3, unit]
    M = "M"  # [m1, m2, m3, unit]
    B = "B"  # [b1, b2, b3, unit]

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
