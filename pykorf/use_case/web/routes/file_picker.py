"""File-picker routes: / and /open."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Blueprint, redirect, render_template, request, url_for

from pykorf.use_case.web import session as _sess

import structlog

logger = structlog.get_logger(__name__)
bp = Blueprint("file_picker", __name__)


def _get_filename(path_str: str) -> str:
    """Extract filename from path using Pathlib."""
    if not path_str:
        return ""
    return Path(path_str).name


def _get_username() -> str:
    """Get the current username from environment variables."""
    return os.environ.get("USERNAME") or os.environ.get("USER") or "there"


@bp.route("/", methods=["GET"])
def file_picker_page():
    """Render the KDF file picker page."""
    from pykorf.use_case.config import get_recent_files

    recent: list[str] = get_recent_files() or []
    default_path: str = recent[0] if recent else ""
    return render_template(
        "file_picker.html",
        recent_files=recent,
        default_path=default_path,
        filename=_get_filename(default_path),
        username=_get_username(),
    )


@bp.route("/open", methods=["POST"])
def open_file():
    """Load a KDF file into the global model state."""
    from pykorf import Model
    from pykorf.use_case.config import get_recent_files, record_opened_file

    kdf_path_str = (request.form.get("kdf_path") or "").strip()
    # Strip surrounding double quotes if present
    if kdf_path_str.startswith('"') and kdf_path_str.endswith('"'):
        kdf_path_str = kdf_path_str[1:-1]
    path = Path(kdf_path_str)

    if not path.is_file():
        recent = get_recent_files() or []
        return render_template(
            "file_picker.html",
            recent_files=recent,
            default_path=kdf_path_str,
            filename=_get_filename(kdf_path_str),
            username=_get_username(),
            error=f"File not found: {path}",
        ), 400

    try:
        model = Model(path)
    except Exception as exc:
        recent = get_recent_files() or []
        return render_template(
            "file_picker.html",
            recent_files=recent,
            default_path=kdf_path_str,
            filename=_get_filename(kdf_path_str),
            username=_get_username(),
            error=f"Failed to load model: {exc}",
        ), 400

    record_opened_file(str(path))
    _sess.load(model, path)
    return redirect(url_for("model_core.main_menu"))
