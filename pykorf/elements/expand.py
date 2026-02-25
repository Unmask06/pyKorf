"""Expander / reducer element (``\\EXPAND``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class Expander(BaseElement):
    """Represents a KORF expander or reducer fitting.

    Example::

        exp = model.expanders[1]
        print(exp.dp_kPag)
    """

    ETYPE = "EXPAND"

    def __init__(self, parser, index: int):
        super().__init__(parser, "EXPAND", index)

    @property
    def expand_type(self) -> int:
        """1 = expander (enlargement), 2 = reducer (contraction)."""
        try:
            return int(self._scalar("TYPE", 0, 1))
        except (TypeError, ValueError):
            return 1

    @property
    def dp_kPag(self) -> float:
        try:
            return float(self._scalar("DP", 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def k_factor(self) -> float:
        try:
            return float(self._scalar("K", 0, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def angle_deg(self) -> float:
        try:
            return float(self._scalar("ANGLE", 0, 180.0))
        except (TypeError, ValueError):
            return 180.0

    @property
    def connection(self) -> tuple[int, int]:
        vals = self._values("CON")
        try:
            return (int(vals[0]), int(vals[1]))
        except (IndexError, TypeError, ValueError):
            return (0, 0)
