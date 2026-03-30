"""Bulk Copy route: /model/bulk-copy."""

from __future__ import annotations

from flask import Blueprint, render_template, request

from pykorf.use_case.web import session as _sess
from pykorf.use_case.web.helpers import is_redirect, pipe_names, require_model

import structlog
logger = structlog.get_logger(__name__)
bp = Blueprint("bulk_copy", __name__)


@bp.route("/model/bulk-copy", methods=["GET", "POST"])
def bulk_copy():
    """Render and handle the Bulk Copy Fluids page."""
    model = require_model()
    if is_redirect(model):
        return model

    result = None
    error = None
    ref_pipe = ""
    target_pipes = ""
    exclude = False
    updated_count = 0
    updated_pipes: list[str] = []

    if request.method == "POST":
        ref_pipe = (request.form.get("ref_pipe") or "").strip()
        target_pipes = (request.form.get("target_pipes") or "").strip()
        exclude = request.form.get("exclude") == "on"

        if not ref_pipe:
            error = "Please enter a reference pipe."
        else:
            try:
                from pykorf.use_case import copy_fluids

                target_list = (
                    [t.strip() for t in target_pipes.split(",") if t.strip()]
                    if target_pipes
                    else None
                )
                updated_pipes = copy_fluids(model, ref_pipe, target_list, exclude)
                updated_count = len(updated_pipes)
                result = "success"
                model.io.save()
                _sess.reload()
            except Exception as exc:
                error = f"Error: {exc}"

    pipes = pipe_names(model)

    return render_template(
        "bulk_copy.html",
        kdf_path=str(_sess.get_kdf_path() or ""),
        pipes=pipes,
        ref_pipe=ref_pipe,
        target_pipes=target_pipes,
        exclude=exclude,
        result=result,
        error=error,
        updated_count=updated_count,
        updated_pipes=updated_pipes,
    )
