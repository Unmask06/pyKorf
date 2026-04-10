"""File-picker routes: / and /open."""

from __future__ import annotations

import os
import time
from pathlib import Path

from flask import Blueprint, redirect, render_template, request, url_for

from pykorf.core.log import get_logger
from pykorf.app.web import session as _sess

logger = get_logger(__name__)
bp = Blueprint("file_picker", __name__)


def _get_filename(path_str: str) -> str:
    """Extract filename from path using Pathlib."""
    if not path_str:
        return ""
    return Path(path_str).name


def _get_username() -> str:
    """Get the current username from environment variables."""
    return os.environ.get("USERNAME") or os.environ.get("USER") or "there"


def _check_setup() -> tuple[bool, bool, bool]:
    """Check whether mandatory preferences are configured.

    Returns:
        (setup_ok, sp_ok, doc_register_ok) — all True means ready to open a model.
    """
    from pathlib import Path as _Path

    from pykorf.app.operation.config.config import (
        get_doc_register_excel_path,
        get_sp_overrides,
        get_skip_sp_override,
    )

    skip_sp = get_skip_sp_override()

    # Check individual statuses for granular display
    sp_ok = bool(get_sp_overrides()) if not skip_sp else True
    excel_path = get_doc_register_excel_path()
    doc_register_ok = bool(excel_path and _Path(excel_path).is_file())

    # If skip_sp_override is ON, bypass all validation
    if skip_sp:
        setup_ok = True
    else:
        setup_ok = sp_ok and doc_register_ok

    logger.info(
        "setup_check",
        sp_ok=sp_ok,
        doc_register_ok=doc_register_ok,
        setup_ok=setup_ok,
        skip_sp_override=skip_sp,
    )
    return setup_ok, sp_ok, doc_register_ok


@bp.route("/", methods=["GET"])
def file_picker_page():
    """Render the KDF file picker page."""
    from pykorf.app.operation.config.config import get_recent_files, get_skip_sp_override

    recent: list[str] = get_recent_files() or []
    default_path: str = recent[0] if recent else ""
    setup_ok, sp_ok, doc_register_ok = _check_setup()
    skip_sp_override = get_skip_sp_override()
    file_age_mins: float | None = None
    if default_path:
        try:
            mtime = Path(default_path).stat().st_mtime
            file_age_mins = (time.time() - mtime) / 60
        except OSError:
            pass
    return render_template(
        "file_picker.html",
        recent_files=recent,
        default_path=default_path,
        filename=_get_filename(default_path),
        username=_get_username(),
        setup_ok=setup_ok,
        sp_ok=sp_ok,
        doc_register_ok=doc_register_ok,
        skip_sp_override=skip_sp_override,
        file_age_mins=file_age_mins,
    )


@bp.route("/open", methods=["POST"])
def open_file():
    """Load a KDF file into the global model state."""
    from pykorf import Model
    from pykorf.app.operation.config.config import (
        get_recent_files,
        get_skip_sp_override,
        record_opened_file,
    )

    setup_ok, sp_ok, doc_register_ok = _check_setup()
    skip_sp_override = get_skip_sp_override()
    if not setup_ok:
        recent: list[str] = get_recent_files() or []
        default_path = (request.form.get("kdf_path") or "").strip()
        return render_template(
            "file_picker.html",
            recent_files=recent,
            default_path=default_path,
            filename=_get_filename(default_path),
            username=_get_username(),
            setup_ok=False,
            sp_ok=sp_ok,
            doc_register_ok=doc_register_ok,
            skip_sp_override=skip_sp_override,
            error="Complete the required setup in Preferences before opening a model.",
        ), 403

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
            setup_ok=setup_ok,
            sp_ok=sp_ok,
            doc_register_ok=doc_register_ok,
            skip_sp_override=skip_sp_override,
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
            setup_ok=setup_ok,
            sp_ok=sp_ok,
            doc_register_ok=doc_register_ok,
            skip_sp_override=skip_sp_override,
            error=f"Failed to load model: {exc}",
        ), 400

    record_opened_file(str(path))
    _sess.load(model, path)
    return redirect(url_for("model_core.main_menu"))
