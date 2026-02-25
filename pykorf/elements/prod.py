"""Product (sink / boundary condition) element (``\\PROD``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement
from pykorf.utils import join_cases, split_cases


class Product(BaseElement):
    """Represents a KORF Product node (boundary condition at the outlet).

    Example::

        prod = model.products[1]
        print(prod.pressure_string)  # '1000'
        prod.set_pressure(1200)
    """

    ETYPE = "PROD"

    def __init__(self, parser, index: int):
        super().__init__(parser, "PROD", index)

    @property
    def type(self) -> str:
        return str(self._scalar("TYPE", 0, "Pipe"))

    @property
    def elevation_m(self) -> float:
        try:
            return float(self._scalar("ELEV", 0, 0.0))
        except (TypeError, ValueError):
            return 0.0

    # Pressure
    @property
    def pressure_string(self) -> str:
        return str(self._scalar("PRES", 0, ""))

    @property
    def pressure_kPag(self) -> float:
        """Calculated inlet pressure [kPag]."""
        try:
            return float(self._scalar("PIN", 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    def get_pressure(self) -> list[str]:
        return split_cases(self.pressure_string)

    def set_pressure(self, pressure: list | str | float) -> None:
        if isinstance(pressure, (list, tuple)):
            p_str = join_cases(pressure)
        elif isinstance(pressure, (int, float)):
            p_str = str(pressure)
        else:
            p_str = str(pressure)

        rec = self._get("PRES")
        if rec:
            new_vals = [p_str] + rec.values[1:]
            self._set("PRES", new_vals)

    @property
    def nozzle_pipe_index(self) -> int:
        try:
            return int(self._scalar("NOZ", 0, 0))
        except (TypeError, ValueError):
            return 0
