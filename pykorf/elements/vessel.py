"""Vessel element (``\\VESSEL``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class Vessel(BaseElement):
    """Represents a KORF pressure vessel / separator."""

    ETYPE = "VESSEL"

    def __init__(self, parser, index: int):
        super().__init__(parser, "VESSEL", index)

    @property
    def vessel_type(self) -> str:
        return str(self._scalar("TYPE", 0, "Vertical"))

    @property
    def pressure_string(self) -> str:
        return str(self._scalar("PRES", 0, ""))

    @property
    def pressure_kPag(self) -> float:
        try:
            return float(self._scalar("PRES", 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    def set_pressure(self, value: str | float) -> None:
        rec = self._get("PRES")
        if rec:
            self._set("PRES", [str(value)] + rec.values[1:])

    @property
    def elevation_m(self) -> float:
        try:
            return float(self._scalar("ELEV", 0, 0.0))
        except (TypeError, ValueError):
            return 0.0
