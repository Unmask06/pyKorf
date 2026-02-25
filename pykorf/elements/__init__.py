"""
Element sub-package.
Exports every concrete element class plus the base :class:`BaseElement`.
"""

from pykorf.elements.base import BaseElement
from pykorf.elements.gen import General
from pykorf.elements.pipe import Pipe
from pykorf.elements.feed import Feed
from pykorf.elements.prod import Product
from pykorf.elements.pump import Pump
from pykorf.elements.valve import Valve
from pykorf.elements.check import CheckValve
from pykorf.elements.orifice import FlowOrifice
from pykorf.elements.hx import HeatExchanger
from pykorf.elements.compressor import Compressor
from pykorf.elements.misc import MiscEquipment
from pykorf.elements.expand import Expander
from pykorf.elements.junction import Junction
from pykorf.elements.tee import Tee
from pykorf.elements.vessel import Vessel

__all__ = [
    "BaseElement",
    "General",
    "Pipe",
    "Feed",
    "Product",
    "Pump",
    "Valve",
    "CheckValve",
    "FlowOrifice",
    "HeatExchanger",
    "Compressor",
    "MiscEquipment",
    "Expander",
    "Junction",
    "Tee",
    "Vessel",
]

# ---- Registry mapping KDF element-type keyword → class ----
ELEMENT_REGISTRY: dict[str, type] = {
    "GEN":    General,
    "PIPE":   Pipe,
    "FEED":   Feed,
    "PROD":   Product,
    "PUMP":   Pump,
    "VALVE":  Valve,
    "CHECK":  CheckValve,
    "FO":     FlowOrifice,
    "HX":     HeatExchanger,
    "COMP":   Compressor,
    "MISC":   MiscEquipment,
    "EXPAND": Expander,
    "JUNC":   Junction,
    "TEE":    Tee,
    "VESSEL": Vessel,
}
