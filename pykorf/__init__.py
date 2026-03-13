"""pyKorf - Enterprise Python toolkit for reading, editing and writing KORF hydraulic model files (.kdf).

This package provides comprehensive support for working with KORF hydraulic simulation
models, including loading, editing, validation, visualization, and export capabilities.

Quickstart
----------
>>> from pykorf import Model
>>> model = Model("Pumpcases.kdf")
>>> model.update_element("L1", {"LEN": 200})
>>> model.save("Pumpcases_new.kdf")

Modules
-------
model          - Model : top-level container for a .kdf file
parser         - KdfParser : low-level tokeniser / serialiser
cases          - CaseSet : multi-case helpers
results        - Results : extract calculated output values
automation     - KorfApp : pywinauto wrapper (requires KORF to be open)
exceptions     - Package-wide exception types
utils          - Shared CSV / value helpers
elements/      - One module per KORF element type
connectivity   - Connection management
layout         - Element positioning
validation     - KDF format compliance
visualization/ - PyVis network visualization
export         - Export to JSON, YAML, Excel, CSV
types          - Pydantic models for type safety
config         - Configuration management
log            - Structured logging

Example Usage
-------------
### Loading and Inspecting

    >>> from pykorf import Model
    >>> model = Model("model.kdf")
    >>> print(model.summary())
    {
        'file': 'model.kdf',
        'version': 'KORF_3.6',
        'cases': ['NORMAL', 'RATED', 'MINIMUM'],
        'num_pipes': 10,
        'num_pumps': 2,
        ...
    }

### Using Type-Safe Models

    >>> from pykorf.types import PipeData, FlowParameters
    >>> pipe = PipeData(
    ...     name="L1",
    ...     diameter_inch="6",
    ...     length_m=100.0,
    ...     flow=FlowParameters(mass_flow_t_h=[50, 55, 20]),
    ... )

### Exporting

    >>> model.to_excel("model.xlsx")
    >>> model.io.export_to_json("model.json")

### Querying

    >>> # Use Model.get_elements() for filtering
    >>> pipes = model.get_elements(etype="PIPE")
    >>> p_elements = model.get_elements(name="P*")

### Logging

    >>> from pykorf.log import get_logger, log_operation
    >>> logger = get_logger()
    >>> with log_operation("process_model", model="test.kdf"):
    ...     model = Model("test.kdf")
    ...     model.validate()
"""

from pathlib import Path

from pykorf.cases import CaseSet
from pykorf.elements import Element
from pykorf.exceptions import (
    AutomationError,
    CaseError,
    ConnectivityError,
    ElementAlreadyExists,
    ElementNotFound,
    ErrorContext,
    ExportError,
    ImportError,
    KorfError,
    LayoutError,
    ParameterError,
    ParseError,
    ValidationError,
    VersionError,
)
from pykorf.fluid import Fluid
from pykorf.model import KorfModel, Model
from pykorf.results import Results
from pykorf.types import (
    CaseInfo,
    CompressorData,
    ElementBase,
    ElementType,
    ExportOptions,
    FeedData,
    FlowParameters,
    FluidProperties,
    HeatExchangerData,
    KdfBaseModel,
    KdfVersion,
    ModelMetadata,
    PipeData,
    Position,
    ProductData,
    PumpData,
    PumpType,
    UnitConfiguration,
    UnitSystem,
    ValidationIssue,
    ValveData,
    VesselData,
    VesselOrientation,
)

# Version information - read from pyproject.toml as fallback
__version__ = "0.1.2"
try:
    from pykorf._version import __version__ as _scm_version

    # Use setuptools-scm version only if it's a clean release (no dev/git info)
    if "dev" not in _scm_version and "+" not in _scm_version:
        __version__ = _scm_version
except Exception:
    pass

# Try importlib.metadata if still on fallback
if __version__ == "0.1.1":
    try:
        from importlib.metadata import version

        _meta_version = version("pykorf")
        if "dev" not in _meta_version and "+" not in _meta_version:
            __version__ = _meta_version
    except Exception:
        pass

# Final fallback: read from pyproject.toml for development
if __version__ == "0.1.1":
    try:
        import tomllib

        _pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        if _pyproject_path.exists():
            with open(_pyproject_path, "rb") as f:
                _data = tomllib.load(f)
                __version__ = _data["project"]["version"]
    except Exception:
        pass

__author__ = "pyKorf Contributors"
__all__ = [
    # Exceptions
    "AutomationError",
    "CaseError",
    # Types
    "CaseInfo",
    # Core classes
    "CaseSet",
    "CompressorData",
    "ConnectivityError",
    # Constants
    "Element",
    "ElementAlreadyExists",
    "ElementBase",
    "ElementNotFound",
    "ElementType",
    "ErrorContext",
    "ExportError",
    "ExportOptions",
    "FeedData",
    "FlowParameters",
    # Fluid
    "Fluid",
    "FluidProperties",
    "HeatExchangerData",
    "ImportError",
    "KdfBaseModel",
    "KdfVersion",
    "KorfError",
    "KorfModel",
    "LayoutError",
    "Model",
    "ModelMetadata",
    "ParameterError",
    "ParseError",
    "PipeData",
    "Position",
    "ProductData",
    "PumpData",
    "PumpType",
    "Results",
    "UnitConfiguration",
    "UnitSystem",
    "ValidationError",
    "ValidationIssue",
    "ValveData",
    "VersionError",
    "VesselData",
    "VesselOrientation",
    # Version
    "__author__",
    "__version__",
]


def open_ui(*args, **kwargs):
    """Open a file in the running KORF instance.

    Lazy import to avoid requiring pywinauto at import time.
    See :func:`pykorf.automation.open_ui` for full documentation.
    """
    from pykorf.automation import open_ui as _open_ui

    return _open_ui(*args, **kwargs)


# Add open_ui to __all__
__all__.append("open_ui")
