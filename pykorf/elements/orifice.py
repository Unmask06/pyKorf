"""Flow orifice element (``\\FO``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement
from pykorf.utils import join_cases


class FlowOrifice(BaseElement):
    """Represents a KORF flow orifice / restriction.

    Example::

        orifice = model.orifices[1]
        print(orifice.beta)  # 0.65
        orifice.set_dp("10;12;8")
    """

    ETYPE = "FO"

    def __init__(self, parser, index: int):
        super().__init__(parser, "FO", index)

    @property
    def orifice_type(self) -> str:
        return str(self._scalar("TYPE", 0, "Orifice"))

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
    def beta(self) -> float:
        """Beta ratio (bore/pipe ID)."""
        try:
            return float(self._scalar("BETA", 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def bore_m(self) -> float:
        try:
            return float(self._scalar("BORE", 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def discharge_coeff(self) -> float:
        try:
            return float(self._scalar("C", 0, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def num_holes(self) -> int:
        try:
            return int(self._scalar("HOLES", 0, 1))
        except (TypeError, ValueError):
            return 1

    @property
    def connection(self) -> tuple[int, int]:
        vals = self._values("CON")
        try:
            return (int(vals[0]), int(vals[1]))
        except (IndexError, TypeError, ValueError):
            return (0, 0)
