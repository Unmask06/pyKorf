"""PipeData element (``\\PIPEDATA``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class PipeData(BaseElement):
    """Represents a pipe data library entry (material, roughness, schedules, diameters)."""

    ETYPE = "PIPEDATA"
    ENAME = "Pipe Data"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/pipedata.py)
    # ------------------------------------------------------------------
    MAT = "MAT"
    PROP = "PROP"
    E = "E"
    NSS = "NSS"
    IDIA = "IDIA"
    SDIA = "SDIA"
    UNITS = "UNITS"
    SCH = "SCH"
    DIA = "DIA"

    ALL = (
        "NUM",
        MAT,
        "NOTES",
        PROP,
        E,
        NSS,
        IDIA,
        SDIA,
        UNITS,
        SCH,
        DIA,
    )

    def __init__(self, parser, index: int):
        super().__init__(parser, "PIPEDATA", index)

    @property
    def material(self) -> str:
        return self._scalar(PipeData.MAT, 0, "")

    @property
    def roughness_m(self) -> float:
        try:
            return float(self._scalar(PipeData.E, 0, 0.0))
        except (TypeError, ValueError):
            return 0.0

    @property
    def schedules(self) -> list[str]:
        return [str(s) for s in self._values(PipeData.SCH)]

    def get_diameters(self) -> list[dict]:
        """Return a list of nominal diameters and their corresponding ID values."""
        results = []
        # DIA records are like: index, nominal_string, od, [ids...]
        for rec in self._parser.records:
            if (
                rec.element_type == "PIPEDATA"
                and rec.index == self._index
                and rec.param == PipeData.DIA
            ):
                results.append(
                    {
                        "id": rec.values[0],
                        "nominal": rec.values[1],
                        "od": rec.values[2],
                        "ids": rec.values[4:],  # index 3 seems to be a flag or something
                    }
                )
        return results
