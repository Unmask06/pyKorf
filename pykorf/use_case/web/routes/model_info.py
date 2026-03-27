"""Model Info route: /model/info."""

from __future__ import annotations

from flask import Blueprint, render_template

from pykorf.use_case.web import session as _sess
from pykorf.use_case.web.helpers import is_redirect, model_summary, pipe_names, require_model

bp = Blueprint("model_info", __name__)


@bp.route("/model/info")
def model_info():
    """Render the Model Info page with element statistics and pipe list."""
    model = require_model()
    if is_redirect(model):
        return model
    return render_template(
        "model_info.html",
        kdf_path=str(_sess.get_kdf_path() or ""),
        summary=model_summary(model),
        pipes=pipe_names(model),
    )
