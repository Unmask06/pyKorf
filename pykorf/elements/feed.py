"""Feed (source / boundary condition) element (``\\FEED``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement
from pykorf.utils import join_cases, split_cases


class Feed(BaseElement):
    """Represents a KORF Feed node (boundary condition at the inlet).

    Example::

        feed = model.feeds[1]
        print(feed.pressure_kPag)  # 50.0
        feed.set_pressure("50;55;30")  # multi-case
    """

    ETYPE = "FEED"

    def __init__(self, parser, index: int):
        super().__init__(parser, "FEED", index)

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
        """Calculated outlet pressure [kPag]."""
        try:
            return float(self._scalar("POUT", 1, 0.0))
        except (TypeError, ValueError):
            return 0.0

    def get_pressure(self) -> list[str]:
        return split_cases(self.pressure_string)

    def set_pressure(self, pressure: list | str | float) -> None:
        """Set the feed pressure specification.

        Parameters
        ----------
        pressure:
            Semicolon string ``"50;55;30"``, a list ``[50, 55, 30]``,
            or a single value applied to all cases.
        """
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
    def dp_string(self) -> str:
        return str(self._scalar("DP", 0, "0"))

    @property
    def nozzle_pipe_index(self) -> int:
        """Index of the pipe connected at this feed."""
        try:
            return int(self._scalar("NOZ", 0, 0))
        except (TypeError, ValueError):
            return 0
