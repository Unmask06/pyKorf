r"""Junction element (``\\JUNC``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class Junction(BaseElement):
    """Multi-connection junction node."""

    ETYPE = "JUNC"
    ENAME = "Junction"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/junc.py)
    # ------------------------------------------------------------------
    PRES = "PRES"  # [pres_str, pres_num, unit]
    LBL = "LBL"  # [on/off, x-offset, y-offset]

    ALL = (
        "NUM",
        "NAME",
        "XY",
        "ROT",
        "FLIP",
        "LBL",
        "COLOR",
        PRES,
        "NOZI",
        "NOZO",
    )

    def __init__(self, parser, index: int):
        super().__init__(parser, "JUNC", index)

    @property
    def pressure_kPag(self) -> float:
        try:
            return float(self._scalar(Junction.PRES, 1))
        except (TypeError, ValueError):
            return 0.0

    def summary(self, export: bool = False) -> dict:
        if export:
            pres_val, pres_unit = self.get_value_and_unit(Junction.PRES, val_index=1, unit_index=-1)
            return {
                "Junction Name": self.name,
                self.format_export_header("Pressure", pres_unit): pres_val,
            }

        return {
            "name": self.name,
            "pressure_kPag": self.pressure_kPag,
        }
