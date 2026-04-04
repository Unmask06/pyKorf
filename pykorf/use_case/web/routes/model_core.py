"""Core model routes: /model and /model/save."""

from __future__ import annotations

from pathlib import Path

import structlog
from flask import Blueprint, redirect, render_template, request, url_for

from pykorf.use_case.web import session as _sess
from pykorf.use_case.web.helpers import is_redirect, require_model

logger = structlog.get_logger(__name__)
bp = Blueprint("model_core", __name__)


def _build_prereqs(model, kdf_path) -> dict:
    """Build prerequisite check results for the main menu.

    Returns:
        Dict with keys: notes_ok, pms_ok, validation_ok, sharepoint_ok,
        issues (full list), pms_path.
    """
    from pykorf.use_case.config import get_pms_excel_path, get_sp_overrides

    issues = model.validate()

    notes_ok = not any(
        "NOTES" in i or "missing line number" in i or "line number" in i.lower() for i in issues
    )
    validation_ok = len(issues) == 0

    pms_raw = get_pms_excel_path()
    pms_path = str(pms_raw) if pms_raw else ""
    pms_ok = bool(pms_path and Path(pms_path).is_file())

    sp_overrides = get_sp_overrides()
    sharepoint_ok = bool(sp_overrides)

    return {
        "notes_ok": notes_ok,
        "pms_ok": pms_ok,
        "validation_ok": validation_ok,
        "sharepoint_ok": sharepoint_ok,
        "issues": issues,
        "pms_path": pms_path,
    }


@bp.route("/model")
def main_menu():
    """Render the main menu with model summary."""
    model = require_model()
    if is_redirect(model):
        return model
    from pykorf.use_case.web.routes.data import apply_pms_if_stale

    apply_pms_if_stale(model)
    kdf_path = _sess.get_kdf_path()
    prereqs = _build_prereqs(model, kdf_path)
    return render_template(
        "main_menu.html",
        kdf_path=str(kdf_path or ""),
        summary=model.summary(),
        prereqs=prereqs,
    )


@bp.route("/model/reload", methods=["POST"])
def reload_model():
    """Re-parse the KDF from disk and redirect back to the calling page."""
    model = require_model()
    if is_redirect(model):
        return model
    kdf_path = _sess.get_kdf_path()
    if kdf_path:
        logger.info("reload_model", kdf_path=str(kdf_path))
        _sess.reload()
        logger.info("reload_model_complete", kdf_path=str(kdf_path))
    next_url = request.form.get("next", "").strip()
    return redirect(next_url or url_for("model_core.main_menu"))


@bp.route("/model/save", methods=["POST"])
def save_model():
    """Save the in-memory model back to its source .kdf file."""
    model = require_model()
    if is_redirect(model):
        return model
    kdf_path = _sess.get_kdf_path()
    if kdf_path:
        logger.info("save_model", kdf_path=str(kdf_path))
        model.io.save(kdf_path)
        _sess.reload()
        logger.info("save_model_complete", kdf_path=str(kdf_path))
    return redirect(url_for("model_core.main_menu"))
