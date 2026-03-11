"""Element sub-package.

Exports every concrete element class plus the base :class:`BaseElement`,
the ``ELEMENT_REGISTRY`` mapping, and the ``PROPERTIES_BY_ELEMENT`` dict
(previously in ``pykorf.definitions``).

Backward-compatibility aliases for the old short definition class names
(``Gen``, ``Hx``, ``Comp``, etc.) are also provided so that existing code
using ``from pykorf.elements import Gen`` continues to work.
"""

from pykorf.elements.base import BaseElement
from pykorf.elements.check import CheckValve
from pykorf.elements.compressor import Compressor
from pykorf.elements.expand import Expander
from pykorf.elements.feed import Feed
from pykorf.elements.gen import General
from pykorf.elements.hx import HeatExchanger
from pykorf.elements.junction import Junction
from pykorf.elements.misc import MiscEquipment
from pykorf.elements.orifice import FlowOrifice
from pykorf.elements.pipe import Pipe
from pykorf.elements.pipedata import PipeData
from pykorf.elements.prod import Product
from pykorf.elements.pseudo import Pseudo
from pykorf.elements.pump import Pump
from pykorf.elements.symbol import Symbol
from pykorf.elements.tee import Tee
from pykorf.elements.tools import Tools
from pykorf.elements.valve import Valve
from pykorf.elements.vessel import Vessel

# ------------------------------------------------------------------
# Backward-compat aliases (old short names from definitions/)
# ------------------------------------------------------------------
Gen = General
Hx = HeatExchanger
Comp = Compressor
Misc = MiscEquipment
Expand = Expander
Junc = Junction
Prod = Product
Check = CheckValve
Orifice = FlowOrifice
# Common is now BaseElement
Common = BaseElement

# ------------------------------------------------------------------
# Element type-token class (formerly definitions/element.py)
# ------------------------------------------------------------------


class Element:
    """KDF element type tokens.

    Prefer using ``<ElementClass>.ETYPE`` (e.g. ``Pipe.ETYPE``) instead.
    This class is retained for backward compatibility.
    """

    GEN = General.ETYPE
    PIPE = Pipe.ETYPE
    FEED = Feed.ETYPE
    PROD = Product.ETYPE
    VALVE = Valve.ETYPE
    CHECK = CheckValve.ETYPE
    ORIFICE = FlowOrifice.ETYPE
    HX = HeatExchanger.ETYPE
    PUMP = Pump.ETYPE
    COMP = Compressor.ETYPE
    MISC = MiscEquipment.ETYPE
    EXPAND = Expander.ETYPE
    JUNC = Junction.ETYPE
    TEE = Tee.ETYPE
    VESSEL = Vessel.ETYPE
    SYMBOL = Symbol.ETYPE
    TOOLS = Tools.ETYPE
    PSEUDO = Pseudo.ETYPE
    PIPEDATA = PipeData.ETYPE

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


# ------------------------------------------------------------------
# Registry mapping KDF element-type keyword → class
# ------------------------------------------------------------------
ELEMENT_REGISTRY: dict[str, type[BaseElement]] = {
    General.ETYPE: General,
    Pipe.ETYPE: Pipe,
    Feed.ETYPE: Feed,
    Product.ETYPE: Product,
    Pump.ETYPE: Pump,
    Valve.ETYPE: Valve,
    CheckValve.ETYPE: CheckValve,
    FlowOrifice.ETYPE: FlowOrifice,
    HeatExchanger.ETYPE: HeatExchanger,
    Compressor.ETYPE: Compressor,
    MiscEquipment.ETYPE: MiscEquipment,
    Expander.ETYPE: Expander,
    Junction.ETYPE: Junction,
    Tee.ETYPE: Tee,
    Vessel.ETYPE: Vessel,
    Symbol.ETYPE: Symbol,
    Tools.ETYPE: Tools,
    Pseudo.ETYPE: Pseudo,
    PipeData.ETYPE: PipeData,
}

# ------------------------------------------------------------------
# Properties-by-element mapping (previously in definitions/__init__)
# ------------------------------------------------------------------
PROPERTIES_BY_ELEMENT: dict[str, tuple[str, ...]] = {
    General.ETYPE: General.ALL,
    Pipe.ETYPE: Pipe.ALL,
    Feed.ETYPE: Feed.ALL,
    Product.ETYPE: Product.ALL,
    Valve.ETYPE: Valve.ALL,
    CheckValve.ETYPE: CheckValve.ALL,
    FlowOrifice.ETYPE: FlowOrifice.ALL,
    HeatExchanger.ETYPE: HeatExchanger.ALL,
    Pump.ETYPE: Pump.ALL,
    Compressor.ETYPE: Compressor.ALL,
    MiscEquipment.ETYPE: MiscEquipment.ALL,
    Expander.ETYPE: Expander.ALL,
    Junction.ETYPE: Junction.ALL,
    Tee.ETYPE: Tee.ALL,
    Vessel.ETYPE: Vessel.ALL,
    Symbol.ETYPE: Symbol.ALL,
    Tools.ETYPE: Tools.ALL,
    Pseudo.ETYPE: Pseudo.ALL,
    PipeData.ETYPE: PipeData.ALL,
}

__all__ = [
    "BaseElement",
    "CheckValve",
    "Compressor",
    "Expander",
    "Feed",
    "FlowOrifice",
    "General",
    "HeatExchanger",
    "Junction",
    "MiscEquipment",
    "Pipe",
    "PipeData",
    "Product",
    "Pseudo",
    "Pump",
    "Symbol",
    "Tee",
    "Tools",
    "Valve",
    "Vessel",
    # Backward-compat aliases
    "Check",
    "Common",
    "Comp",
    "Element",
    "Expand",
    "Gen",
    "Hx",
    "Junc",
    "Misc",
    "Orifice",
    "Prod",
    # Registries
    "ELEMENT_REGISTRY",
    "PROPERTIES_BY_ELEMENT",
]
