"""Compressor element (``\\COMP``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class Compressor(BaseElement):
    """Represents a KORF compressor.

    Very similar interface to :class:`Pump` but for gas service.
    """

    ETYPE = "COMP"

    def __init__(self, parser, index: int):
        super().__init__(parser, "COMP", index)

    @property
    def comp_type(self) -> str:
        return str(self._scalar("TYPE", 0, "Centrifugal"))

    @property
    def efficiency(self) -> float:
        try:
            return float(self._scalar("EFFC", 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    def set_efficiency(self, value: float) -> None:
        rec = self._get("EFFC")
        if rec:
            self._set("EFFC", [str(value)] + rec.values[1:])

    @property
    def power_kW(self) -> float:
        try:
            return float(self._scalar("POW", 0, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def head_m(self) -> float:
        try:
            return float(self._scalar("HQACT", 0, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def dp_kPag(self) -> float:
        try:
            return float(self._scalar("DP", 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def connection(self) -> tuple[int, int]:
        vals = self._values("CON")
        try:
            return (int(vals[0]), int(vals[1]))
        except (IndexError, TypeError, ValueError):
            return (0, 0)
