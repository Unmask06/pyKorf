"""pyKorf Web UI and project-specific workflows.

This module provides:
1. Flask web application for local KDF model editing
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

from flask import Flask

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

# Flask app imports
from pykorf.app.routes.browse import bp as browse_bp
from pykorf.app.routes.bulk_copy import bp as bulk_copy_bp
from pykorf.app.routes.preferences import bp as preferences_bp
from pykorf.app.routes.data import bp as data_bp
from pykorf.app.routes.file_picker import bp as file_picker_bp
from pykorf.app.routes.model_core import bp as model_core_bp
from pykorf.app.routes.pipe_criteria import bp as pipe_criteria_bp
from pykorf.app.routes.references import bp as references_bp
from pykorf.app.routes.report import bp as report_bp
from pykorf.app.routes.doc_register import bp as doc_register_bp
from pykorf.app.routes.about import bp as about_bp
from pykorf.app.routes.global_parameters import bp as settings_bp

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_STATIC_DIR = Path(__file__).parent / "static"


def create_app() -> Flask:
    """Create and configure the Flask application.

    Returns:
        Configured Flask app with all Blueprints registered.
    """
    import os

    app = Flask(
        __name__,
        template_folder=str(_TEMPLATES_DIR),
        static_folder=str(_STATIC_DIR),
    )
    app.secret_key = os.urandom(24)

    # Performance timing middleware
    @app.before_request
    def before_request():
        """Record request start time for performance monitoring."""
        from flask import g
        import time

        g.start_time = time.time()

    @app.after_request
    def log_request_duration(response):
        """Log request duration for performance monitoring."""
        from flask import g, request
        from pykorf.core.log import get_logger
        import time

        if hasattr(g, "start_time"):
            elapsed = time.time() - g.start_time
            app_logger = get_logger(__name__)
            app_logger.info(
                "request_timing",
                path=request.path,
                method=request.method,
                status=response.status_code,
                duration_ms=round(elapsed * 1000, 2),
            )
        return response

    app.register_blueprint(file_picker_bp)
    app.register_blueprint(model_core_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(pipe_criteria_bp)
    app.register_blueprint(references_bp)
    app.register_blueprint(browse_bp)
    app.register_blueprint(preferences_bp)
    app.register_blueprint(bulk_copy_bp)
    app.register_blueprint(doc_register_bp)
    app.register_blueprint(about_bp)

    from pathlib import Path as _Path

    from urllib.parse import quote as _quote

    app.jinja_env.filters["split"] = lambda s, sep: s.split(sep)
    app.jinja_env.filters["quote"] = lambda s: _quote(str(s), safe="")
    app.jinja_env.filters["basename"] = lambda s: _Path(s).name if s else ""
    app.jinja_env.filters["dirname"] = lambda s: str(_Path(s).parent) if s else ""
    app.jinja_env.filters["ternary"] = lambda c, t, f: t if c else f

    @app.after_request
    def add_no_cache(response):
        """Prevent browser caching of HTML pages and ensure UTF-8 for JS/CSS."""
        if "text/html" in response.content_type:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
        if "javascript" in response.content_type and "charset" not in response.content_type:
            response.content_type = "text/javascript; charset=utf-8"
        return response

    @app.context_processor
    def inject_kdf_mtime():
        """Inject kdf_mtime_str into every template context."""
        import os
        from datetime import datetime
        from pykorf.app.web import session as _sess

        kdf_path = _sess.get_kdf_path()
        kdf_mtime_str = ""
        if kdf_path:
            try:
                mtime = os.path.getmtime(kdf_path)
                kdf_mtime_str = datetime.fromtimestamp(mtime).strftime("%d %b %H:%M")
            except OSError:
                pass
        return {"kdf_mtime_str": kdf_mtime_str}

    return app


def _setup_console_logging() -> None:
    """Add a stderr StreamHandler to the pykorf logger if none exists yet."""
    pykorf_logger = logging.getLogger("pykorf")
    if not any(isinstance(h, logging.StreamHandler) for h in pykorf_logger.handlers):
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        pykorf_logger.addHandler(handler)
    pykorf_logger.setLevel(logging.DEBUG)
    pykorf_logger.propagate = False  # don't double-print via root


def run_server(port: int = 8000) -> None:
    """Start the Flask development server and open the browser.

    Args:
        port: TCP port to listen on (default 8000).
    """
    import os

    _setup_console_logging()
    app = create_app()
    url = f"http://localhost:{port}"
    print(f"\n  pyKorf Web UI -> {url}\n  Press Ctrl+C to stop.\n")

    # Only open the browser from the parent process; the reloader child sets
    # WERKZEUG_RUN_MAIN=true, so this guard prevents a double-open on reload.
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Timer(0.8, webbrowser.open, args=[url]).start()

    app.run(host="127.0.0.1", port=port, debug=True, use_reloader=True)


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
    "create_app",
    "run_server",
]
