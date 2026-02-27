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
