"""Miscellaneous equipment element (``\\MISC``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class MiscEquipment(BaseElement):
    """Generic pressure-drop equipment (filter, separator, etc.)."""

    ETYPE = "MISC"
    ENAME = "Misc Equipment"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/misc.py)
    # ------------------------------------------------------------------
    DP = "DP"
    PIN = "PIN"
    POUT = "POUT"
    PRAT = "PRAT"
    K = "K"
    LD = "LD"
    DPELEV = "DPELEV"
    VOLBAL = "VOLBAL"
    MASBAL = "MASBAL"

    ALL = (
        "NUM",
        "NAME",
        "XY",
        "ROT",
        "FLIP",
        "LBL",
        "COLOR",
        "NOZI",
        "NOZO",
        DP,
        PIN,
        POUT,
        PRAT,
        K,
        LD,
        DPELEV,
        VOLBAL,
        MASBAL,
        "NOTES",
    )

    def __init__(self, parser, index: int):
        super().__init__(parser, "MISC", index)

    @property
    def dp_string(self) -> str:
        return str(self._scalar(MiscEquipment.DP, 0, "0"))

    @property
    def dp_kPag(self) -> float:
        try:
            return float(self._scalar(MiscEquipment.DP, 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    def set_dp(self, value: str | float) -> None:
        rec = self._get(MiscEquipment.DP)
        if rec:
            self._set(MiscEquipment.DP, [str(value)] + rec.values[1:])
