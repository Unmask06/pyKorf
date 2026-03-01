"""
KDF element and property definitions.

This subpackage provides string constants for element types and their valid
parameter keys, derived from ``library/New.kdf``.

Examples:
    >>> from pykorf.definitions import Element, Pipe
    >>> Element.PIPE
    'PIPE'
    >>> Pipe.PRES
    'PRES'
    >>> Pipe.ALL  # Tuple of all pipe parameters
"""

from pykorf.definitions.check import Check
from pykorf.definitions.common import Common
from pykorf.definitions.comp import Comp
from pykorf.definitions.element import Element
from pykorf.definitions.expand import Expand
from pykorf.definitions.feed import Feed
from pykorf.definitions.gen import Gen
from pykorf.definitions.hx import Hx
from pykorf.definitions.junc import Junc
from pykorf.definitions.misc import Misc
from pykorf.definitions.orifice import Orifice
from pykorf.definitions.pipe import Pipe
from pykorf.definitions.pipedata import PipeData
from pykorf.definitions.prod import Prod
from pykorf.definitions.pump import Pump
from pykorf.definitions.pseudo import Pseudo
from pykorf.definitions.symbol import Symbol
from pykorf.definitions.tee import Tee
from pykorf.definitions.tools import Tools
from pykorf.definitions.valve import Valve
from pykorf.definitions.vessel import Vessel

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
    "Common",
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
