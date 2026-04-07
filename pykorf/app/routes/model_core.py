"""Core model routes: /model and /model/save."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, url_for

from pykorf.core.log import flash_logs, get_logger
from pykorf.app.web import session as _sess
from pykorf.app.web.helpers import is_redirect, require_model

logger = get_logger(__name__)
bp = Blueprint("model_core", __name__)


def _build_prereqs(model, kdf_path) -> dict:
    """Build prerequisite check results for the main menu.

    Returns:
        Dict with keys: notes_ok, pms_ok, validation_ok, sharepoint_ok,
        issues (full list), pms_path.
    """
    from pykorf.app.operation.config.config import get_pms_excel_path, get_sp_overrides

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
    from pykorf.app.routes.data import apply_pms_if_stale

    apply_pms_if_stale(model)
    kdf_path = _sess.get_kdf_path()
    prereqs = _build_prereqs(model, kdf_path)

    from pykorf.app.operation.project.project_info import build_smart_defaults

    gen = model.general
    project_info = {
        "company1": gen.company or "",
        "company2": gen.company2 or "",
        "project_name1": gen.project or "",
        "project_name2": gen.project_name2 or "",
        "item_name1": gen.item_name1 or "",
        "item_name2": gen.item_name2 or "",
        "prepared_by": gen.prepared_by or "",
        "checked_by": gen.checked_by or "",
        "approved_by": gen.approved_by or "",
        "date": gen.date or "",
        "project_no": gen.project_no or "",
        "revision": gen.revision or "",
    }
    smart_defaults = build_smart_defaults(kdf_path)

    return render_template(
        "main_menu.html",
        kdf_path=str(kdf_path or ""),
        summary=model.get_summary(),
        prereqs=prereqs,
        project_info=project_info,
        smart_defaults=smart_defaults,
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
        flash("Model reloaded from disk", "success")
    next_url = request.form.get("next", "").strip()
    if next_url:
        if next_url.startswith("/"):
            return redirect(next_url)
    return redirect(url_for("model_core.main_menu"))


@bp.route("/model/save", methods=["POST"])
def save_model():
    """Save the in-memory model back to its source .kdf file."""
    model = require_model()
    if is_redirect(model):
        return model
    if _sess.has_model():
        with flash_logs() as logs:
            model.save()
            _sess.reload()
        for alert_type, message in logs:
            flash(message, alert_type)
        flash("Model saved to disk.", "success")
    return redirect(url_for("model_core.main_menu"))


@bp.route("/model/project-info", methods=["POST"])
def save_project_info():
    """Save project metadata (COM, PRJ, ENG) to the active KDF file."""
    model = require_model()
    if is_redirect(model):
        return model
    kdf_path = _sess.get_kdf_path()
    if not kdf_path:
        flash("No model loaded.", "warning")
        return redirect(url_for("model_core.main_menu"))

    company1 = request.form.get("company1", "").strip()
    company2 = request.form.get("company2", "").strip()
    project_name1 = request.form.get("project_name1", "").strip()
    project_name2 = request.form.get("project_name2", "").strip()
    item_name1 = request.form.get("item_name1", "").strip()
    item_name2 = request.form.get("item_name2", "").strip()
    prepared_by = request.form.get("prepared_by", "").strip()
    checked_by = request.form.get("checked_by", "").strip()
    approved_by = request.form.get("approved_by", "").strip()
    date = request.form.get("date", "").strip()
    project_no = request.form.get("project_no", "").strip()
    revision = request.form.get("revision", "").strip()

    with flash_logs() as logs:
        logger.info("save_project_info", kdf_path=str(kdf_path))
        model.general.set_company(company1, company2)
        model.general.set_project(project_name1, project_name2, item_name1, item_name2)
        model.general.set_engineering(
            prepared_by, checked_by, approved_by, date, project_no, revision
        )
        model.save()
        _sess.reload()
    for alert_type, message in logs:
        flash(message, alert_type)
    flash("Project info saved.", "success")
    return redirect(url_for("model_core.main_menu"))
