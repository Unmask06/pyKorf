"""Settings API: /api/settings/*."""

from __future__ import annotations

from fastapi import APIRouter

from pykorf.app.api import session_state as _sess
from pykorf.app.api.deps import require_model
from pykorf.app.api.schemas import (
    ApplyGlobalSettingsRequest,
    CenterLayoutResponse,
    EmptyRequest,
    GlobalSettingSchema,
    SettingsApplyResponse,
    SettingsGetResponse,
    SnapOrthogonalRequest,
)
from pykorf.core.log import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=SettingsGetResponse, operation_id="getSettings")
async def get_settings() -> SettingsGetResponse:
    """Return list of available global settings with saved selections."""
    from pykorf.app.operation.config.config import (
        get_global_parameters_selected,
        get_last_interaction,
    )
    from pykorf.app.operation.config.defaults import (
        get_default_dp_margin,
        get_default_min_pump_elevation,
        get_default_min_vel_coeff,
        get_default_shutoff_margin,
    )
    from pykorf.app.operation.config.global_parameters import (
        get_default_settings,
        get_global_settings,
    )

    settings = get_global_settings()
    default_settings = get_default_settings()
    saved_selections = get_global_parameters_selected() or []
    interaction_data = get_last_interaction()
    saved_dp_margin = interaction_data.get("dp_margin") or str(get_default_dp_margin())
    saved_shutoff_margin = interaction_data.get("shutoff_margin") or str(
        get_default_shutoff_margin()
    )
    saved_pump_elevation = interaction_data.get("pump_elevation") or str(
        get_default_min_pump_elevation()
    )
    saved_min_vel_coeff = interaction_data.get("min_vel_coeff") or str(get_default_min_vel_coeff())

    return SettingsGetResponse(
        settings=[
            GlobalSettingSchema(id=s.id, name=s.name, description=s.description) for s in settings
        ],
        default_settings=[
            GlobalSettingSchema(id=s.id, name=s.name, description=s.description)
            for s in default_settings
        ],
        saved_selections=saved_selections,
        saved_dp_margin=saved_dp_margin,
        saved_shutoff_margin=saved_shutoff_margin,
        saved_min_pump_elev=saved_pump_elevation,
        saved_min_vel_coeff=saved_min_vel_coeff,
    )


@router.post("/apply", response_model=SettingsApplyResponse, operation_id="applySettings")
async def apply_settings(req: ApplyGlobalSettingsRequest) -> SettingsApplyResponse:
    """Apply selected global settings to the model."""
    model = await require_model()
    from pykorf.app.operation.config.config import (
        set_global_parameters_selected,
        set_last_interaction,
    )
    from pykorf.app.operation.config.global_parameters import apply_global_settings

    set_global_parameters_selected(req.setting_ids)
    set_last_interaction(
        "global_parameters",
        {
            "dp_margin": str(req.dp_margin),
            "shutoff_margin": str(req.shutoff_margin),
            "pump_elevation": str(req.min_pump_elevation),
            "min_vel_coeff": str(req.min_vel_coeff),
            "selected_settings": req.setting_ids,
        },
    )

    try:
        apply_results = apply_global_settings(
            model,
            req.setting_ids,
            save=True,
            dp_margin=req.dp_margin,
            shutoff_margin=req.shutoff_margin,
            min_pump_elevation=req.min_pump_elevation,
            min_vel_coeff=req.min_vel_coeff,
        )
        await _sess.reload()
        errors = apply_results.pop("_errors", [])
        results = dict(apply_results.items())
        return SettingsApplyResponse(results=results, errors=errors, message="Settings applied.")
    except Exception as exc:
        logger.error("global_settings_error", error=str(exc))
        return SettingsApplyResponse(errors=[str(exc)])


@router.post("/center-layout", response_model=CenterLayoutResponse, operation_id="centerLayout")
async def center_layout(_: EmptyRequest) -> CenterLayoutResponse:
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


@router.post("/snap-orthogonal", response_model=CenterLayoutResponse, operation_id="snapOrthogonal")
async def snap_orthogonal(req: SnapOrthogonalRequest) -> CenterLayoutResponse:
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
