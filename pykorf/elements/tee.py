"""Tee piece element (``\\TEE``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class Tee(BaseElement):
    """Represents a 3-way tee piece."""

    ETYPE = "TEE"

    def __init__(self, parser, index: int):
        super().__init__(parser, "TEE", index)

    @property
    def tee_type(self) -> int:
        try:
            return int(self._scalar("TYPE", 0, 0))
        except (TypeError, ValueError):
            return 0

    @property
    def pressures_kPag(self) -> list[float]:
        vals = self._values("PRES")
        nums = vals[:-1] if vals and isinstance(vals[-1], str) else vals
        result = []
        for v in nums:
            try:
                result.append(float(v))
            except (TypeError, ValueError):
                pass
        return result
