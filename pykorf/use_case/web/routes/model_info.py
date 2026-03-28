"""Model Info route: /model/info."""

from __future__ import annotations

from flask import Blueprint, render_template

from pykorf.use_case.web import session as _sess
from pykorf.use_case.web.helpers import is_redirect, pipe_names, require_model

bp = Blueprint("model_info", __name__)


def _categorize_issue(issue: str) -> str:
    """Categorize validation issue by type."""
    issue_lower = issue.lower()
    if "NUM" in issue:
        return "NUM"
    elif "NAME" in issue or "missing NAME" in issue:
        return "NAME"
    elif "CON" in issue or "references" in issue:
        return "CONN"
    elif "NOTES" in issue:
        return "NOTES"
    elif "empty" in issue_lower or "whitespace" in issue_lower:
        return "VALUE"
    elif "Layout" in issue or "overlap" in issue or "clash" in issue:
        return "LAYOUT"
    elif "connectivity" in issue_lower:
        return "CONN"
    elif "missing" in issue_lower or "required" in issue_lower:
        return "REQUIRED"
    return "INFO"


@bp.route("/model/info")
def model_info():
    """Render the Model Info page with element statistics, pipe list, and validation."""
    model = require_model()
    if is_redirect(model):
        return model

    validation_issues = model.validate()
    categorized_issues = [
        {"category": _categorize_issue(issue), "message": issue} for issue in validation_issues
    ]

    return render_template(
        "model_info.html",
        kdf_path=str(_sess.get_kdf_path() or ""),
        summary=model.summary(),
        pipes=pipe_names(model),
        validation_issues=categorized_issues,
        has_errors=len(validation_issues) > 0,
        error_count=len(validation_issues),
    )
