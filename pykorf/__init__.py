"""pyKorf – Python toolkit for reading, editing and writing KORF hydraulic model files (.kdf).

Quickstart
----------
>>> from pykorf import KorfModel
>>> model = KorfModel.load("Pumpcases.kdf")
>>> model.pipes[1].set_flow("60;65;25")
>>> model.save("Pumpcases_new.kdf")

Modules
-------
model        – KorfModel  : top-level container for a .kdf file
parser       – KdfParser  : low-level tokeniser / serialiser
cases        – CaseSet    : multi-case helpers
results      – Results    : extract calculated output values
automation   – KorfApp    : pywinauto wrapper (requires KORF to be open)
exceptions   – package-wide exception types
utils        – shared CSV / value helpers
elements/    – one module per KORF element type
"""

__version__ = "0.1.0"
__author__ = "pyKorf contributors"

from pykorf.cases import CaseSet
from pykorf.exceptions import ElementNotFound, KorfError, ParseError
from pykorf.model import KorfModel
from pykorf.results import Results

__all__ = [
    "KorfModel",
    "CaseSet",
    "Results",
    "KorfError",
    "ParseError",
    "ElementNotFound",
]
