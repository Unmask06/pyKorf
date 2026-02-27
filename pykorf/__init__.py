"""pyKorf – Python toolkit for reading, editing and writing KORF hydraulic model files (.kdf).

Quickstart
----------
>>> from pykorf import Model
>>> model = Model("Pumpcases.kdf")
>>> model.update_element('L1', {'LEN': 200})
>>> model.save("Pumpcases_new.kdf")

Modules
-------
model        – Model       : top-level container for a .kdf file
parser       – KdfParser   : low-level tokeniser / serialiser
cases        – CaseSet     : multi-case helpers
results      – Results     : extract calculated output values
automation   – KorfApp     : pywinauto wrapper (requires KORF to be open)
exceptions   – package-wide exception types
utils        – shared CSV / value helpers
elements/    – one module per KORF element type
connectivity – connection management
layout       – element positioning
validation   – KDF format compliance
visualization/ – PyVis network visualization (requires pyvis, pydantic)
"""

__version__ = "0.2.0"
__author__ = "pyKorf contributors"

from pykorf.cases import CaseSet
from pykorf.definitions import Element
from pykorf.exceptions import (
    AutomationError,
    CaseError,
    ConnectivityError,
    ElementNotFound,
    KorfError,
    LayoutError,
    ParseError,
    ValidationError,
)
from pykorf.model import KorfModel, Model
from pykorf.results import Results
from pykorf.visualization import Visualizer

__all__ = [
    "Model",
    "KorfModel",
    "CaseSet",
    "Results",
    "Visualizer",
    "KorfError",
    "ParseError",
    "ElementNotFound",
    "CaseError",
    "AutomationError",
    "ValidationError",
    "ConnectivityError",
    "LayoutError",
    "Element",
    "open_ui",
]


def open_ui(*args, **kwargs):
    """Open a file in the running KORF instance.

    Lazy import to avoid requiring pywinauto at import time.
    See :func:`pykorf.automation.open_ui` for full documentation.
    """
    from pykorf.automation import open_ui as _open_ui

    return _open_ui(*args, **kwargs)
