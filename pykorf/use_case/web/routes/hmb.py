"""Apply HMB route: /model/hmb."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, render_template, request

from pykorf.use_case.web import session as _sess
from pykorf.use_case.web.helpers import is_redirect, require_model

bp = Blueprint("hmb", __name__)


@bp.route("/model/hmb", methods=["GET", "POST"])
def apply_hmb():
    """Render and handle the Apply HMB form."""
    model = require_model()
    if is_redirect(model):
        return model

    from pykorf.use_case.config import get_stream_path

    if request.method == "GET":
        return render_template(
            "hmb.html",
            kdf_path=str(_sess.get_kdf_path() or ""),
            hmb_json_path=str(get_stream_path() or ""),
            result=None,
        )

    hmb_source_str = (request.form.get("hmb_source") or "").strip()
    hmb_source = Path(hmb_source_str) if hmb_source_str else get_stream_path()

    result_lines: list[tuple[str, str]] = []
    errors: list[str] = []

    if not hmb_source or not Path(hmb_source).is_file():
        errors.append(f"HMB data file not found: {hmb_source}")
    else:
        try:
            from pykorf.use_case.hmb import apply_hmb as _apply_hmb

            _apply_hmb(hmb_source, model, save=False)
            result_lines.append(("success", "HMB data applied successfully."))
        except Exception as exc:
            errors.append(f"Error applying HMB: {exc}")

    return render_template(
        "hmb.html",
        kdf_path=str(_sess.get_kdf_path() or ""),
        hmb_json_path=str(hmb_source or ""),
        result={"lines": result_lines, "errors": errors},
    )
