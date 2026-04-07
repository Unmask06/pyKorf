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
    VERNO = "VERNO"  # [version_str]
    COM = "COM"  # [company1, company2]
    PRJ = "PRJ"  # [project_name1, project_name2, item_name1, item_name2]
    ENG = "ENG"  # [prepared_by, checked_by, approved_by, date, project_no, revision]
    UNITS = "UNITS"  # ["unit_system"]
    UNITS1 = "UNITS1"  # [u1, u2, u3, u4, u5, u6]
    UNITS2 = "UNITS2"  # [u1, u2, u3, u4, u5, u6]
    UNITS3 = "UNITS3"  # [u1, u2, u3, u4, u5]
    UNITS4 = "UNITS4"  # [u1, u2]
    UNITS6 = "UNITS6"  # [u1, u2, u3, u4, u5]
    PATM = "PATM"  # [patm, unit]
    DWGSTD = "DWGSTD"  # ["Page Size"]
    DWGSIZ = "DWGSIZ"  # [width, height, unit]
    DWGMAR = "DWGMAR"  # [margin, unit]
    DWGGRD = "DWGGRD"  # [grid on-off, grid_spacing] [0 = off, 1 = on]
    DWGCON = "DWGCON"  # [dwgcon]
    DWGBOR = "DWGBOR"  # [dwgbor]
    RPTSIZ = "RPTSIZ"  # [rpt_size, rpt_margin, unit, font_size, unit]
    PRTWID = "PRTWID"  # [width, unit]
    MITER = "MITER"  # [miter_angle]
    MSOS = "MSOS"  # [sos_const]
    MFIT = "MFIT"  # ["fittings_source"]
    MFT = "MFT"  # [mft]
    MCOMP = "MCOMP"  # ["compressibility_model"]
    MTP = "MTP"  # ["two_phase_model"]
    MDELEV = "MDELEV"  # ["elevation_model"]
    MDUKHP = "MDUKHP"  # ["duk_hp_model"]
    MDUKF = "MDUKF"  # [mdukf]
    MACCEL = "MACCEL"  # ["acceleration_model"]
    MSONIC = "MSONIC"  # ["sonic_model"]
    MHDAMP = "MHDAMP"  # [h_damp]
    MSIM = "MSIM"  # [sim1, sim2]
    MFLASH = "MFLASH"  # ["flash_model"]
    MFLASHK = "MFLASHK"  # ["k_model"]
    MFLASHH = "MFLASHH"  # ["h_model"]
    MVAPK = "MVAPK"  # ["vap_k_model"]
    MQLOSS = "MQLOSS"  # ["q_loss_model"]
    MFLASHR = "MFLASHR"  # [flash_r]
    MXYDAMP = "MXYDAMP"  # [xy_damp]
    MKE = "MKE"  # [mke]
    M3PHASE = "M3PHASE"  # [m3phase]
    MHVYCOMP = "MHVYCOMP"  # ["heavy_comp"]
    MPPP = "MPPP"  # [mppp]
    MHYSYS = "MHYSYS"  # ["hysys_model"]
    MHVIEW = "MHVIEW"  # [mhview]
    MFODEN = "MFODEN"  # ["fo_den_model"]
    MCVDEN = "MCVDEN"  # ["cv_den_model"]
    MCVFL = "MCVFL"  # ["cv_fl_model"]
    MPCURV = "MPCURV"  # [mpcurv1, mpcurv2]
    MCOL = "MCOL"  # [col1, col2, col3, col4]
    PCURQ = "PCURQ"  # [q1, q2, ..., q10, unit]
    PCURH = "PCURH"  # [h1, h2, ..., h10, unit]
    PCUREFF = "PCUREFF"  # [eff1, eff2, ..., eff10, unit]
    PCURNPSH = "PCURNPSH"  # [npsh1, npsh2, ..., npsh10, unit]
    CCURQ = "CCURQ"  # [q1, q2, ..., q10, unit]
    CCURH = "CCURH"  # [h1, h2, ..., h10, unit]
    CCUREFF = "CCUREFF"  # [eff1, eff2, ..., eff10, unit]
    CASENO = "CASENO"  # ["cases_str"]
    CASEDSC = "CASEDSC"  # ["descriptions_str"]
    CASERPT = "CASERPT"  # ["reports_str"]
    CASEDLG = "CASEDLG"  # [casedlg]
    DIRLIC = "DIRLIC"  # ["license_dir"]
    DIRLIB = "DIRLIB"  # ["library_dir"]
    DIRINI = "DIRINI"  # ["ini_dir"]
    DIRDAT = "DIRDAT"  # ["data_dir"]

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
        return self._scalar("COM", 0)

    @property
    def project(self) -> str:
        return self._scalar("PRJ", 0)

    @property
    def company2(self) -> str:
        """COM[1]: second company name / sub-company."""
        return self._scalar("COM", 1)

    @property
    def project_name2(self) -> str:
        """PRJ[1]: secondary project name."""
        return self._scalar("PRJ", 1)

    @property
    def item_name1(self) -> str:
        """PRJ[2]: document number / item name 1."""
        return self._scalar("PRJ", 2)

    @property
    def item_name2(self) -> str:
        """PRJ[3]: item tag / item name 2."""
        return self._scalar("PRJ", 3)

    @property
    def prepared_by(self) -> str:
        """ENG[0]: prepared by initials or name."""
        return self._scalar("ENG", 0)

    @property
    def checked_by(self) -> str:
        """ENG[1]: checked by initials or name."""
        return self._scalar("ENG", 1)

    @property
    def approved_by(self) -> str:
        """ENG[2]: approved by initials or name."""
        return self._scalar("ENG", 2)

    @property
    def date(self) -> str:
        """ENG[3]: document date string."""
        return self._scalar("ENG", 3)

    @property
    def project_no(self) -> str:
        """ENG[4]: project number."""
        return self._scalar("ENG", 4)

    @property
    def revision(self) -> str:
        """ENG[5]: document revision."""
        return self._scalar("ENG", 5)

    def set_company(self, company1: str, company2: str = "") -> None:
        """Set company names (COM record).

        Args:
            company1: Primary company name. COM[0].
            company2: Secondary company / sub-company. COM[1].
        """
        self.set_param("COM", [company1, company2])

    def set_project(
        self,
        name1: str,
        name2: str = "",
        item_name1: str = "",
        item_name2: str = "",
    ) -> None:
        """Set project names (PRJ record).

        Args:
            name1: Primary project name. PRJ[0].
            name2: Secondary project name. PRJ[1].
            item_name1: Document number / item name 1. PRJ[2].
            item_name2: Item tag / item name 2. PRJ[3].
        """
        self.set_param("PRJ", [name1, name2, item_name1, item_name2])

    def set_engineering(
        self,
        prepared_by: str = "",
        checked_by: str = "",
        approved_by: str = "",
        date: str = "",
        project_no: str = "",
        revision: str = "",
    ) -> None:
        """Set engineering title block fields (ENG record).

        Args:
            prepared_by: Prepared by initials. ENG[0].
            checked_by: Checked by initials. ENG[1].
            approved_by: Approved by initials. ENG[2].
            date: Document date string. ENG[3].
            project_no: Project number. ENG[4].
            revision: Document revision. ENG[5].
        """
        self.set_param("ENG", [prepared_by, checked_by, approved_by, date, project_no, revision])

    @property
    def units(self) -> str:
        """Unit system, e.g. ``'Metric'``, ``'Imperial'`` or ``'Custom'``."""
        return self._scalar("UNITS", 0)

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
            return float(self._scalar("PATM", 0))
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
        raw = self._scalar("CASENO", 0)
        return [c.strip() for c in str(raw).split(";") if c.strip()]

    @property
    def case_descriptions(self) -> list[str]:
        """List of case descriptions, e.g. ``['NORMAL', 'RATED', 'MINIMUM']``."""
        raw = self._scalar("CASEDSC", 0)
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
        self.set_param("CASENO", [no_str])
        if descriptions:
            desc_str = ";".join(descriptions)
            self.set_param("CASEDSC", [desc_str])

    # ------------------------------------------------------------------
    # Modelling options
    # ------------------------------------------------------------------

    @property
    def compressibility_model(self) -> str:
        return self._scalar("MCOMP", 0)

    @property
    def two_phase_model(self) -> str:
        return self._scalar("MTP", 0)

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
