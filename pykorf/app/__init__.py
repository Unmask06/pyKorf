"""pyKorf Web UI and project-specific workflows.

This module provides:
1. FastAPI web application for local KDF model editing
2. High-level utilities for batch processing KDF files using PMS, HMB, and Global Settings

Web UI
------
Launch with::

    uv run pykorf --web [--port 8000]

Pipedata Processor
------------------
    >>> from pykorf.app import PipedataProcessor
    >>>
    >>> processor = PipedataProcessor()
    >>> processor.load_pms("pms.json")
    >>> processor.load_hmb("hmb.json")
    >>> result = processor.process_kdf("model.kdf")
    >>> print(f"Processed {result.pipes_processed} pipes")

Simplified API (functions):
    >>> from pykorf import Model
    >>> from pykorf.app.operation.data_import.pms import apply_pms
    >>> from pykorf.app.operation.data_import.hmb import apply_hmb
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

from __future__ import annotations

import logging
import sys
import threading
import webbrowser
from pathlib import Path

from pykorf.app.operation.processor.batch_report import BatchReportGenerator
from pykorf.app.operation.processor.bulk_copy import copy_fluids
from pykorf.app.exceptions import (
    ExcelConversionError,
    LineNumberParseError,
    PmsLookupError,
    ProcessError,
    StreamNotFoundError,
    UseCaseError,
    ValidationError,
)
from pykorf.app.operation.config.global_parameters import (
    apply_global_settings,
    get_global_setting,
    get_global_settings,
)
from pykorf.app.operation.data_import.hmb import (
    FluidProperties,
    HmbReader,
    apply_hmb,
    convert_hmb_excel,
    load_hmb,
    lookup_stream,
)
from pykorf.app.operation.data_import.line_number import (
    LineNumber,
    ValidationResult,
    parse_stream_from_notes,
)
from pykorf.app.operation.data_import.pms import (
    apply_pms,
    convert_pms_excel,
    load_pms,
    lookup_schedule,
)
from pykorf.app.operation.processor.processor import (
    PipedataProcessor,
    PipeUpdateResult,
    ProcessResult,
)
from pykorf.app.operation.config.settings import SettingsReader, UseCaseSettings


def _setup_console_logging(debug: bool = True) -> None:
    """Add a stderr StreamHandler to the pykorf logger if none exists yet.

    Args:
        debug: When True, log at DEBUG level; otherwise WARNING to reduce noise.
    """
    from pykorf.core.log import set_log_level

    level = "DEBUG" if debug else "WARNING"
    set_log_level(level)

    pykorf_logger = logging.getLogger("pykorf")
    if not any(isinstance(h, logging.StreamHandler) for h in pykorf_logger.handlers):
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.DEBUG if debug else logging.WARNING)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        pykorf_logger.addHandler(handler)
    pykorf_logger.propagate = False  # don't double-print via root


def run_server(port: int = 8000, debug: bool = True) -> None:
    """Start the web server and open the browser.

    Launches the FastAPI + Vue application via uvicorn.

    Args:
        port: TCP port to listen on (default 8000).
        debug: When True (developer mode), enable auto-reload and DEBUG level.
    """
    from pykorf.app.api.app import run_server as _run_fastapi

    _run_fastapi(port=port, debug=debug)


__all__ = [
    # Operation classes
    "BatchReportGenerator",
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
    # Operation functions
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
    # Web app functions
    "run_server",
]
