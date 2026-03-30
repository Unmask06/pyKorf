"""Flask application factory for the pyKorf local web UI.

Single-user, local-only server.  Model state is held in a module-level
global (see :mod:`pykorf.use_case.web.session`), matching the terminal TUI
approach.  No cookies, no auth — it's just localhost.

Launch with::

    uv run pykorf --web [--port 8000]
"""

from __future__ import annotations

import logging
import sys
import threading
import webbrowser
from pathlib import Path

from flask import Flask

from pykorf.use_case.web.routes.browse import bp as browse_bp
from pykorf.use_case.web.routes.bulk_copy import bp as bulk_copy_bp
from pykorf.use_case.web.routes.preferences import bp as preferences_bp
from pykorf.use_case.web.routes.data import bp as data_bp
from pykorf.use_case.web.routes.file_picker import bp as file_picker_bp
from pykorf.use_case.web.routes.model_core import bp as model_core_bp
from pykorf.use_case.web.routes.model_info import bp as model_info_bp
from pykorf.use_case.web.routes.pipe_criteria import bp as pipe_criteria_bp
from pykorf.use_case.web.routes.references import bp as references_bp
from pykorf.use_case.web.routes.report import bp as report_bp
from pykorf.use_case.web.routes.about import bp as about_bp
from pykorf.use_case.web.routes.settings import bp as settings_bp

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_STATIC_DIR = Path(__file__).parent / "static"


def create_app() -> Flask:
    """Create and configure the Flask application.

    Returns:
        Configured Flask app with all Blueprints registered.
    """
    app = Flask(
        __name__,
        template_folder=str(_TEMPLATES_DIR),
        static_folder=str(_STATIC_DIR),
    )

    app.register_blueprint(file_picker_bp)
    app.register_blueprint(model_core_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(model_info_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(pipe_criteria_bp)
    app.register_blueprint(references_bp)
    app.register_blueprint(browse_bp)
    app.register_blueprint(preferences_bp)
    app.register_blueprint(bulk_copy_bp)
    app.register_blueprint(about_bp)

    from pathlib import Path as _Path

    app.jinja_env.filters["split"] = lambda s, sep: s.split(sep)
    app.jinja_env.filters["basename"] = lambda s: _Path(s).name if s else ""
    app.jinja_env.filters["dirname"] = lambda s: str(_Path(s).parent) if s else ""
    app.jinja_env.filters["ternary"] = lambda c, t, f: t if c else f

    @app.after_request
    def add_no_cache(response):
        """Prevent browser caching of HTML pages so the UI always reflects current server state."""
        if "text/html" in response.content_type:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
        return response

    @app.context_processor
    def inject_kdf_mtime():
        """Inject kdf_mtime_str into every template context."""
        import os
        from datetime import datetime
        from pykorf.use_case.web import session as _sess

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
    print(f"\n  pyKorf Web UI → {url}\n  Press Ctrl+C to stop.\n")

    # Only open the browser from the parent process; the reloader child sets
    # WERKZEUG_RUN_MAIN=true, so this guard prevents a double-open on reload.
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Timer(0.8, webbrowser.open, args=[url]).start()

    app.run(host="127.0.0.1", port=port, debug=True, use_reloader=True)
