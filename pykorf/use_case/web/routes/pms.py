"""Apply PMS route: /model/pms."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, render_template, request

from pykorf.use_case.web import session as _sess
from pykorf.use_case.web.helpers import is_redirect, require_model

bp = Blueprint("pms", __name__)


@bp.route("/model/pms", methods=["GET", "POST"])
def apply_pms():
    """Render and handle the Apply PMS form."""
    model = require_model()
    if is_redirect(model):
        return model

    from pykorf.use_case.config import get_pms_path

    if request.method == "GET":
        return render_template(
            "pms.html",
            kdf_path=str(_sess.get_kdf_path() or ""),
            pms_json_path=str(get_pms_path() or ""),
            result=None,
        )

    pms_source_str = (request.form.get("pms_source") or "").strip()
    pms_source = Path(pms_source_str) if pms_source_str else get_pms_path()

    result_lines: list[tuple[str, str]] = []
    errors: list[str] = []

    if not pms_source or not Path(pms_source).is_file():
        errors.append(f"PMS data file not found: {pms_source}")
    else:
        try:
            from pykorf.use_case.pms import apply_pms as _apply_pms

            _apply_pms(pms_source, model, save=False)
            result_lines.append(("success", "PMS data applied successfully."))
        except Exception as exc:
            errors.append(f"Error applying PMS: {exc}")

    return render_template(
        "pms.html",
        kdf_path=str(_sess.get_kdf_path() or ""),
        pms_json_path=str(pms_source or ""),
        result={"lines": result_lines, "errors": errors},
    )
