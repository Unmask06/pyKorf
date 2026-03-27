"""File-picker routes: / and /open."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, redirect, render_template, request, url_for

from pykorf.use_case.web import session as _sess

bp = Blueprint("file_picker", __name__)


@bp.route("/", methods=["GET"])
def file_picker_page():
    """Render the KDF file picker page."""
    from pykorf.use_case.config import get_recent_files

    recent: list[str] = get_recent_files() or []
    return render_template("file_picker.html", recent_files=recent)


@bp.route("/open", methods=["POST"])
def open_file():
    """Load a KDF file into the global model state."""
    from pykorf import Model
    from pykorf.use_case.config import get_recent_files, record_opened_file

    kdf_path_str = (request.form.get("kdf_path") or "").strip()
    path = Path(kdf_path_str)

    if not path.is_file():
        return render_template(
            "file_picker.html",
            recent_files=get_recent_files() or [],
            error=f"File not found: {path}",
        ), 400

    try:
        model = Model(path)
    except Exception as exc:
        return render_template(
            "file_picker.html",
            recent_files=get_recent_files() or [],
            error=f"Failed to load model: {exc}",
        ), 400

    record_opened_file(str(path))
    _sess.load(model, path)
    return redirect(url_for("model_core.main_menu"))
