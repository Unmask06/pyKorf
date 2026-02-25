"""Miscellaneous equipment element (``\\MISC``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class MiscEquipment(BaseElement):
    """Generic pressure-drop equipment (filter, separator, etc.)."""

    ETYPE = "MISC"

    def __init__(self, parser, index: int):
        super().__init__(parser, "MISC", index)

    @property
    def dp_string(self) -> str:
        return str(self._scalar("DP", 0, "0"))

    @property
    def dp_kPag(self) -> float:
        try:
            return float(self._scalar("DP", 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    def set_dp(self, value: str | float) -> None:
        rec = self._get("DP")
        if rec:
            self._set("DP", [str(value)] + rec.values[1:])
