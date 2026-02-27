"""Centralized KDF element and property definitions.

This package provides string constants for element types and their valid
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

from .check import Check
from .comp import Comp
from .element import Element
from .expand import Expand
from .feed import Feed
from .gen import Gen
from .hx import Hx
from .junc import Junc
from .misc import Misc
from .orifice import Orifice
from .pipe import Pipe
from .pipedata import PipeData
from .prod import Prod
from .pseudo import Pseudo
from .pump import Pump
from .symbol import Symbol
from .tee import Tee
from .tools import Tools
from .valve import Valve
from .vessel import Vessel

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
