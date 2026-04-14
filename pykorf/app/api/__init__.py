"""FastAPI web application for pyKorf.

Replaces the Flask web UI with a FastAPI backend serving a Vue SPA.
"""

from __future__ import annotations

from pykorf.app.api.app import create_app, run_server

__all__ = ["create_app", "run_server"]
