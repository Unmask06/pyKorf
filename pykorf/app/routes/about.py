"""About route: /about."""

from __future__ import annotations

from flask import Blueprint, render_template

from pykorf import __version__

bp = Blueprint("about", __name__)

_RELEASE_DATE = "2026-03-29"


@bp.route("/about")
def about():
    """Render the About page."""
    return render_template("about.html", version=__version__, release_date=_RELEASE_DATE)
