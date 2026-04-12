"""Model API: /api/model/*."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from pykorf.app.api import session_state as _sess
from pykorf.app.api.deps import pipe_names, require_model
from pykorf.app.api.schemas import (
    BulkCopyRequest,
    BulkCopyResponse,
    ModelFullResponse,
    PipeCriteriaEntry,
    PipeCriteriaResponse,
    PredictCriteriaResponse,
    SaveProjectInfoRequest,
    SaveResponse,
    SetCriteriaResponse,
    SetPipeCriteriaRequest,
)
from pykorf.core.log import get_logger

logger = get_logger(__name__)
router = APIRouter()


# --- KORF defaults that should be replaced with pyKorf defaults ---
KORF_DEFAULTS: dict[str, list[str]] = {
    "company1": ["KORF", ""],
    "company2": ["Town, Country", ""],
    "project_name1": ["Company", ""],
    "project_name2": ["Town, Country", ""],
    "item_name1": ["Project", ""],
    "item_name2": [""],
    "project_no": [""],
    "prepared_by": [""],
    "checked_by": [""],
    "approved_by": [""],
    "date": [""],
    "revision": [""],
}


def _is_korf_default(field: str, value: str) -> bool:
    return value in KORF_DEFAULTS.get(field, [])


@router.get("/summary", response_model=ModelFullResponse)
async def get_summary():
    """Return model summary, prerequisites, and project info."""
    model = await require_model()
    from pykorf.app.api.routers.data import apply_pms_if_stale

    if apply_pms_if_stale(model):
        await _sess.reload()

    kdf_path = await _sess.get_kdf_path()

    # Build summary
    summary = model.get_summary()
    summary_resp = {
        "num_pipes": summary.get("num_pipes", 0),
        "num_junctions": summary.get("num_junctions", 0),
        "num_pumps": summary.get("num_pumps", 0),
        "num_valves": summary.get("num_valves", 0),
        "num_feeds": summary.get("num_feeds", 0),
        "num_products": summary.get("num_products", 0),
    }

    # Build prereqs
    from pykorf.app.api.routers.model import _build_prereqs

    prereqs = _build_prereqs(model, kdf_path)

    # Build project info
    from pykorf.app.operation.project.project_info import build_smart_defaults

    smart_defaults = build_smart_defaults(kdf_path)
    project_info = _build_project_info(model, kdf_path, smart_defaults)

    return ModelFullResponse(
        kdf_path=str(kdf_path or ""),
        summary=summary_resp,
        prereqs=prereqs,
        project_info=project_info,
        smart_defaults=smart_defaults,
    )


@router.post("/save", response_model=SaveResponse)
async def save_model():
    """Save the in-memory model back to its source .kdf file."""
    model = await require_model()
    from pykorf.core.log import flash_logs

    logs: list[dict[str, str]] = []
    with flash_logs() as flash_list:
        model.save()
        await _sess.reload()
    for alert_type, message in flash_list:
        logs.append({"type": alert_type, "message": message})
    return SaveResponse(message="Model saved to disk.", logs=logs)


@router.post("/project-info", response_model=SaveResponse)
async def save_project_info(req: SaveProjectInfoRequest):
    """Save project metadata (COM, PRJ, ENG) to the active KDF file."""
    model = await require_model()
    from pykorf.core.log import flash_logs, get_logger

    logger = get_logger(__name__)
    kdf_path = await _sess.get_kdf_path()
    if not kdf_path:
        return SaveResponse(message="No model loaded.", logs=[])

    logs: list[dict[str, str]] = []
    with flash_logs() as flash_list:
        logger.info("save_project_info", kdf_path=str(kdf_path))
        model.general.set_company(req.company1, req.company2)
        model.general.set_project(
            req.project_name1, req.project_name2, req.item_name1, req.item_name2
        )
        model.general.set_engineering(
            req.prepared_by,
            req.checked_by,
            req.approved_by,
            req.date,
            req.project_no,
            req.revision,
        )
        model.save()
        await _sess.reload()
    for alert_type, message in flash_list:
        logs.append({"type": alert_type, "message": message})
    return SaveResponse(message="Project info saved.", logs=logs)


@router.get("/pipes")
async def get_pipes():
    """Return list of pipe names for dropdowns."""
    model = await require_model()
    return {"pipes": await pipe_names(model)}


@router.post("/bulk-copy", response_model=BulkCopyResponse)
async def bulk_copy(req: BulkCopyRequest):
    """Copy fluid properties from one pipe to multiple others."""
    model = await require_model()

    if not req.ref_pipe:
        return BulkCopyResponse(success=False, error="Please enter a reference pipe.")

    try:
        from pykorf.app import copy_fluids

        target_list = (
            [t.strip() for t in req.target_pipes.split(",") if t.strip()]
            if req.target_pipes
            else None
        )
        updated_pipes = copy_fluids(model, req.ref_pipe, target_list, req.exclude)
        model.save()
        await _sess.reload()
        return BulkCopyResponse(
            success=True,
            updated_pipes=updated_pipes,
            updated_count=len(updated_pipes),
        )
    except Exception as exc:
        await _sess.reload()
        return BulkCopyResponse(success=False, error=str(exc))


# --- Pipe Criteria ---


@router.get("/pipe-criteria", response_model=PipeCriteriaResponse)
async def get_pipe_criteria():
    """Get pipe criteria data for the criteria table."""
    model = await require_model()
    from pykorf.app.operation.project.pykorf_file import get_pipe_criteria
    from pykorf.app.operation.integration.sizing_criteria import all_codes_by_type, FLUID_LABELS

    kdf_path = await _sess.get_kdf_path()
    pipes = _get_pipes_list(model)
    codes = all_codes_by_type()
    existing = get_pipe_criteria(kdf_path) if kdf_path else {}
    existing = _seed_from_kdf(model, pipes, existing)
    pipe_criteria_values = _precompute_criteria_values(model, pipes, codes)
    pipe_calcs = _compute_pipe_calcs(model, pipes)

    return PipeCriteriaResponse(
        kdf_path=str(kdf_path or ""),
        pipes=pipes,
        existing=existing,
        codes=codes,
        fluid_labels=FLUID_LABELS,
        pipe_criteria_values=pipe_criteria_values,
        pipe_calcs=pipe_calcs,
        units_data=_load_units_data(),
    )


@router.post("/pipe-criteria", response_model=SetCriteriaResponse)
async def set_pipe_criteria(req: SetPipeCriteriaRequest):
    """Apply criteria to pipe SIZ parameters."""
    model = await require_model()
    from pykorf.app.operation.project.pykorf_file import set_pipe_criteria as save_criteria

    kdf_path = await _sess.get_kdf_path()
    pipes = _get_pipes_list(model)

    # Convert Pydantic entries to plain dict
    criteria_dict = {k: {"state": v.state, "criteria": v.criteria} for k, v in req.criteria.items()}

    if kdf_path:
        save_criteria(kdf_path, criteria_dict)

    result = _handle_set_criteria(model, pipes, criteria_dict)
    if await _sess.has_model():
        model.save()
        await _sess.reload()

    return SetCriteriaResponse(applied=result["applied"], skipped=result["skipped"])


@router.post("/pipe-criteria/predict", response_model=PredictCriteriaResponse)
async def predict_criteria():
    """Auto-predict state and criteria for all pipes."""
    model = await require_model()
    from pykorf.app.operation.project.pykorf_file import get_pipe_criteria

    kdf_path = await _sess.get_kdf_path()
    pipes = _get_pipes_list(model)
    existing = get_pipe_criteria(kdf_path) if kdf_path else {}
    existing = _seed_from_kdf(model, pipes, existing)

    predicted, predict_result = _handle_predict_action(model, pipes, existing)

    return PredictCriteriaResponse(
        predicted={
            k: PipeCriteriaEntry(state=v["state"], criteria=v["criteria"])
            for k, v in predicted.items()
        },
        filled_state=predict_result["filled_state"],
        filled_criteria=predict_result["filled_criteria"],
        errors=predict_result["errors"],
    )


# --- Helper functions (ported from routes/pipe_criteria.py) ---


def _get_pipes_list(model) -> list[tuple[int, str]]:
    return [
        (idx, model.pipes[idx].name)
        for idx in range(1, model.num_pipes + 1)
        if model.pipes[idx].name and not model.pipes[idx].name.startswith("d")
    ]


def _build_prereqs(model, kdf_path) -> dict:
    from pykorf.app.operation.config.config import (
        get_pms_excel_path,
        get_sp_overrides,
        get_skip_sp_override,
    )

    issues = model.validate()
    notes_ok = not any(
        "NOTES" in i or "missing line number" in i or "line number" in i.lower()
        for i in issues
    )
    validation_ok = len(issues) == 0
    pms_raw = get_pms_excel_path()
    pms_path = str(pms_raw) if pms_raw else ""
    pms_ok = bool(pms_path and Path(pms_path).is_file())
    skip_sp = get_skip_sp_override()
    sharepoint_ok = bool(get_sp_overrides()) if not skip_sp else True

    return {
        "notes_ok": notes_ok,
        "pms_ok": pms_ok,
        "validation_ok": validation_ok,
        "sharepoint_ok": sharepoint_ok,
        "issues": issues,
        "pms_path": pms_path,
    }


def _build_project_info(model, kdf_path, smart_defaults: dict) -> dict:
    gen = model.general
    raw_values = {
        "company1": gen.company or "",
        "company2": gen.company2 or "",
        "project_name1": gen.project or "",
        "project_name2": gen.project_name2 or "",
        "item_name1": gen.item_name1 or "",
        "item_name2": gen.item_name2 or "",
        "prepared_by": gen.prepared_by or "",
        "checked_by": gen.checked_by or "",
        "approved_by": gen.approved_by or "",
        "date": gen.date or "",
        "project_no": gen.project_no or "",
        "revision": gen.revision or "",
    }
    project_info = {}
    for field, value in raw_values.items():
        if _is_korf_default(field, value):
            project_info[field] = smart_defaults.get(field, "")
        else:
            project_info[field] = value
    return project_info


def _seed_from_kdf(model, pipes, existing):
    from pykorf.app.operation.integration.sizing_criteria import code_to_state

    pipe_by_name = _build_pipe_lookup(model)
    merged = {k: dict(v) for k, v in existing.items()}
    for _, pipe_name in pipes:
        saved = merged.get(pipe_name, {})
        if saved.get("state") or saved.get("criteria"):
            continue
        pipe = pipe_by_name.get(pipe_name)
        if pipe is None:
            continue
        code = pipe.criteria_code
        if not code:
            continue
        state = code_to_state(code)
        if state:
            merged[pipe_name] = {"state": state, "criteria": code}
    return merged


def _build_pipe_lookup(model):
    return {
        model.pipes[i].name: model.pipes[i]
        for i in range(1, model.num_pipes + 1)
        if model.pipes[i].name and not model.pipes[i].name.startswith("d")
    }


def _precompute_criteria_values(model, pipes, codes):
    from pykorf.app.operation.integration.sizing_criteria import lookup_criteria

    result: dict[str, dict[str, dict]] = {}
    for _, pipe_name in pipes:
        pipe = _get_pipe_by_name(model, pipe_name)
        if pipe is None:
            result[pipe_name] = {}
            continue
        size_inch, pressure_barg = _get_pipe_size_and_pressure(pipe)
        pipe_vals = {}
        for state, code_list in codes.items():
            for code, _ in code_list:
                vals = lookup_criteria(state, code, size_inch, pressure_barg)
                if vals is not None:
                    pipe_vals[f"{state}:{code}"] = {
                        "max_dp": vals.max_dp,
                        "max_vel": vals.max_vel,
                        "min_vel": vals.min_vel,
                        "rho_v2_min": vals.rho_v2_min,
                        "rho_v2_max": vals.rho_v2_max,
                    }
        result[pipe_name] = pipe_vals
    return result


def _compute_pipe_calcs(model, pipes) -> dict[str, dict[str, float | None]]:
    lookup = _build_pipe_lookup(model)
    result: dict[str, dict[str, float | None]] = {}
    for _, name in pipes:
        pipe = lookup.get(name)
        if pipe is None:
            result[name] = {"dp_calc": None, "vel_calc": None, "rho_v2_calc": None}
            continue
        vel_list = pipe.velocity
        dp = pipe.pressure_drop_per_100m
        result[name] = {
            "dp_calc": dp if dp else None,
            "vel_calc": vel_list[0] if vel_list else None,
            "rho_v2_calc": pipe.rho_v2,
        }
    return result


def _load_units_data():
    import json

    from pykorf.core.reports.unit_converter import UNITS_JSON_PATH

    if UNITS_JSON_PATH.exists():
        with open(UNITS_JSON_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _get_pipe_by_name(model, pipe_name):
    for i in range(1, model.num_pipes + 1):
        if model.pipes[i].name == pipe_name:
            return model.pipes[i]
    return None


def _get_pipe_size_and_pressure(pipe):
    try:
        size_inch = float(pipe.diameter_inch or 9999)
    except (ValueError, TypeError):
        size_inch = 9999.0
    pressures = pipe.pressure or []
    try:
        pressure_barg = pressures[0] / 100.0 if pressures else 9999.0
    except (IndexError, TypeError):
        pressure_barg = 9999.0
    return size_inch, pressure_barg


def _handle_set_criteria(model, pipes, existing):
    from pykorf.app.operation.integration.sizing_criteria import lookup_criteria

    applied = 0
    skipped = []
    for _, pipe_name in pipes:
        saved = existing.get(pipe_name, {})
        state = saved.get("state", "")
        code = saved.get("criteria", "")
        if not state or not code:
            continue
        pipe = _get_pipe_by_name(model, pipe_name)
        if pipe is None:
            skipped.append(pipe_name)
            continue
        size_inch, pressure_barg = _get_pipe_size_and_pressure(pipe)
        vals = lookup_criteria(state, code, size_inch, pressure_barg)
        if vals is None:
            skipped.append(pipe_name)
            continue
        pipe.criteria_code = code
        pipe.max_dp_criteria = vals.max_dp
        pipe.max_velocity_criteria = vals.max_vel
        pipe.min_velocity_criteria = vals.min_vel
        applied += 1
    return {"applied": applied, "skipped": skipped}


def _handle_predict_action(model, pipes, existing):
    from pykorf.app.operation.integration.sizing_criteria import predict_criteria, predict_state

    predicted = {k: dict(v) for k, v in existing.items()}
    filled_state_total = 0
    filled_criteria_total = 0
    errors = []
    pipe_by_name = _build_pipe_lookup(model)

    for idx, pipe_name in pipes:
        try:
            pipe = pipe_by_name.get(pipe_name)
            if pipe is None:
                continue
            current = predicted.get(pipe_name, {})
            state = current.get("state", "")
            criteria = current.get("criteria", "")
            if not state:
                try:
                    fluid = pipe.get_fluid()
                    raw_lf = fluid.lf
                    lf_values = raw_lf if isinstance(raw_lf, list) else []
                    predicted_state = predict_state(lf_values) or ""
                    if predicted_state:
                        state = predicted_state
                        filled_state_total += 1
                except Exception as exc:
                    errors.append(f"{pipe_name} state: {exc}")
            if not criteria and state:
                try:
                    predicted_crit = predict_criteria(state, pipe_name) or ""
                    if predicted_crit:
                        criteria = predicted_crit
                        filled_criteria_total += 1
                except Exception as exc:
                    errors.append(f"{pipe_name} criteria: {exc}")
            if state or criteria:
                predicted[pipe_name] = {"state": state, "criteria": criteria}
        except Exception as exc:
            errors.append(f"{pipe_name}: {exc}")

    predict_result = {
        "filled_state": filled_state_total,
        "filled_criteria": filled_criteria_total,
        "errors": errors,
    }
    return predicted, predict_result
