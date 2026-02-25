"""Control valve element (``\\VALVE``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement
from pykorf.utils import join_cases


class Valve(BaseElement):
    """Represents a KORF control valve.

    Example::

        valve = model.valves[1]
        print(valve.dp_kPag)  # 565.3
        valve.set_dp("175;200;100")  # multi-case
        valve.set_opening("80;90;60")  # % open per case
    """

    ETYPE = "VALVE"

    def __init__(self, parser, index: int):
        super().__init__(parser, "VALVE", index)

    @property
    def valve_type(self) -> str:
        return str(self._scalar("TYPE", 0, "Linear"))

    @property
    def cv(self) -> float:
        try:
            return float(self._scalar("CV", 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def dp_string(self) -> str:
        return str(self._scalar("DP", 0, ""))

    @property
    def dp_kPag(self) -> float:
        try:
            return float(self._scalar("DP", 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    def set_dp(self, value: str | float | list) -> None:
        if isinstance(value, (list, tuple)):
            value = join_cases(value)
        rec = self._get("DP")
        if rec:
            self._set("DP", [str(value)] + rec.values[1:])

    @property
    def opening_string(self) -> str:
        return str(self._scalar("OPEN", 0, "100"))

    def set_opening(self, value: str | float | list) -> None:
        """Set valve opening (% open, per case)."""
        if isinstance(value, (list, tuple)):
            value = join_cases(value)
        rec = self._get("OPEN")
        if rec:
            self._set("OPEN", [str(value)] + rec.values[1:])

    @property
    def inlet_pressure_kPag(self) -> float:
        try:
            return float(self._scalar("PIN", 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def outlet_pressure_kPag(self) -> float:
        try:
            return float(self._scalar("POUT", 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def connection(self) -> tuple[int, int]:
        """(inlet_pipe_index, outlet_pipe_index)"""
        vals = self._values("CON")
        try:
            return (int(vals[0]), int(vals[1]))
        except (IndexError, TypeError, ValueError):
            return (0, 0)
