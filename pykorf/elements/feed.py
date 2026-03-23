r"""Feed (source / boundary condition) element (``\\FEED``)."""

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
    ENAME = "Feed"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/feed.py)
    # ------------------------------------------------------------------
    TYPE = "TYPE"  # ["feed_type"]
    ELEV = "ELEV"  # [elevation, unit]
    LEVELH = "LEVELH"  # [level1, level2, unit, level4, unit, level6]
    PRES = "PRES"  # [pres_str, pres_num, unit]
    POUT = "POUT"  # [pres_out_str, pres_out_num, unit]
    DP = "DP"  # [dp_str, dp_num, unit]
    EQN = "EQN"  # [eqn_type, ..., ..., ..., ...]
    CHOKE = "CHOKE"  # [choke_bool]

    ALL = (
        "NUM",
        "NAME",
        "XY",
        "ROT",
        "FLIP",
        "LBL",
        "COLOR",
        TYPE,
        ELEV,
        LEVELH,
        "NOZL",
        PRES,
        POUT,
        DP,
        EQN,
        CHOKE,
        "NOTES",
    )

    def __init__(self, parser, index: int):
        super().__init__(parser, "FEED", index)

    @property
    def type(self) -> str:
        return str(self._scalar(Feed.TYPE, 0))

    @property
    def elevation_m(self) -> float:
        try:
            return float(self._scalar(Feed.ELEV, 0))
        except (TypeError, ValueError):
            return 0.0

    # Pressure
    @property
    def pressure_string(self) -> str:
        return str(self._scalar(Feed.PRES, 0))

    @property
    def pressure_kPag(self) -> float:
        """Calculated outlet pressure [kPag]."""
        try:
            return float(self._scalar(Feed.POUT, 1))
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

        rec = self.get_param(Feed.PRES)
        if rec:
            new_vals = [p_str, *rec.values[1:]]
            self.set_param(Feed.PRES, new_vals)

    @property
    def dp_string(self) -> str:
        return str(self._scalar(Feed.DP, 0))

    @property
    def nozzle_pipe_index(self) -> int:
        """Index of the pipe connected at this feed."""
        try:
            return int(self._scalar(self.NOZ, 0))
        except (TypeError, ValueError):
            return 0

    def summary(self, export: bool = False) -> dict:
        if export:
            pres_val, pres_unit = self.get_value_and_unit(Feed.POUT, val_index=1, unit_index=-1)
            return {
                "Feed Name": self.name,
                "Type": self.type,
                self.format_export_header("Outlet Pressure", pres_unit): pres_val,
            }

        return {
            "name": self.name,
            "type": self.type,
            "pressure_kPag": self.pressure_kPag,
        }
