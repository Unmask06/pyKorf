"""Project-specific workflows for piping data automation.

This module provides high-level utilities for batch processing KDF files
using project-specific data sources like PMS, HMB, and Global Settings.

Main Classes:
    PipedataProcessor: Main processor for batch processing KDF files

Submodules:
    exceptions: Custom exceptions for use case operations
    line_number: Line number parsing and validation
    pms: PMS (Piping Material Specification) reader and parameter builder
    hmb: HMB (Heat and Material Balance) reader and parameter builder
    settings: Global settings reader
    processor: Main processor implementation

Usage:
    >>> from pykorf.use_case import PipedataProcessor
    >>>
    >>> processor = PipedataProcessor()
    >>> processor.load_pms("pms.json")
    >>> processor.load_hmb("hmb.json")
    >>> result = processor.process_kdf("model.kdf")
    >>> print(f"Processed {result.pipes_processed} pipes")

Simplified API (functions):
    >>> from pykorf import Model
    >>> from pykorf.use_case.pms import apply_pms
    >>> from pykorf.use_case.hmb import apply_hmb
    >>>
    >>> model = Model("model.kdf")
    >>> pms_pipes = apply_pms("Consolidated PMS.json", model)
    >>> print(f"Updated {len(pms_pipes)} pipes with PMS specs")
    >>>
    >>> hmb_pipes = apply_hmb("Stream Data.json", model)
    >>> print(f"Updated {len(hmb_pipes)} pipes with fluid properties")
    >>>
    >>> # Model is automatically saved by default
"""

from pykorf.use_case.bulk_calc import copy_fluids
from pykorf.use_case.exceptions import (
    ExcelConversionError,
    LineNumberParseError,
    PmsLookupError,
    ProcessError,
    StreamNotFoundError,
    UseCaseError,
    ValidationError,
)
from pykorf.use_case.global_settings import (
    apply_global_settings,
    get_global_setting,
    get_global_settings,
    set_pipe_criteria,
)
from pykorf.use_case.hmb import (
    FluidProperties,
    HmbReader,
    apply_hmb,
    convert_hmb_excel,
    load_hmb,
    lookup_stream,
)
from pykorf.use_case.line_number import (
    LineNumber,
    ValidationResult,
    parse_stream_from_notes,
)
from pykorf.use_case.pms import (
    apply_pms,
    convert_pms_excel,
    load_pms,
    lookup_schedule,
)
from pykorf.use_case.processor import PipedataProcessor, PipeUpdateResult, ProcessResult
from pykorf.use_case.settings import SettingsReader, UseCaseSettings
from pykorf.use_case.tui import run_tui

__all__ = [
    "ExcelConversionError",
    "FluidProperties",
    "HmbReader",
    "LineNumber",
    "LineNumberParseError",
    "PipeUpdateResult",
    "PipedataProcessor",
    "PmsLookupError",
    "ProcessError",
    "ProcessResult",
    "SettingsReader",
    "StreamNotFoundError",
    "UseCaseError",
    "UseCaseSettings",
    "ValidationError",
    "ValidationResult",
    "apply_global_settings",
    "apply_hmb",
    "apply_pms",
    "convert_hmb_excel",
    "convert_pms_excel",
    "copy_fluids",
    "get_global_setting",
    "get_global_settings",
    "load_hmb",
    "load_pms",
    "lookup_schedule",
    "lookup_stream",
    "parse_stream_from_notes",
    "run_tui",
    "set_pipe_criteria",
]
