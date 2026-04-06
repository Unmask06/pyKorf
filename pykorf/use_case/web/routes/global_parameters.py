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
        saved_shutoff_margin = interaction_data.get("shutoff_margin") or "1.20"
        if not saved_selections and "selected_settings" in interaction_data:
            saved_selections = interaction_data.get("selected_settings", [])
        return render_template(
            "global_parameters.html",
            kdf_path=str(_sess.get_kdf_path() or ""),
            settings=settings,
            saved_selections=saved_selections,
            saved_dp_margin=saved_dp_margin,
            saved_shutoff_margin=saved_shutoff_margin,
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

    shutoff_margin_str = (request.form.get("shutoff_margin") or "1.20").strip()
    try:
        shutoff_margin = float(shutoff_margin_str)
    except ValueError:
        shutoff_margin = 1.20
        shutoff_margin_str = "1.20"

    result_lines: list[tuple[str, str]] = []
    errors: list[str] = []

    if not selected_ids:
        errors.append("No settings selected. Please select at least one setting.")
    else:
        set_global_parameters_selected(selected_ids)
        interaction_data = {
            "dp_margin": dp_margin_str,
            "shutoff_margin": shutoff_margin_str,
            "selected_settings": selected_ids,
        }
        set_last_interaction("global_parameters", interaction_data)
        logger.info(
            "global_settings_apply",
            selected=selected_ids,
            dp_margin=dp_margin,
            shutoff_margin=shutoff_margin,
        )
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
                    result_lines.append(("info", f"  - ... and {len(pipes) - 10} more"))
            model.io.save()
            _sess.reload()
            result_lines.append(("success", "Model saved."))
        except Exception as exc:
            logger.error("global_settings_error", error=str(exc))
            errors.append(f"Error applying settings: {exc}")
            _sess.reload()

    return render_template(
        "global_parameters.html",
        kdf_path=str(_sess.get_kdf_path() or ""),
        settings=settings,
        saved_selections=selected_ids,
        saved_dp_margin=dp_margin_str,
        saved_shutoff_margin=shutoff_margin_str,
        result={"lines": result_lines, "errors": errors},
    )


@bp.route("/model/center_layout", methods=["POST"])
def center_layout():
    """Center all elements on the page."""
    model = require_model()
    if is_redirect(model):
        return model

    from pykorf.use_case.config import set_last_interaction
    from pykorf.use_case.global_parameters import get_global_settings

    result_lines: list[tuple[str, str]] = []
    errors: list[str] = []

    try:
        model.layout.center_layout()
        model.io.save()
        logger.info("center_layout_saved", path=str(_sess.get_kdf_path()))
        _sess.reload()
        result_lines.append(("success", "Layout centered successfully."))
        set_last_interaction("center_layout", {})
        logger.info("center_layout_applied")
    except Exception as exc:
        logger.error("center_layout_error", error=str(exc))
        errors.append(f"Error centering layout: {exc}")

    return render_template(
        "global_parameters.html",
        kdf_path=str(_sess.get_kdf_path() or ""),
        settings=get_global_settings(),
        saved_selections=[],
        saved_dp_margin="1.25",
        saved_shutoff_margin="1.20",
        result={"lines": result_lines, "errors": errors},
    )


@bp.route("/model/snap_orthogonal", methods=["POST"])
def snap_orthogonal_route():
    """Snap near-orthogonal connections and align all elements to grid."""
    model = require_model()
    if is_redirect(model):
        return model

    from pykorf.use_case.config import set_last_interaction
    from pykorf.use_case.global_parameters import get_global_settings

    threshold_deg_str = (request.form.get("orthogonal_threshold") or "10.0").strip()
    try:
        threshold_deg = float(threshold_deg_str)
    except ValueError:
        threshold_deg = 10.0
        threshold_deg_str = "10.0"

    grid_size_str = (request.form.get("grid_size") or "500.0").strip()
    try:
        grid_size = float(grid_size_str)
    except ValueError:
        grid_size = 500.0
        grid_size_str = "500.0"

    result_lines: list[tuple[str, str]] = []
    errors: list[str] = []

    try:
        model.layout.snap_orthogonal(threshold_deg=threshold_deg)
        model.layout.snap_to_grid(grid_size=grid_size)
        model.io.save()
        _sess.reload()
        result_lines.append(
            ("success", f"Snapped connections to orthogonal (threshold: {threshold_deg}°).")
        )
        result_lines.append(("success", f"Aligned all elements to {grid_size:.0f}-unit grid."))
        set_last_interaction(
            "snap_orthogonal", {"threshold": threshold_deg_str, "grid_size": grid_size_str}
        )
        logger.info("snap_orthogonal_applied", threshold=threshold_deg, grid_size=grid_size)
    except Exception as exc:
        logger.error("snap_orthogonal_error", error=str(exc))
        errors.append(f"Error snapping orthogonal: {exc}")

    return render_template(
        "global_parameters.html",
        kdf_path=str(_sess.get_kdf_path() or ""),
        settings=get_global_settings(),
        saved_selections=[],
        saved_dp_margin="1.25",
        saved_shutoff_margin="1.20",
        result={"lines": result_lines, "errors": errors},
    )
