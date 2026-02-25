"""General / project-wide settings element (``\\GEN``)."""

from __future__ import annotations
from pykorf.elements.base import BaseElement


class General(BaseElement):
    """
    Wraps the ``\\GEN,0,...`` records (always index 0, only one instance).

    Typical usage::

        gen = model.general
        print(gen.units)      # 'Metric'
        print(gen.cases)      # ['1', '2', '3']
        gen.set_cases(['1','2','3'], ['NORMAL','RATED','MINIMUM'])
    """

    ETYPE = "GEN"

    def __init__(self, parser):
        super().__init__(parser, "GEN", 0)

    # ------------------------------------------------------------------
    # Project metadata
    # ------------------------------------------------------------------

    @property
    def company(self) -> str:
        return self._scalar("COM", 0, "")

    @property
    def project(self) -> str:
        return self._scalar("PRJ", 0, "")

    @property
    def units(self) -> str:
        """Unit system, e.g. ``'Metric'``."""
        return self._scalar("UNITS", 0, "Metric")

    @property
    def patm(self) -> float:
        """Atmospheric pressure (kPa)."""
        try:
            return float(self._scalar("PATM", 0, 101))
        except (TypeError, ValueError):
            return 101.0

    # ------------------------------------------------------------------
    # Cases
    # ------------------------------------------------------------------

    @property
    def case_numbers(self) -> list[str]:
        """
        List of active case numbers, e.g. ``['1', '2', '3']``.
        Parsed from the ``CASENO`` semicolon string.
        """
        raw = self._scalar("CASENO", 0, "")
        return [c.strip() for c in str(raw).split(";") if c.strip()]

    @property
    def case_descriptions(self) -> list[str]:
        """List of case descriptions, e.g. ``['NORMAL', 'RATED', 'MINIMUM']``."""
        raw = self._scalar("CASEDSC", 0, "")
        return [c.strip() for c in str(raw).split(";") if c.strip()]

    @property
    def num_cases(self) -> int:
        return len(self.case_numbers)

    def set_cases(
        self,
        numbers: list[str | int],
        descriptions: list[str] | None = None,
    ) -> None:
        """
        Update the active case set.

        Parameters
        ----------
        numbers:
            Ordered list of case identifiers, e.g. ``[1, 2, 3]``.
        descriptions:
            Optional matching list of descriptions.
        """
        no_str = ";".join(str(n) for n in numbers)
        self._set("CASENO", [no_str])
        if descriptions:
            desc_str = ";".join(descriptions)
            self._set("CASEDSC", [desc_str])

    # ------------------------------------------------------------------
    # Modelling options
    # ------------------------------------------------------------------

    @property
    def compressibility_model(self) -> str:
        return self._scalar("MCOMP", 0, "")

    @property
    def two_phase_model(self) -> str:
        return self._scalar("MTP", 0, "")

    # ------------------------------------------------------------------
    # Pump / compressor curve defaults
    # ------------------------------------------------------------------

    @property
    def pump_curve_q(self) -> list[str]:
        return self._values("PCURQ")[:-1]  # last token is unit

    @property
    def pump_curve_h(self) -> list[str]:
        return self._values("PCURH")[:-1]

    @property
    def pump_curve_eff(self) -> list[str]:
        return self._values("PCUREFF")[:-1]
