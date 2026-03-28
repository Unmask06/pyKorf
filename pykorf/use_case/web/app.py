"""Flask application factory for the pyKorf local web UI.

Single-user, local-only server.  Model state is held in a module-level
global (see :mod:`pykorf.use_case.web.session`), matching the terminal TUI
approach.  No cookies, no auth — it's just localhost.

Launch with::

    uv run pykorf --web [--port 8000]
"""

from __future__ import annotations

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
from pykorf.use_case.web.routes.references import bp as references_bp
from pykorf.use_case.web.routes.report import bp as report_bp
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
    app.register_blueprint(references_bp)
    app.register_blueprint(browse_bp)
    app.register_blueprint(preferences_bp)
    app.register_blueprint(bulk_copy_bp)

    from pathlib import Path as _Path

    app.jinja_env.filters["split"] = lambda s, sep: s.split(sep)
    app.jinja_env.filters["basename"] = lambda s: _Path(s).name if s else ""
    app.jinja_env.filters["dirname"] = lambda s: str(_Path(s).parent) if s else ""
    app.jinja_env.filters["ternary"] = lambda c, t, f: t if c else f

    return app


def run_server(port: int = 8000) -> None:
    """Start the Flask development server and open the browser.

    Args:
        port: TCP port to listen on (default 8000).
    """
    import os

    app = create_app()
    url = f"http://localhost:{port}"
    print(f"\n  pyKorf Web UI → {url}\n  Press Ctrl+C to stop.\n")

    # Only open the browser from the parent process; the reloader child sets
    # WERKZEUG_RUN_MAIN=true, so this guard prevents a double-open on reload.
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Timer(0.8, webbrowser.open, args=[url]).start()

    app.run(host="127.0.0.1", port=port, debug=True, use_reloader=True)
