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

from pykorf.use_case.exceptions import (
    ExcelConversionError,
    LineNumberParseError,
    PmsLookupError,
    ProcessError,
    StreamNotFoundError,
    UseCaseError,
    ValidationError,
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

__all__ = [
    # Main processor
    "PipedataProcessor",
    "ProcessResult",
    "PipeUpdateResult",
    # PMS functions (simplified API)
    "apply_pms",
    "load_pms",
    "lookup_schedule",
    "convert_pms_excel",
    # HMB functions (simplified API)
    "apply_hmb",
    "load_hmb",
    "lookup_stream",
    "convert_hmb_excel",
    # Classes for advanced use
    "HmbReader",
    "FluidProperties",
    "LineNumber",
    "ValidationResult",
    "parse_stream_from_notes",
    "SettingsReader",
    "UseCaseSettings",
    # Exceptions
    "UseCaseError",
    "LineNumberParseError",
    "StreamNotFoundError",
    "PmsLookupError",
    "ValidationError",
    "ExcelConversionError",
    "ProcessError",
]
