"""Check valve element (``\\CHECK``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class CheckValve(BaseElement):
    """Represents a KORF check valve."""

    ETYPE = "CHECK"

    def __init__(self, parser, index: int):
        super().__init__(parser, "CHECK", index)

    @property
    def dp_kPag(self) -> float:
        try:
            return float(self._scalar("DP", 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def loss_diameter(self) -> float:
        """L/D equivalent loss."""
        try:
            return float(self._scalar("LD", 0, 100.0))
        except (TypeError, ValueError):
            return 100.0

    @loss_diameter.setter
    def loss_diameter(self, value: float) -> None:
        self._set("LD", [value])

    @property
    def connection(self) -> tuple[int, int]:
        vals = self._values("CON")
        try:
            return (int(vals[0]), int(vals[1]))
        except (IndexError, TypeError, ValueError):
            return (0, 0)
