"""Settings API: /api/settings/*."""

from __future__ import annotations

from fastapi import APIRouter

from pykorf.app.api import session_state as _sess
from pykorf.app.api.deps import require_model
from pykorf.app.api.schemas import (
    ApplyGlobalSettingsRequest,
    CenterLayoutResponse,
    GlobalSettingSchema,
    SettingsApplyResponse,
    SnapOrthogonalRequest,
)
from pykorf.core.log import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
async def get_settings():
    """Return list of available global settings with saved selections."""
    from pykorf.app.operation.config.config import (
        get_global_parameters_selected,
        get_last_interaction,
    )
    from pykorf.app.operation.config.global_parameters import get_global_settings

    settings = get_global_settings()
    saved_selections = get_global_parameters_selected() or []
    interaction_data = get_last_interaction()
    saved_dp_margin = interaction_data.get("dp_margin") or "1.25"
    saved_shutoff_margin = interaction_data.get("shutoff_margin") or "1.20"

    return {
        "settings": [
            GlobalSettingSchema(id=s.id, name=s.name, description=s.description)
            for s in settings
        ],
        "saved_selections": saved_selections,
        "saved_dp_margin": saved_dp_margin,
        "saved_shutoff_margin": saved_shutoff_margin,
    }


@router.post("/apply", response_model=SettingsApplyResponse)
async def apply_settings(req: ApplyGlobalSettingsRequest):
    """Apply selected global settings to the model."""
    model = await require_model()
    from pykorf.app.operation.config.config import (
        set_global_parameters_selected,
        set_last_interaction,
    )
    from pykorf.app.operation.config.global_parameters import apply_global_settings

    if not req.setting_ids:
        return SettingsApplyResponse(errors=["No settings selected."])

    set_global_parameters_selected(req.setting_ids)
    set_last_interaction(
        "global_parameters",
        {
            "dp_margin": str(req.dp_margin),
            "shutoff_margin": str(req.shutoff_margin),
            "selected_settings": req.setting_ids,
        },
    )

    try:
        apply_results = apply_global_settings(
            model, req.setting_ids, save=True, dp_margin=req.dp_margin
        )
        await _sess.reload()
        errors = apply_results.pop("_errors", [])
        results = dict(apply_results.items())
        return SettingsApplyResponse(results=results, errors=errors, message="Settings applied.")
    except Exception as exc:
        logger.error("global_settings_error", error=str(exc))
        return SettingsApplyResponse(errors=[str(exc)])


@router.post("/center-layout", response_model=CenterLayoutResponse)
async def center_layout():
    """Center all elements on the page."""
    model = await require_model()
    from pykorf.app.operation.config.config import set_last_interaction

    try:
        model._layout_service.center_layout()
        model.save()
        await _sess.reload()
        set_last_interaction("center_layout", {})
        return CenterLayoutResponse(message="Layout centered successfully.")
    except Exception as exc:
        logger.error("center_layout_error", error=str(exc))
        raise


@router.post("/snap-orthogonal", response_model=CenterLayoutResponse)
async def snap_orthogonal(req: SnapOrthogonalRequest):
    """Snap near-orthogonal connections and align to grid."""
    model = await require_model()
    from pykorf.app.operation.config.config import set_last_interaction

    try:
        model._layout_service.snap_orthogonal(threshold_deg=req.threshold_deg)
        model._layout_service.snap_to_grid(grid_size=req.grid_size)
        model.save()
        await _sess.reload()
        set_last_interaction(
            "snap_orthogonal",
            {"threshold": str(req.threshold_deg), "grid_size": str(req.grid_size)},
        )
        return CenterLayoutResponse(
            message="Snapped connections to orthogonal and aligned to grid."
        )
    except Exception as exc:
        logger.error("snap_orthogonal_error", error=str(exc))
        raise
