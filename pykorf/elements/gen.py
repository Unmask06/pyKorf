r"""General / project-wide settings element (``\\GEN``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class General(BaseElement):
    r"""Wraps the ``\\GEN,0,...`` records (always index 0, only one instance).

    Also carries all GEN parameter string constants as class attributes
    so that callers can write ``General.CASENO`` instead of a bare string.

    Typical usage::

        gen = model.general
        print(gen.units)  # 'Metric'
        print(gen.cases)  # ['1', '2', '3']
        gen.set_cases(["1", "2", "3"], ["NORMAL", "RATED", "MINIMUM"])
    """

    ETYPE = "GEN"
    ENAME = "General"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/gen.py)
    # ------------------------------------------------------------------
    VERNO = "VERNO"
    COM = "COM"
    PRJ = "PRJ"
    ENG = "ENG"
    UNITS = "UNITS"
    UNITS1 = "UNITS1"
    UNITS2 = "UNITS2"
    UNITS3 = "UNITS3"
    UNITS4 = "UNITS4"
    UNITS6 = "UNITS6"
    PATM = "PATM"
    DWGSTD = "DWGSTD"
    DWGSIZ = "DWGSIZ"
    DWGMAR = "DWGMAR"
    DWGGRD = "DWGGRD"
    DWGCON = "DWGCON"
    DWGBOR = "DWGBOR"
    RPTSIZ = "RPTSIZ"
    PRTWID = "PRTWID"
    MITER = "MITER"
    MSOS = "MSOS"
    MFIT = "MFIT"
    MFT = "MFT"
    MCOMP = "MCOMP"
    MTP = "MTP"
    MDELEV = "MDELEV"
    MDUKHP = "MDUKHP"
    MDUKF = "MDUKF"
    MACCEL = "MACCEL"
    MSONIC = "MSONIC"
    MHDAMP = "MHDAMP"
    MSIM = "MSIM"
    MFLASH = "MFLASH"
    MFLASHK = "MFLASHK"
    MFLASHH = "MFLASHH"
    MVAPK = "MVAPK"
    MQLOSS = "MQLOSS"
    MFLASHR = "MFLASHR"
    MXYDAMP = "MXYDAMP"
    MKE = "MKE"
    M3PHASE = "M3PHASE"
    MHVYCOMP = "MHVYCOMP"
    MPPP = "MPPP"
    MHYSYS = "MHYSYS"
    MHVIEW = "MHVIEW"
    MFODEN = "MFODEN"
    MCVDEN = "MCVDEN"
    MCVFL = "MCVFL"
    MPCURV = "MPCURV"
    MCOL = "MCOL"
    PCURQ = "PCURQ"
    PCURH = "PCURH"
    PCUREFF = "PCUREFF"
    PCURNPSH = "PCURNPSH"
    CCURQ = "CCURQ"
    CCURH = "CCURH"
    CCUREFF = "CCUREFF"
    CASENO = "CASENO"
    CASEDSC = "CASEDSC"
    CASERPT = "CASERPT"
    CASEDLG = "CASEDLG"
    DIRLIC = "DIRLIC"
    DIRLIB = "DIRLIB"
    DIRINI = "DIRINI"
    DIRDAT = "DIRDAT"

    ALL = (
        VERNO,
        COM,
        PRJ,
        ENG,
        UNITS,
        UNITS1,
        UNITS2,
        UNITS3,
        UNITS4,
        UNITS6,
        PATM,
        DWGSTD,
        DWGSIZ,
        DWGMAR,
        DWGGRD,
        DWGCON,
        DWGBOR,
        RPTSIZ,
        PRTWID,
        MITER,
        MSOS,
        MFIT,
        MFT,
        MCOMP,
        MTP,
        MDELEV,
        MDUKHP,
        MDUKF,
        MACCEL,
        MSONIC,
        MHDAMP,
        MSIM,
        MFLASH,
        MFLASHK,
        MFLASHH,
        MVAPK,
        MQLOSS,
        MFLASHR,
        MXYDAMP,
        MKE,
        M3PHASE,
        MHVYCOMP,
        MPPP,
        MHYSYS,
        MHVIEW,
        MFODEN,
        MCVDEN,
        MCVFL,
        MPCURV,
        MCOL,
        PCURQ,
        PCURH,
        PCUREFF,
        PCURNPSH,
        CCURQ,
        CCURH,
        CCUREFF,
        CASENO,
        CASEDSC,
        CASERPT,
        CASEDLG,
        DIRLIC,
        DIRLIB,
        DIRINI,
        DIRDAT,
    )

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
        """Unit system, e.g. ``'Metric'``, ``'Imperial'`` or ``'Custom'``."""
        return self._scalar("UNITS", 0, "Metric")

    @property
    def units_definitions(self) -> list[str]:
        """Detailed unit strings from UNITS1-6 records."""
        results = []
        for i in range(1, 7):
            results.extend(self._values(f"UNITS{i}"))
        return results

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
        """List of active case numbers, e.g. ``['1', '2', '3']``.
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
        """Update the active case set.

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
