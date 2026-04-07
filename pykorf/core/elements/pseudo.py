r"""Pseudo-component element (``\\PSEUDO``)."""

from __future__ import annotations

from pykorf.core.elements.base import BaseElement


class Pseudo(BaseElement):
    r"""Wraps ``\\PSEUDO`` records - user-defined pseudo-component fluid data.

    This is a lightweight stub carrying only the KDF parameter constants.
    """

    ETYPE = "PSEUDO"
    ENAME = "Pseudo"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/pseudo.py)
    # ------------------------------------------------------------------
    FOR = "FOR"  # [formula, description]
    MW = "MW"  # [mw1, mw2]
    TFP = "TFP"  # [tfp1, tfp2, unit]
    TBP = "TBP"  # [tbp1, tbp2, unit]
    TC = "TC"  # [tc1, tc2, unit]
    PC = "PC"  # [pc1, pc2, unit]
    VC = "VC"  # [vc1, vc2, unit]
    ZC = "ZC"  # [zc1, zc2]
    ACC = "ACC"  # [acc1, acc2]
    DENS = "DENS"  # [dens1, dens2, unit]
    DENT = "DENT"  # [dent1, dent2, unit, dent4, dent5, unit]
    DIPM = "DIPM"  # [dipm1, dipm2]
    CP = "CP"  # [cp1, cp2, ..., cp10, unit]
    VISC = "VISC"  # [visc1, visc2, ..., visc10, unit]
    HVAP = "HVAP"  # [hvap1, hvap2]
    HFOR = "HFOR"  # [hfor1, hfor2]
    ANT = "ANT"  # [ant1, ant2, ..., ant10, unit, ant12, ant13, ant14, ant15, unit]

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
