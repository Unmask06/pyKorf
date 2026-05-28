"""Model API: /api/model/*."""

from __future__ import annotations

import asyncio
from functools import cache
from pathlib import Path

from fastapi import APIRouter, HTTPException

from pykorf.app.api import session_state as _sess
from pykorf.app.api.deps import is_real_pipe, pipe_names, require_model
from pykorf.app.api.schemas import (
    BulkCopyRequest,
    BulkCopyResponse,
    CriteriaValuesInfo,
    CriteriaViolationsInfo,
    EmptyRequest,
    JustificationRequest,
    JustificationSaveResponse,
    ModelFullResponse,
    ModelPipesResponse,
    ModelSummaryResponse,
    PipeCalcInfo,
    PipeCriteriaEntry,
    PipeCriteriaResponse,
    PredictCriteriaRequest,
    PredictCriteriaResponse,
    PrereqsResponse,
    ProjectInfoRequiredResponse,
    ProjectInfoResponse,
    ProjectInfoStatusResponse,
    SaveProjectInfoRequest,
    SaveResponse,
    SetCriteriaResponse,
    SetPipeCriteriaRequest,
    SmartDefaultsResponse,
    StatusMessage,
    UnitConversionInfo,
    ViolationSummary,
)
from pykorf.app.operation.project.pykorf_file import get_justifications, set_justifications
from pykorf.core.log import get_logger
from pykorf.core.model import Model

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

REQUIRED_PROJECT_INFO_FIELDS = ["company1", "company2", "project_name1", "prepared_by"]


def _is_korf_default(field: str, value: str) -> bool:
    return value in KORF_DEFAULTS.get(field, [])


def _is_project_info_complete_raw(
    model, smart_defaults: SmartDefaultsResponse
) -> tuple[bool, list[str]]:
    """Check if required project info fields are filled with real values.

    Reads raw values directly from model.general. Returns a tuple of
    (is_complete, incomplete_fields) where incomplete_fields contains
    the names of fields that are empty or whitespace-only.
    """
    gen = model.general
    incomplete: list[str] = []
    for field in REQUIRED_PROJECT_INFO_FIELDS:
        raw_value = (
            getattr(
                gen,
                {
                    "company1": "company",
                    "company2": "company2",
                    "project_name1": "project",
                    "prepared_by": "prepared_by",
                }.get(field, field),
                "",
            )
            or ""
        )
        if not raw_value.strip():
            incomplete.append(field)
    return (len(incomplete) == 0, incomplete)


async def check_project_info_or_return(
    model, kdf_path: Path | None
) -> ProjectInfoRequiredResponse | None:
    """Check if project info is complete. Returns None if OK, else returns response.

    Returns ProjectInfoRequiredResponse if:
    - Session hasn't confirmed project info yet
    - Required fields are empty or whitespace

    Call this at the start of mutating operations. If it returns a response,
    return that responses instead of proceeding with the operation.
    """
    from pykorf.app.operation.project.project_info import build_smart_defaults

    if _sess.is_project_info_checked():
        return None

    smart_defaults = SmartDefaultsResponse(**build_smart_defaults(kdf_path))
    project_info = _build_project_info(model, kdf_path, smart_defaults)

    is_complete, incomplete_fields = _is_project_info_complete_raw(model, smart_defaults)

    if is_complete:
        _sess.set_project_info_checked(True)
        return None

    return ProjectInfoRequiredResponse(
        project_info_required=True,
        project_info=project_info,
        smart_defaults=smart_defaults,
        required_fields=REQUIRED_PROJECT_INFO_FIELDS,
        incomplete_fields=incomplete_fields,
    )


@router.get(
    "/project-info/status",
    response_model=ProjectInfoStatusResponse,
    operation_id="getProjectInfoStatus",
)
async def get_project_info_status() -> ProjectInfoStatusResponse:
    """Return project info completeness status (non-blocking check).

    Unlike check_project_info_or_return, this endpoint never blocks operations.
    It simply returns the current status so the frontend can display warnings.
    """
    model = await require_model()
    kdf_path = await _sess.get_kdf_path()

    from pykorf.app.operation.project.project_info import build_smart_defaults

    smart_defaults = SmartDefaultsResponse(**build_smart_defaults(kdf_path))
    is_complete, incomplete_fields = _is_project_info_complete_raw(model, smart_defaults)

    return ProjectInfoStatusResponse(
        is_complete=is_complete,
        incomplete_fields=incomplete_fields,
        required_fields=REQUIRED_PROJECT_INFO_FIELDS,
    )


@router.get("/summary", response_model=ModelFullResponse, operation_id="getModelSummary")
async def get_summary() -> ModelFullResponse:
    """Return model summary, prerequisites, and project info."""
    model = await require_model()
    from pykorf.app.api.routers.data import apply_pms_if_stale

    if await asyncio.to_thread(apply_pms_if_stale, model):
        await _sess.reload()

    kdf_path = await _sess.get_kdf_path()

    # Build summary
    summary = model.get_summary()
    summary_resp = ModelSummaryResponse(
        num_pipes=summary.get("num_pipes", 0),
        num_junctions=summary.get("num_junctions", 0),
        num_pumps=summary.get("num_pumps", 0),
        num_valves=summary.get("num_valves", 0),
        num_feeds=summary.get("num_feeds", 0),
        num_products=summary.get("num_products", 0),
    )

    # Build prereqs
    from pykorf.app.api.routers.model import _build_prereqs

    prereqs = _build_prereqs(model, kdf_path)

    # Build project info
    from pykorf.app.operation.project.project_info import build_smart_defaults

    smart_defaults = SmartDefaultsResponse(**build_smart_defaults(kdf_path))
    project_info = _build_project_info(model, kdf_path, smart_defaults)

    return ModelFullResponse(
        kdf_path=str(kdf_path or ""),
        summary=summary_resp,
        prereqs=prereqs,
        project_info=project_info,
        smart_defaults=smart_defaults,
        required_fields=REQUIRED_PROJECT_INFO_FIELDS,
    )


@router.post("/save", response_model=SaveResponse, operation_id="saveModel")
async def save_model(_: EmptyRequest) -> SaveResponse:
    """Save the in-memory model back to its source .kdf file."""
    model = await require_model()
    from pykorf.core.log import flash_logs

    logs: list[StatusMessage] = []
    with flash_logs() as flash_list:
        model.save()
        await _sess.reload()
    for alert_type, message in flash_list:
        logs.append(StatusMessage(type=alert_type, message=message))
    return SaveResponse(message="Model saved to disk.", logs=logs)


@router.post("/project-info", response_model=SaveResponse, operation_id="saveProjectInfo")
async def save_project_info(req: SaveProjectInfoRequest) -> SaveResponse:
    """Save project metadata (COM, PRJ, ENG) to the active KDF file."""
    model = await require_model()
    from pykorf.core.log import flash_logs, get_logger

    logger = get_logger(__name__)
    kdf_path = await _sess.get_kdf_path()
    if not kdf_path:
        return SaveResponse(message="No model loaded.", logs=[])

    logs: list[StatusMessage] = []
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
        _sess.set_project_info_checked(True)
        await _sess.reload()
    for alert_type, message in flash_list:
        logs.append(StatusMessage(type=alert_type, message=message))
    return SaveResponse(message="Project info saved.", logs=logs)


@router.get("/pipes", response_model=ModelPipesResponse, operation_id="getPipes")
async def get_pipes() -> ModelPipesResponse:
    """Return list of pipe names for dropdowns."""
    model = await require_model()
    return ModelPipesResponse(pipes=pipe_names(model))


@router.post("/bulk-copy", response_model=BulkCopyResponse, operation_id="bulkCopy")
async def bulk_copy(req: BulkCopyRequest) -> BulkCopyResponse:
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


@router.get("/pipe-criteria", response_model=PipeCriteriaResponse, operation_id="getPipeCriteria")
async def get_pipe_criteria() -> PipeCriteriaResponse:
    """Get pipe criteria data for the criteria table."""
    model = await require_model()
    from pykorf.app.operation.integration.sizing_criteria import FLUID_LABELS, all_codes_by_type

    kdf_path = await _sess.get_kdf_path()
    pipes = _get_pipes_list(model)
    codes = all_codes_by_type()
    existing = _map_pipecriteria_entry(model, pipes)
    pipe_criteria_values = _precompute_criteria_values(model, pipes, codes)
    pipe_calcs = _compute_pipe_calcs(model, pipes)
    pipe_criteria_violations = _compute_criteria_violations(pipe_calcs, pipe_criteria_values)

    valid_indices = {idx for idx, _ in pipes}
    idx_justifications = (
        get_justifications(kdf_path, valid_pipe_indices=valid_indices) if kdf_path else {}
    )
    idx_to_name = {idx: model.pipes[idx].name for idx in valid_indices if idx in model.pipes}
    justifications = {
        idx_to_name[idx]: text for idx, text in idx_justifications.items() if idx in idx_to_name
    }

    violation_summary = _compute_violation_summary(
        pipe_criteria_violations, justifications, existing
    )
    orphaned_justifications = _compute_orphaned_justifications(
        justifications, pipe_criteria_violations, existing
    )

    return PipeCriteriaResponse(
        kdf_path=str(kdf_path or ""),
        pipes=pipes,
        existing=existing,
        codes=codes,
        fluid_labels=FLUID_LABELS,
        pipe_criteria_values=pipe_criteria_values,
        pipe_calcs=pipe_calcs,
        pipe_criteria_violations=pipe_criteria_violations,
        units_data=_load_units_data(),
        justifications=justifications,
        orphaned_justifications=orphaned_justifications,
        violation_summary=violation_summary,
    )


@router.post("/pipe-criteria", response_model=SetCriteriaResponse, operation_id="setPipeCriteria")
async def set_pipe_criteria(req: SetPipeCriteriaRequest) -> SetCriteriaResponse:
    """Apply criteria to pipe SIZ parameters."""
    model = await require_model()

    pipes = _get_pipes_list(model)

    criteria_dict = {k: {"state": v.state, "criteria": v.criteria} for k, v in req.criteria.items()}

    result = _handle_set_criteria(model, pipes, criteria_dict)
    if await _sess.has_model():
        model.save()
        await _sess.reload()

    return result


@router.post(
    "/pipe-criteria/predict",
    response_model=PredictCriteriaResponse,
    operation_id="predictPipeCriteria",
)
async def predict_criteria(_req: PredictCriteriaRequest) -> PredictCriteriaResponse:
    """Auto-predict state and criteria for all pipes."""
    model = await require_model()

    pipes = _get_pipes_list(model)
    existing = _map_pipecriteria_entry(model, pipes)

    _, predict_result = _handle_predict_action(model, pipes, existing)
    return predict_result


@router.post(
    "/pipe-criteria/justification",
    response_model=JustificationSaveResponse,
    operation_id="savePipeJustification",
)
async def save_justification(req: JustificationRequest) -> JustificationSaveResponse:
    """Save or clear a justification for a pipe criteria violation."""
    model = await require_model()
    kdf_path = await _sess.get_kdf_path()
    if not kdf_path:
        raise HTTPException(status_code=400, detail="No KDF file loaded")

    if req.pipe_idx not in model.pipes or req.pipe_idx == 0:
        raise HTTPException(status_code=400, detail=f"Pipe index {req.pipe_idx} not found")

    valid_indices = {idx for idx, _ in _get_pipes_list(model)}
    if req.pipe_idx not in valid_indices:
        raise HTTPException(status_code=400, detail=f"Pipe index {req.pipe_idx} not found")

    justifications = get_justifications(kdf_path, valid_pipe_indices=valid_indices)
    if req.justification.strip():
        justifications[req.pipe_idx] = req.justification
    else:
        justifications.pop(req.pipe_idx, None)
    set_justifications(kdf_path, justifications)

    idx_to_name = {idx: model.pipes[idx].name for idx in valid_indices}
    name_keyed = {
        idx_to_name[idx]: text for idx, text in justifications.items() if idx in idx_to_name
    }
    return JustificationSaveResponse(justifications=name_keyed, saved=True)


# --- Helper functions (ported from routes/pipe_criteria.py) ---


def _compute_violation_summary(
    pipe_criteria_violations: dict[str, dict],
    justifications: dict[str, str],
    existing: dict[str, dict],
) -> ViolationSummary:
    def _selected(pipe_name: str) -> CriteriaViolationsInfo | None:
        entry = existing.get(pipe_name)
        if entry is None or not entry.state or not entry.criteria:
            return None
        return pipe_criteria_violations.get(pipe_name, {}).get(f"{entry.state}:{entry.criteria}")

    selected: dict[str, CriteriaViolationsInfo | None] = {
        name: _selected(name) for name in pipe_criteria_violations
    }

    def _flag_count(info: CriteriaViolationsInfo) -> int:
        return sum(
            [
                info.dp_exceeds,
                info.vel_below_min,
                info.vel_above_max,
                info.rho_v2_below_min,
                info.rho_v2_above_max,
            ]
        )

    failing_pipes = {name for name, v in selected.items() if v is not None and v.overall == "FAIL"}
    justified = {p for p in failing_pipes if p in justifications}
    unjustified = failing_pipes - justified

    def _total_flags(pipes_set: set[str]) -> int:
        return sum(_flag_count(selected[p]) for p in pipes_set if selected[p] is not None)

    return ViolationSummary(
        total_pipes_with_violations=len(failing_pipes),
        total_violations=_total_flags(failing_pipes),
        justified_pipes=len(justified),
        justified_violations=_total_flags(justified),
        pipes_needing_justification=len(unjustified),
        violations_needing_justification=_total_flags(unjustified),
    )


def _compute_orphaned_justifications(
    justifications: dict[str, str],
    pipe_criteria_violations: dict[str, dict],
    existing: dict[str, dict],
) -> dict[str, str]:
    """Return justifications for pipes that are NOT currently failing criteria."""
    failing_pipes: set[str] = set()
    for name in pipe_criteria_violations:
        entry = existing.get(name)
        if entry is None or not entry.state or not entry.criteria:
            continue
        violations = pipe_criteria_violations.get(name, {}).get(f"{entry.state}:{entry.criteria}")
        if violations is not None and violations.overall == "FAIL":
            failing_pipes.add(name)

    return {name: text for name, text in justifications.items() if name not in failing_pipes}


def _get_pipes_list(model) -> list[tuple[int, str]]:
    return [
        (idx, model.pipes[idx].name)
        for idx in range(1, len(model.pipes) + 1)
        if is_real_pipe(model.pipes[idx])
    ]


def _build_prereqs(model: Model, kdf_path: Path) -> PrereqsResponse:
    from pykorf.app.api.schemas import ValidationIssue
    from pykorf.app.operation.config.config import (
        get_pms_excel_path,
        get_skip_sp_override,
        get_sp_overrides,
    )
    from pykorf.app.validation import categorize_issue

    raw_issues = model.validate()
    issues = [ValidationIssue(message=msg, category=categorize_issue(msg)) for msg in raw_issues]
    notes_ok = not any(
        "NOTES" in i.message
        or "missing line number" in i.message
        or "line number" in i.message.lower()
        for i in issues
    )
    validation_ok = len(issues) == 0
    pms_raw = get_pms_excel_path()
    pms_path = str(pms_raw) if pms_raw else ""
    pms_ok = bool(pms_path and Path(pms_path).is_file())
    skip_sp = get_skip_sp_override()
    sharepoint_ok = bool(get_sp_overrides()) if not skip_sp else True

    return PrereqsResponse(
        notes_ok=notes_ok,
        pms_ok=pms_ok,
        validation_ok=validation_ok,
        sharepoint_ok=sharepoint_ok,
        issues=issues,
        pms_path=pms_path,
    )


def _build_project_info(
    model, kdf_path, smart_defaults: SmartDefaultsResponse
) -> ProjectInfoResponse:
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
    project_info: dict[str, str] = {}
    for field, value in raw_values.items():
        if _is_korf_default(field, value):
            project_info[field] = getattr(smart_defaults, field, "")
        else:
            project_info[field] = value
    return ProjectInfoResponse(**project_info)


def _map_pipecriteria_entry(model, pipes) -> dict[str, PipeCriteriaEntry]:
    """Map existing pipe criteria from the model to a dict of PipeCriteriaEntry for the given pipes.

    Args:
        model: The Model instance containing pipes.
        pipes: List of (index, pipe_name) tuples.

    Returns:
        Dict mapping pipe name to PipeCriteriaEntry(state, criteria).
        Pipes without a criteria_code in SIZ[0] are omitted.
    """
    from pykorf.app.operation.integration.sizing_criteria import code_to_state

    pipe_by_name = _build_pipe_lookup(model)
    result: dict[str, PipeCriteriaEntry] = {}
    for _, pipe_name in pipes:
        pipe = pipe_by_name.get(pipe_name)
        if pipe is None:
            continue
        code = pipe.criteria_code
        if not code:
            continue
        state = code_to_state(code)
        if state:
            result[pipe_name] = PipeCriteriaEntry(state=state, criteria=code)
    return result


def _build_pipe_lookup(model):
    return {
        model.pipes[i].name: model.pipes[i]
        for i in range(1, len(model.pipes) + 1)
        if is_real_pipe(model.pipes[i])
    }


def _precompute_criteria_values(model, pipes, codes) -> dict[str, dict[str, CriteriaValuesInfo]]:
    from pykorf.app.operation.integration.sizing_criteria import lookup_criteria

    result: dict[str, dict[str, CriteriaValuesInfo]] = {}
    for _, pipe_name in pipes:
        pipe = _get_pipe_by_name(model, pipe_name)
        if pipe is None:
            result[pipe_name] = {}
            continue
        size_inch, pressure_barg = _get_pipe_size_and_pressure(pipe)
        pipe_vals: dict[str, CriteriaValuesInfo] = {}
        for state, code_list in codes.items():
            for code, _ in code_list:
                vals = lookup_criteria(state, code, size_inch, pressure_barg)
                if vals is not None:
                    pipe_vals[f"{state}:{code}"] = CriteriaValuesInfo(
                        max_dp=vals.max_dp,
                        max_vel=vals.max_vel,
                        min_vel=vals.min_vel,
                        rho_v2_min=vals.rho_v2_min,
                        rho_v2_max=vals.rho_v2_max,
                    )
        result[pipe_name] = pipe_vals
    return result


def _compute_pipe_calcs(model, pipes) -> dict[str, PipeCalcInfo]:
    lookup = _build_pipe_lookup(model)
    result: dict[str, PipeCalcInfo] = {}
    for _, name in pipes:
        pipe = lookup.get(name)
        if pipe is None:
            result[name] = PipeCalcInfo()
            continue
        vel_list = pipe.velocity
        dp = pipe.pressure_drop_per_100m
        result[name] = PipeCalcInfo(
            dp_calc=dp if dp else None,
            vel_calc=vel_list[0] if vel_list else None,
            rho_v2_calc=pipe.rho_v2,
            length_m=pipe.length_m,
            line_size=pipe.format_line_size(),
        )
    return result


def _compute_criteria_violations(
    pipe_calcs: dict[str, PipeCalcInfo],
    pipe_criteria_values: dict[str, dict[str, CriteriaValuesInfo]],
) -> dict[str, dict[str, CriteriaViolationsInfo]]:
    """Compute criteria violations for each pipe and criteria combination.

    Args:
        pipe_calcs: Precomputed calculated values for each pipe
        pipe_criteria_values: Precomputed criteria limits for each pipe/criteria combo

    Returns:
        Dict mapping pipe name -> criteria key -> violation flags
    """
    result: dict[str, dict[str, CriteriaViolationsInfo]] = {}
    for pipe_name, calcs in pipe_calcs.items():
        pipe_violations: dict[str, CriteriaViolationsInfo] = {}
        criteria_dict = pipe_criteria_values.get(pipe_name, {})
        for crit_key, crit_vals in criteria_dict.items():
            dp_calc = calcs.dp_calc
            vel_calc = calcs.vel_calc
            rho_v2_calc = calcs.rho_v2_calc

            dp_exceeds = False
            if dp_calc is not None and crit_vals.max_dp is not None:
                dp_exceeds = dp_calc > crit_vals.max_dp

            vel_below_min = False
            if vel_calc is not None and crit_vals.min_vel > 0:
                vel_below_min = vel_calc < crit_vals.min_vel

            vel_above_max = False
            if vel_calc is not None and crit_vals.max_vel is not None:
                vel_above_max = vel_calc > crit_vals.max_vel

            rho_v2_below_min = False
            if rho_v2_calc is not None and crit_vals.rho_v2_min is not None:
                rho_v2_below_min = rho_v2_calc < crit_vals.rho_v2_min

            rho_v2_above_max = False
            if rho_v2_calc is not None and crit_vals.rho_v2_max is not None:
                rho_v2_above_max = rho_v2_calc > crit_vals.rho_v2_max

            overall = "PASS"
            if dp_exceeds or vel_below_min or vel_above_max or rho_v2_below_min or rho_v2_above_max:
                overall = "FAIL"

            pipe_violations[crit_key] = CriteriaViolationsInfo(
                dp_exceeds=dp_exceeds,
                vel_below_min=vel_below_min,
                vel_above_max=vel_above_max,
                rho_v2_below_min=rho_v2_below_min,
                rho_v2_above_max=rho_v2_above_max,
                overall=overall,
            )
        result[pipe_name] = pipe_violations
    return result


@cache
def _load_units_data() -> dict[str, dict[str, UnitConversionInfo]]:
    import json

    from pykorf.core.reports.unit_converter import UNITS_JSON_PATH

    if UNITS_JSON_PATH.exists():
        with open(UNITS_JSON_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _get_pipe_by_name(model, pipe_name):
    return _build_pipe_lookup(model).get(pipe_name)


def _get_pipe_size_and_pressure(pipe):
    try:
        size_inch = float(pipe.diameter_inch) if pipe.diameter_inch else None
    except (ValueError, TypeError):
        size_inch = None
    pressures = pipe.pressure or []
    try:
        pressure_barg = pressures[0] / 100.0 if pressures else None
    except (IndexError, TypeError):
        pressure_barg = None
    return size_inch, pressure_barg


def _handle_set_criteria(model, pipes, existing: dict[str, dict[str, str]]) -> SetCriteriaResponse:
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
    return SetCriteriaResponse(applied=applied, skipped=skipped)


def _handle_predict_action(
    model, pipes, existing: dict[str, PipeCriteriaEntry]
) -> tuple[dict[str, PipeCriteriaEntry], PredictCriteriaResponse]:
    from pykorf.app.operation.integration.sizing_criteria import (
        predict_criteria as predict_criteria_code,
        predict_state,
    )

    predicted = {
        k: PipeCriteriaEntry(state=v.state, criteria=v.criteria) for k, v in existing.items()
    }
    filled_state_total = 0
    filled_criteria_total = 0
    errors: list[str] = []
    pipe_by_name = _build_pipe_lookup(model)

    for _, pipe_name in pipes:
        try:
            pipe = pipe_by_name.get(pipe_name)
            if pipe is None:
                continue
            current = predicted.get(pipe_name, PipeCriteriaEntry())
            state = current.state
            criteria = current.criteria
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
                    predicted_crit = predict_criteria_code(state, pipe_name) or ""
                    if predicted_crit:
                        criteria = predicted_crit
                        filled_criteria_total += 1
                except Exception as exc:
                    errors.append(f"{pipe_name} criteria: {exc}")
            if state or criteria:
                predicted[pipe_name] = PipeCriteriaEntry(state=state, criteria=criteria)
        except Exception as exc:
            errors.append(f"{pipe_name}: {exc}")

    predict_result = PredictCriteriaResponse(
        predicted=predicted,
        filled_state=filled_state_total,
        filled_criteria=filled_criteria_total,
        errors=errors,
    )
    return predicted, predict_result
