"""Heat exchanger element (``\\HX``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class HeatExchanger(BaseElement):
    """Represents a KORF heat exchanger (Shell-and-Tube or other).

    Example::

        hx = model.exchangers[1]
        print(hx.dp_kPag)  # pressure drop across HX
        hx.set_dp(60)
    """

    ETYPE = "HX"

    def __init__(self, parser, index: int):
        super().__init__(parser, "HX", index)

    @property
    def hx_type(self) -> str:
        """Exchanger type, e.g. ``'S-T'`` (shell-and-tube)."""
        return str(self._scalar("TYPE", 0, "S-T"))

    @property
    def side(self) -> str:
        """Hydraulic side modelled (``'Tube'`` or ``'Shell'``)."""
        return str(self._scalar("SIDE", 0, "Tube"))

    @property
    def dp_string(self) -> str:
        return str(self._scalar("DP", 0, "50"))

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
    def heat_duty_kJh(self) -> float:
        try:
            return float(self._scalar("Q", 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def nozzle_in(self) -> int:
        try:
            return int(self._scalar("NOZI", 0, 0))
        except (TypeError, ValueError):
            return 0

    @property
    def nozzle_out(self) -> int:
        try:
            return int(self._scalar("NOZO", 0, 0))
        except (TypeError, ValueError):
            return 0
