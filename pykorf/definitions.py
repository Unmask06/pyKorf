"""Centralized KDF element and property definitions.

This module provides string constants for element types and their valid
parameter keys, derived from ``library/New.kdf``.

Examples:
--------
>>> from pykorf.definitions import Element, Pipe
>>> Element.PIPE
'PIPE'
>>> Pipe.PRES
'PRES'
"""

from __future__ import annotations


class Element:
    """KDF element type tokens."""

    GEN = "GEN"
    PIPE = "PIPE"
    FEED = "FEED"
    PROD = "PROD"
    VALVE = "VALVE"
    CHECK = "CHECK"
    ORIFICE = "FO"
    HX = "HX"
    PUMP = "PUMP"
    COMP = "COMP"
    MISC = "MISC"
    EXPAND = "EXPAND"
    JUNC = "JUNC"
    TEE = "TEE"
    VESSEL = "VESSEL"
    SYMBOL = "SYMBOL"
    TOOLS = "TOOLS"
    PSEUDO = "PSEUDO"
    PIPEDATA = "PIPEDATA"

    ALL = (
        GEN,
        PIPE,
        FEED,
        PROD,
        VALVE,
        CHECK,
        ORIFICE,
        HX,
        PUMP,
        COMP,
        MISC,
        EXPAND,
        JUNC,
        TEE,
        VESSEL,
        SYMBOL,
        TOOLS,
        PSEUDO,
        PIPEDATA,
    )


class Gen:
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


class Pipe:
    NUM = "NUM"
    NAME = "NAME"
    BEND = "BEND"
    XY = "XY"
    LBL = "LBL"
    COLOR = "COLOR"
    STRM = "STRM"
    LOCK = "LOCK"
    TEMP = "TEMP"
    PRES = "PRES"
    LF = "LF"
    H = "H"
    HAMB = "HAMB"
    S = "S"
    FT = "FT"
    Q = "Q"
    UI = "UI"
    TAMB = "TAMB"
    DAMB = "DAMB"
    TSUR = "TSUR"
    QFAC = "QFAC"
    QNTU = "QNTU"
    QAIR = "QAIR"
    QPIP = "QPIP"
    QINS = "QINS"
    REFLINE = "REFLINE"
    OUTIN = "OUTIN"
    LVFLOW = "LVFLOW"
    LIQDEN = "LIQDEN"
    LIQVISC = "LIQVISC"
    LIQSUR = "LIQSUR"
    LIQCON = "LIQCON"
    LIQCP = "LIQCP"
    LIQMW = "LIQMW"
    VAPDEN = "VAPDEN"
    VAPVISC = "VAPVISC"
    VAPMW = "VAPMW"
    VAPZ = "VAPZ"
    VAPK = "VAPK"
    VAPCON = "VAPCON"
    VAPCP = "VAPCP"
    TFLOW = "TFLOW"
    TPROP = "TPROP"
    TOTCON = "TOTCON"
    TOTCP = "TOTCP"
    TOTMW = "TOTMW"
    PSAT = "PSAT"
    OMEGA = "OMEGA"
    RS = "RS"
    YW = "YW"
    MAT = "MAT"
    DIA = "DIA"
    ID = "ID"
    IDH = "IDH"
    ODF = "ODF"
    SCH = "SCH"
    LEN = "LEN"
    EQLEN = "EQLEN"
    FITK = "FITK"
    FITLD = "FITLD"
    FITLR = "FITLR"
    FIT1 = "FIT1"
    FIT2 = "FIT2"
    FIT3 = "FIT3"
    FIT4 = "FIT4"
    FIT5 = "FIT5"
    FIT6 = "FIT6"
    FIT7 = "FIT7"
    FIT8 = "FIT8"
    FIT9 = "FIT9"
    FIT10 = "FIT10"
    FIT11 = "FIT11"
    SELEV = "SELEV"
    DPELEV = "DPELEV"
    DPFRIC = "DPFRIC"
    DPACCEL = "DPACCEL"
    ELEV = "ELEV"
    FAC = "FAC"
    EPS = "EPS"
    F = "F"
    RE = "RE"
    SIZ = "SIZ"
    DPL = "DPL"
    VEL = "VEL"
    HUP = "HUP"
    REG = "REG"
    REGA = "REGA"
    MTP = "MTP"
    DUK = "DUK"
    LM = "LM"
    EQN = "EQN"
    NOTES = "NOTES"
    FILES = "FILES"

    ALL = (
        NUM,
        NAME,
        BEND,
        XY,
        LBL,
        COLOR,
        STRM,
        LOCK,
        TEMP,
        PRES,
        LF,
        H,
        HAMB,
        S,
        FT,
        Q,
        UI,
        TAMB,
        DAMB,
        TSUR,
        QFAC,
        QNTU,
        QAIR,
        QPIP,
        QINS,
        REFLINE,
        OUTIN,
        LVFLOW,
        LIQDEN,
        LIQVISC,
        LIQSUR,
        LIQCON,
        LIQCP,
        LIQMW,
        VAPDEN,
        VAPVISC,
        VAPMW,
        VAPZ,
        VAPK,
        VAPCON,
        VAPCP,
        TFLOW,
        TPROP,
        TOTCON,
        TOTCP,
        TOTMW,
        PSAT,
        OMEGA,
        RS,
        YW,
        MAT,
        DIA,
        ID,
        IDH,
        ODF,
        SCH,
        LEN,
        EQLEN,
        FITK,
        FITLD,
        FITLR,
        FIT1,
        FIT2,
        FIT3,
        FIT4,
        FIT5,
        FIT6,
        FIT7,
        FIT8,
        FIT9,
        FIT10,
        FIT11,
        SELEV,
        DPELEV,
        DPFRIC,
        DPACCEL,
        ELEV,
        FAC,
        EPS,
        F,
        RE,
        SIZ,
        DPL,
        VEL,
        HUP,
        REG,
        REGA,
        MTP,
        DUK,
        LM,
        EQN,
        NOTES,
        FILES,
    )


class Feed:
    NUM = "NUM"
    NAME = "NAME"
    XY = "XY"
    ROT = "ROT"
    FLIP = "FLIP"
    LBL = "LBL"
    COLOR = "COLOR"
    TYPE = "TYPE"
    ELEV = "ELEV"
    LEVELH = "LEVELH"
    NOZL = "NOZL"
    PRES = "PRES"
    POUT = "POUT"
    DP = "DP"
    EQN = "EQN"
    CHOKE = "CHOKE"
    NOTES = "NOTES"

    ALL = (
        NUM,
        NAME,
        XY,
        ROT,
        FLIP,
        LBL,
        COLOR,
        TYPE,
        ELEV,
        LEVELH,
        NOZL,
        PRES,
        POUT,
        DP,
        EQN,
        CHOKE,
        NOTES,
    )


class Prod:
    NUM = "NUM"
    NAME = "NAME"
    XY = "XY"
    ROT = "ROT"
    FLIP = "FLIP"
    LBL = "LBL"
    COLOR = "COLOR"
    TYPE = "TYPE"
    ELEV = "ELEV"
    LEVELH = "LEVELH"
    NOZL = "NOZL"
    PRES = "PRES"
    PIN = "PIN"
    DP = "DP"
    EQN = "EQN"
    CHOKE = "CHOKE"
    NOTES = "NOTES"

    ALL = (
        NUM,
        NAME,
        XY,
        ROT,
        FLIP,
        LBL,
        COLOR,
        TYPE,
        ELEV,
        LEVELH,
        NOZL,
        PRES,
        PIN,
        DP,
        EQN,
        CHOKE,
        NOTES,
    )


class Valve:
    NUM = "NUM"
    NAME = "NAME"
    XY = "XY"
    ROT = "ROT"
    FLIP = "FLIP"
    LBL = "LBL"
    COLOR = "COLOR"
    CON = "CON"
    ELEV = "ELEV"
    DP = "DP"
    PIN = "PIN"
    POUT = "POUT"
    DPP = "DPP"
    PSAT = "PSAT"
    PCRIT = "PCRIT"
    THICK = "THICK"
    K = "K"
    CV = "CV"
    DIA = "DIA"
    TYPE2 = "TYPE2"
    TYPE = "TYPE"
    OPEN = "OPEN"
    OPENCV = "OPENCV"
    XT = "XT"
    FL = "FL"
    YIN = "YIN"
    FP2 = "FP2"
    CHOKE = "CHOKE"
    OMEGA = "OMEGA"
    RS = "RS"
    XC = "XC"
    NDS = "NDS"
    MDEN = "MDEN"
    NOTES = "NOTES"

    ALL = (
        NUM,
        NAME,
        XY,
        ROT,
        FLIP,
        LBL,
        COLOR,
        CON,
        ELEV,
        DP,
        PIN,
        POUT,
        DPP,
        PSAT,
        PCRIT,
        THICK,
        K,
        CV,
        DIA,
        TYPE2,
        TYPE,
        OPEN,
        OPENCV,
        XT,
        FL,
        YIN,
        FP2,
        CHOKE,
        OMEGA,
        RS,
        XC,
        NDS,
        MDEN,
        NOTES,
    )


class Check:
    NUM = "NUM"
    NAME = "NAME"
    XY = "XY"
    ROT = "ROT"
    FLIP = "FLIP"
    LBL = "LBL"
    COLOR = "COLOR"
    CON = "CON"
    ELEV = "ELEV"
    DP = "DP"
    PIN = "PIN"
    POUT = "POUT"
    LD = "LD"

    ALL = (NUM, NAME, XY, ROT, FLIP, LBL, COLOR, CON, ELEV, DP, PIN, POUT, LD)


class Orifice:
    NUM = "NUM"
    NAME = "NAME"
    XY = "XY"
    COLOR = "COLOR"
    TYPE = "TYPE"
    ROT = "ROT"
    FLIP = "FLIP"
    LBL = "LBL"
    CON = "CON"
    ELEV = "ELEV"
    DP = "DP"
    DPF = "DPF"
    PIN = "PIN"
    POUT = "POUT"
    PSAT = "PSAT"
    HOLES = "HOLES"
    THICK = "THICK"
    BORE = "BORE"
    BETA = "BETA"
    BETAO = "BETAO"
    CD = "CD"
    YIN = "YIN"
    CHOKE = "CHOKE"
    OMEGA = "OMEGA"
    RS = "RS"
    RC = "RC"
    NDS = "NDS"
    MDEN = "MDEN"
    NOTES = "NOTES"

    ALL = (
        NUM,
        NAME,
        XY,
        COLOR,
        TYPE,
        ROT,
        FLIP,
        LBL,
        CON,
        ELEV,
        DP,
        DPF,
        PIN,
        POUT,
        PSAT,
        HOLES,
        THICK,
        BORE,
        BETA,
        BETAO,
        CD,
        YIN,
        CHOKE,
        OMEGA,
        RS,
        RC,
        NDS,
        MDEN,
        NOTES,
    )


class Hx:
    NUM = "NUM"
    NAME = "NAME"
    XY = "XY"
    ROT = "ROT"
    FLIP = "FLIP"
    LBL = "LBL"
    COLOR = "COLOR"
    TYPE = "TYPE"
    SIDE = "SIDE"
    NOZI = "NOZI"
    NOZO = "NOZO"
    DP = "DP"
    PIN = "PIN"
    POUT = "POUT"
    PRAT = "PRAT"
    K = "K"
    DPELEV = "DPELEV"
    Q = "Q"
    NOTES = "NOTES"

    ALL = (
        NUM,
        NAME,
        XY,
        ROT,
        FLIP,
        LBL,
        COLOR,
        TYPE,
        SIDE,
        NOZI,
        NOZO,
        DP,
        PIN,
        POUT,
        PRAT,
        K,
        DPELEV,
        Q,
        NOTES,
    )


class Pump:
    NUM = "NUM"
    NAME = "NAME"
    XY = "XY"
    ROT = "ROT"
    FLIP = "FLIP"
    LBL = "LBL"
    COLOR = "COLOR"
    CON = "CON"
    ELEV = "ELEV"
    DP = "DP"
    PIN = "PIN"
    POUT = "POUT"
    TYPE = "TYPE"
    EFFP = "EFFP"
    EFFS = "EFFS"
    POW = "POW"
    HQACT = "HQACT"
    CURRPM = "CURRPM"
    CURDIA = "CURDIA"
    CURVSD = "CURVSD"
    CURC1 = "CURC1"
    CURNP = "CURNP"
    CURQ = "CURQ"
    CURH = "CURH"
    CUREFF = "CUREFF"
    CURNPSH = "CURNPSH"
    NPSHA13 = "NPSHA13"
    NPSHR13 = "NPSHR13"
    NPSHAF = "NPSHAF"
    NPSHRE = "NPSHRE"
    NPSHVV = "NPSHVV"
    NPSHVT = "NPSHVT"
    PZPRES = "PZPRES"
    PZRAT = "PZRAT"
    PZVES = "PZVES"
    NOTES = "NOTES"

    ALL = (
        NUM,
        NAME,
        XY,
        ROT,
        FLIP,
        LBL,
        COLOR,
        CON,
        ELEV,
        DP,
        PIN,
        POUT,
        TYPE,
        EFFP,
        EFFS,
        POW,
        HQACT,
        CURRPM,
        CURDIA,
        CURVSD,
        CURC1,
        CURNP,
        CURQ,
        CURH,
        CUREFF,
        CURNPSH,
        NPSHA13,
        NPSHR13,
        NPSHAF,
        NPSHRE,
        NPSHVV,
        NPSHVT,
        PZPRES,
        PZRAT,
        PZVES,
        NOTES,
    )


class Comp:
    NUM = "NUM"
    NAME = "NAME"
    XY = "XY"
    ROT = "ROT"
    FLIP = "FLIP"
    LBL = "LBL"
    COLOR = "COLOR"
    CON = "CON"
    ELEV = "ELEV"
    DP = "DP"
    PIN = "PIN"
    POUT = "POUT"
    PRAT = "PRAT"
    QACT = "QACT"
    TYPE = "TYPE"
    EFFC = "EFFC"
    EFFS = "EFFS"
    POW = "POW"
    FHAD = "FHAD"
    HQACT = "HQACT"
    CURRPM = "CURRPM"
    CURDIA = "CURDIA"
    CURNP = "CURNP"
    CURQ = "CURQ"
    CURH = "CURH"
    CUREFF = "CUREFF"
    NOTES = "NOTES"

    ALL = (
        NUM,
        NAME,
        XY,
        ROT,
        FLIP,
        LBL,
        COLOR,
        CON,
        ELEV,
        DP,
        PIN,
        POUT,
        PRAT,
        QACT,
        TYPE,
        EFFC,
        EFFS,
        POW,
        FHAD,
        HQACT,
        CURRPM,
        CURDIA,
        CURNP,
        CURQ,
        CURH,
        CUREFF,
        NOTES,
    )


class Misc:
    NUM = "NUM"
    NAME = "NAME"
    XY = "XY"
    ROT = "ROT"
    FLIP = "FLIP"
    LBL = "LBL"
    COLOR = "COLOR"
    NOZI = "NOZI"
    NOZO = "NOZO"
    DP = "DP"
    PIN = "PIN"
    POUT = "POUT"
    PRAT = "PRAT"
    K = "K"
    LD = "LD"
    DPELEV = "DPELEV"
    VOLBAL = "VOLBAL"
    MASBAL = "MASBAL"
    NOTES = "NOTES"

    ALL = (
        NUM,
        NAME,
        XY,
        ROT,
        FLIP,
        LBL,
        COLOR,
        NOZI,
        NOZO,
        DP,
        PIN,
        POUT,
        PRAT,
        K,
        LD,
        DPELEV,
        VOLBAL,
        MASBAL,
        NOTES,
    )


class Expand:
    NUM = "NUM"
    NAME = "NAME"
    XY = "XY"
    ROT = "ROT"
    FLIP = "FLIP"
    LBL = "LBL"
    COLOR = "COLOR"
    TYPE = "TYPE"
    CON = "CON"
    ELEV = "ELEV"
    DP = "DP"
    PIN = "PIN"
    POUT = "POUT"
    DPP = "DPP"
    CHOKE = "CHOKE"
    K = "K"
    ANGLE = "ANGLE"

    ALL = (
        NUM,
        NAME,
        XY,
        ROT,
        FLIP,
        LBL,
        COLOR,
        TYPE,
        CON,
        ELEV,
        DP,
        PIN,
        POUT,
        DPP,
        CHOKE,
        K,
        ANGLE,
    )


class Junc:
    NUM = "NUM"
    NAME = "NAME"
    XY = "XY"
    ROT = "ROT"
    FLIP = "FLIP"
    LBL = "LBL"
    COLOR = "COLOR"
    PRES = "PRES"
    NOZI = "NOZI"
    NOZO = "NOZO"

    ALL = (NUM, NAME, XY, ROT, FLIP, LBL, COLOR, PRES, NOZI, NOZO)


class Tee:
    NUM = "NUM"
    NAME = "NAME"
    XY = "XY"
    ROT = "ROT"
    FLIP = "FLIP"
    LBL = "LBL"
    COLOR = "COLOR"
    TYPE = "TYPE"
    CON = "CON"
    ELEV = "ELEV"
    PRES = "PRES"
    DPP = "DPP"
    KCM = "KCM"
    KCB = "KCB"
    SPAC = "SPAC"
    C = "C"
    M = "M"
    B = "B"
    NOTES = "NOTES"

    ALL = (
        NUM,
        NAME,
        XY,
        ROT,
        FLIP,
        LBL,
        COLOR,
        TYPE,
        CON,
        ELEV,
        PRES,
        DPP,
        KCM,
        KCB,
        SPAC,
        C,
        M,
        B,
        NOTES,
    )


class Vessel:
    NUM = "NUM"
    NAME = "NAME"
    XY = "XY"
    ROT = "ROT"
    FLIP = "FLIP"
    LBL = "LBL"
    COLOR = "COLOR"
    TYPE = "TYPE"
    PRES = "PRES"
    WSPEC = "WSPEC"
    VF = "VF"
    LLF = "LLF"
    HLF = "HLF"
    ELEV = "ELEV"
    LEVELL = "LEVELL"
    LEVELM = "LEVELM"
    LEVELH = "LEVELH"
    NOZN = "NOZN"
    NOZLI = "NOZLI"
    NOZLO = "NOZLO"
    NOTES = "NOTES"

    ALL = (
        NUM,
        NAME,
        XY,
        ROT,
        FLIP,
        LBL,
        COLOR,
        TYPE,
        PRES,
        WSPEC,
        VF,
        LLF,
        HLF,
        ELEV,
        LEVELL,
        LEVELM,
        LEVELH,
        NOZN,
        NOZLI,
        NOZLO,
        NOTES,
    )


class Symbol:
    NUM = "NUM"
    TYPE = "TYPE"
    XY = "XY"
    TEXT = "TEXT"
    COLOR = "COLOR"
    STYLL = "STYLL"
    STYLA = "STYLA"
    ANGL = "ANGL"
    FSIZ = "FSIZ"

    ALL = (NUM, TYPE, XY, TEXT, COLOR, STYLL, STYLA, ANGL, FSIZ)


class Tools:
    PIPEI = "PIPEI"
    PIPEOA = "PIPEOA"
    PIPEOB = "PIPEOB"
    VALVEI = "VALVEI"
    VALVEO = "VALVEO"
    FOI = "FOI"
    FOO = "FOO"

    ALL = (PIPEI, PIPEOA, PIPEOB, VALVEI, VALVEO, FOI, FOO)


class Pseudo:
    NUM = "NUM"
    NAME = "NAME"
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
        NUM,
        NAME,
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


class PipeData:
    NUM = "NUM"
    MAT = "MAT"
    NOTES = "NOTES"
    PROP = "PROP"
    E = "E"
    NSS = "NSS"
    IDIA = "IDIA"
    SDIA = "SDIA"
    UNITS = "UNITS"
    SCH = "SCH"
    DIA = "DIA"

    ALL = (NUM, MAT, NOTES, PROP, E, NSS, IDIA, SDIA, UNITS, SCH, DIA)


PROPERTIES_BY_ELEMENT = {
    Element.GEN: Gen.ALL,
    Element.PIPE: Pipe.ALL,
    Element.FEED: Feed.ALL,
    Element.PROD: Prod.ALL,
    Element.VALVE: Valve.ALL,
    Element.CHECK: Check.ALL,
    Element.ORIFICE: Orifice.ALL,
    Element.HX: Hx.ALL,
    Element.PUMP: Pump.ALL,
    Element.COMP: Comp.ALL,
    Element.MISC: Misc.ALL,
    Element.EXPAND: Expand.ALL,
    Element.JUNC: Junc.ALL,
    Element.TEE: Tee.ALL,
    Element.VESSEL: Vessel.ALL,
    Element.SYMBOL: Symbol.ALL,
    Element.TOOLS: Tools.ALL,
    Element.PSEUDO: Pseudo.ALL,
    Element.PIPEDATA: PipeData.ALL,
}


__all__ = [
    "Element",
    "Gen",
    "Pipe",
    "Feed",
    "Prod",
    "Valve",
    "Check",
    "Orifice",
    "Hx",
    "Pump",
    "Comp",
    "Misc",
    "Expand",
    "Junc",
    "Tee",
    "Vessel",
    "Symbol",
    "Tools",
    "Pseudo",
    "PipeData",
    "PROPERTIES_BY_ELEMENT",
]
