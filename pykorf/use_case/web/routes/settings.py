"""Global Parameters route: /model/settings."""

from __future__ import annotations

from typing import Any

import structlog
from flask import Blueprint, render_template, request

from pykorf.use_case.web import session as _sess
from pykorf.use_case.web.helpers import is_redirect, require_model

logger = structlog.get_logger(__name__)
bp = Blueprint("settings", __name__)


@bp.route("/model/settings", methods=["GET", "POST"])
def global_settings():
    """Render and handle the Global Parameters form."""
    model = require_model()
    if is_redirect(model):
        return model

    from pykorf.use_case.config import get_global_parameters_selected, get_last_interaction
    from pykorf.use_case.global_parameters import apply_global_settings, get_global_settings

    settings = get_global_settings()

    if request.method == "GET":
        saved_selections: list[str] = get_global_parameters_selected() or []
        interaction_data = get_last_interaction()
        saved_dp_margin = interaction_data.get("dp_margin") or "1.25"
        if not saved_selections and "selected_settings" in interaction_data:
            saved_selections = interaction_data.get("selected_settings", [])
        return render_template(
            "global_parameters.html",
            kdf_path=str(_sess.get_kdf_path() or ""),
            settings=settings,
            saved_selections=saved_selections,
            saved_dp_margin=saved_dp_margin,
            result=None,
        )

    # POST — apply settings
    from pykorf.use_case.config import set_global_parameters_selected, set_last_interaction

    selected_ids = [s.id for s in settings if request.form.get(f"setting_{s.id}")]

    dp_margin_str = (request.form.get("dp_margin") or "1.25").strip()
    try:
        dp_margin = float(dp_margin_str)
    except ValueError:
        dp_margin = 1.25
        dp_margin_str = "1.25"

    result_lines: list[tuple[str, str]] = []
    errors: list[str] = []

    if not selected_ids:
        errors.append("No settings selected. Please select at least one setting.")
    else:
        set_global_parameters_selected(selected_ids)
        interaction_data = {
            "dp_margin": dp_margin_str,
            "selected_settings": selected_ids,
        }
        set_last_interaction("global_parameters", interaction_data)
        logger.info("global_settings_apply", selected=selected_ids, dp_margin=dp_margin)
        try:
            apply_results: dict[str, Any] = apply_global_settings(
                model, selected_ids, save=False, dp_margin=dp_margin
            )
            errs: list[str] = apply_results.pop("_errors", [])
            errors.extend(errs)
            for setting_id, pipes in apply_results.items():
                setting = next(s for s in settings if s.id == setting_id)
                logger.info("global_setting_result", setting=setting_id, pipes_affected=len(pipes))
                result_lines.append(("success", f"{setting.name}: {len(pipes)} pipe(s) affected"))
                for pipe_name in pipes[:10]:
                    result_lines.append(("info", f"  - {pipe_name}"))
                if len(pipes) > 10:
                    result_lines.append(("info", f"  - … and {len(pipes) - 10} more"))
        except Exception as exc:
            logger.error("global_settings_error", error=str(exc))
            errors.append(f"Error applying settings: {exc}")

    return render_template(
        "global_parameters.html",
        kdf_path=str(_sess.get_kdf_path() or ""),
        settings=settings,
        saved_selections=selected_ids,
        saved_dp_margin=dp_margin_str,
        result={"lines": result_lines, "errors": errors},
    )
