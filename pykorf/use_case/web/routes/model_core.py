"""Core model routes: /model and /model/save."""

from __future__ import annotations

from flask import Blueprint, redirect, render_template, url_for

from pykorf.use_case.web import session as _sess
from pykorf.use_case.web.helpers import is_redirect, require_model

bp = Blueprint("model_core", __name__)


@bp.route("/model")
def main_menu():
    """Render the main menu with model summary."""
    model = require_model()
    if is_redirect(model):
        return model
    return render_template(
        "main_menu.html",
        kdf_path=str(_sess.get_kdf_path() or ""),
        summary=model.summary(),
    )


@bp.route("/model/save", methods=["POST"])
def save_model():
    """Save the in-memory model back to its source .kdf file."""
    model = require_model()
    if is_redirect(model):
        return model
    kdf_path = _sess.get_kdf_path()
    if kdf_path:
        model.io.save(kdf_path)
    return redirect(url_for("model_core.main_menu"))
