r"""Product (sink / boundary condition) element (``\\PROD``)."""

from __future__ import annotations

from pykorf.core.elements.base import BaseElement
from pykorf.core.utils import join_cases, split_cases


class Product(BaseElement):
    """Represents a KORF Product node (boundary condition at the outlet).

    Example::

        prod = model.products[1]
        print(prod.pressure_string)  # '1000'
        prod.set_pressure(1200)
    """

    ETYPE = "PROD"
    ENAME = "Product"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/prod.py)
    # ------------------------------------------------------------------
    XY = "XY"  # [icon_x, icon_y] - 1 coordinate pair (icon anchor position only)
    TYPE = "TYPE"  # ["prod_type"]
    ELEV = "ELEV"  # [elevation, unit]
    LEVELH = "LEVELH"  # [level1, level2, unit, level4, unit, level6]
    PRES = "PRES"  # [pres_str, pres_num, unit]
    PIN = "PIN"  # [pres_in_str, pres_in_num, unit]
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
        PIN,
        DP,
        EQN,
        CHOKE,
        "NOTES",
    )

    def __init__(self, parser, index: int):
        super().__init__(parser, "PROD", index)

    @property
    def type(self) -> str:
        return str(self._scalar(Product.TYPE, 0))

    @property
    def elevation_m(self) -> float:
        try:
            return float(self._scalar(Product.ELEV, 0))
        except (TypeError, ValueError):
            return 0.0

    # Pressure
    @property
    def pressure_string(self) -> str:
        return str(self._scalar(Product.PRES, 0))

    @property
    def pressure_kPag(self) -> float:
        """Calculated inlet pressure [kPag]."""
        try:
            return float(self._scalar(Product.PIN, 1))
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

        rec = self.get_param(Product.PRES)
        if rec:
            new_vals = [p_str, *rec.values[1:]]
            self.set_param(Product.PRES, new_vals)

    @property
    def nozzle_pipe_index(self) -> int:
        try:
            return int(self._scalar(self.NOZ, 0))
        except (TypeError, ValueError):
            return 0

    def summary(self, export: bool = False) -> dict:
        if export:
            pres_val, pres_unit = self.get_value_and_unit(Product.PIN, val_index=1, unit_index=-1)
            display_name = f"{self.name} , {self.description}" if self.description else self.name
            return {
                "Product Name": display_name,
                "Type": self.type,
                self.format_export_header("Inlet Pressure", pres_unit): pres_val,
            }

        return {
            "name": self.name,
            "type": self.type,
            "pressure_kPag": self.pressure_kPag,
        }
