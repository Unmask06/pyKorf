r"""Pseudo-component element (``\\PSEUDO``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class Pseudo(BaseElement):
    r"""Wraps ``\\PSEUDO`` records - user-defined pseudo-component fluid data.

    This is a lightweight stub carrying only the KDF parameter constants.
    """

    ETYPE = "PSEUDO"
    ENAME = "Pseudo"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/pseudo.py)
    # ------------------------------------------------------------------
    FOR = "FOR"
    MW = "MW"
    TFP = "TFP"
    TBP = "TBP"
    TC = "TC"
    PC = "PC"
    VC = "VC"
    ZC = "ZC"
    ACC = "ACC"
    DENS = "DENS"
    DENT = "DENT"
    DIPM = "DIPM"
    CP = "CP"
    VISC = "VISC"
    HVAP = "HVAP"
    HFOR = "HFOR"
    ANT = "ANT"

    ALL = (
        "NUM",
        "NAME",
        FOR,
        MW,
        TFP,
        TBP,
        TC,
        PC,
        VC,
        ZC,
        ACC,
        DENS,
        DENT,
        DIPM,
        CP,
        VISC,
        HVAP,
        HFOR,
        ANT,
    )
