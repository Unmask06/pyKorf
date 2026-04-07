"""Pipe Sizing Criteria route: /model/pipe-criteria."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Blueprint, render_template, request

from pykorf.log import get_logger
from pykorf.use_case.web import session as _sess
from pykorf.use_case.web.helpers import is_redirect, require_model

if TYPE_CHECKING:
    from pathlib import Path

    from pykorf.elements.pipe import Pipe
    from pykorf.model import Model

logger = get_logger(__name__)
bp = Blueprint("pipe_criteria", __name__)


def _get_pipes_list(model: Model) -> list[tuple[int, str]]:
    """Build pipe list, excluding dummy pipes (names starting with 'd')."""
    return [
        (idx, model.pipes[idx].name)
        for idx in range(1, model.num_pipes + 1)
        if model.pipes[idx].name and not model.pipes[idx].name.startswith("d")
    ]


def _build_pipe_lookup(model: Model) -> dict[str, Pipe]:
    """Build a name→pipe lookup to avoid O(n²) scans, excluding dummy pipes."""
    return {
        model.pipes[i].name: model.pipes[i]
        for i in range(1, model.num_pipes + 1)
        if model.pipes[i].name and not model.pipes[i].name.startswith("d")
    }


def _predict_for_pipe(
    pipe_name: str,
    pipe: Pipe,
    predicted: dict[str, dict],
    errors: list[str],
) -> tuple[int, int]:
    """Predict state and criteria for a single pipe. Returns (filled_state, filled_criteria)."""
    from pykorf.use_case.sizing_criteria import predict_criteria, predict_state

    filled_state = 0
    filled_criteria = 0
    current = predicted.get(pipe_name, {})
    state = current.get("state", "")
    criteria = current.get("criteria", "")

    # Step 1 — predict state from liquid fraction (LF)
    if not state:
        try:
            fluid = pipe.get_fluid()
            raw_lf = fluid.lf
            # get_values() returns list[float] | None, never a single float
            lf_values: list[float] = raw_lf if isinstance(raw_lf, list) else []
            logger.debug(
                "predict_state_debug",
                pipe_name=pipe_name,
                raw_lf=raw_lf,
                raw_lf_type=type(raw_lf).__name__ if raw_lf is not None else "None",
                lf_values=lf_values,
                lf_values_len=len(lf_values),
                has_lf_data=bool(lf_values),
            )
            predicted_state = predict_state(lf_values) or ""
            logger.debug(
                "predict_state_result",
                pipe_name=pipe_name,
                predicted_state=predicted_state,
                will_fill=bool(predicted_state),
            )
            if predicted_state:
                state = predicted_state
                filled_state += 1
        except Exception as exc:
            logger.debug("predict_state_error", pipe_name=pipe_name, error=str(exc))
            errors.append(f"{pipe_name} state: {exc}")

    # Step 2 — predict criteria code from state
    if not criteria and state:
        try:
            predicted_crit = predict_criteria(state, pipe_name) or ""
            if predicted_crit:
                criteria = predicted_crit
                filled_criteria += 1
        except Exception as exc:
            errors.append(f"{pipe_name} criteria: {exc}")

    if state or criteria:
        predicted[pipe_name] = {"state": state, "criteria": criteria}

    return filled_state, filled_criteria


def _handle_predict_action(
    model: Model,
    pipes: list[tuple[int, str]],
    existing: dict[str, dict],
) -> tuple[dict[str, dict], dict]:
    """Handle the predict action: auto-fill state and criteria for all pipes."""
    logger.debug(
        "predict_action_start",
        total_pipes=len(pipes),
        existing_entries=len(existing),
    )
    predicted = {k: dict(v) for k, v in existing.items()}
    filled_state_total = 0
    filled_criteria_total = 0
    errors: list[str] = []

    pipe_by_name = _build_pipe_lookup(model)

    for idx, pipe_name in pipes:
        try:
            pipe = pipe_by_name.get(pipe_name)
            if pipe is None:
                logger.debug("predict_pipe_not_found", pipe_name=pipe_name)
                continue

            logger.debug("predict_processing_pipe", pipe_name=pipe_name, pipe_index=idx)
            fs, fc = _predict_for_pipe(pipe_name, pipe, predicted, errors)
            filled_state_total += fs
            filled_criteria_total += fc

        except Exception as exc:
            logger.debug("predict_pipe_exception", pipe_name=pipe_name, error=str(exc))
            errors.append(f"{pipe_name}: {exc}")

    predict_result = {
        "filled_state": filled_state_total,
        "filled_criteria": filled_criteria_total,
        "errors": errors,
    }
    logger.debug(
        "predict_action_complete",
        filled_state_total=filled_state_total,
        filled_criteria_total=filled_criteria_total,
        errors_count=len(errors),
    )

    return predicted, predict_result


def _extract_form_data(pipes: list[tuple[int, str]]) -> dict[str, dict]:
    """Extract state and criteria from form data for all pipes."""
    updated: dict[str, dict] = {}
    for _, pipe_name in pipes:
        state = (request.form.get(f"state_{pipe_name}") or "").strip()
        criteria = (request.form.get(f"criteria_{pipe_name}") or "").strip()
        if state or criteria:
            updated[pipe_name] = {"state": state, "criteria": criteria}
    return updated


def _get_pipe_by_name(model: Model, pipe_name: str) -> Pipe | None:
    """Find a pipe by name in the model."""
    for i in range(1, model.num_pipes + 1):
        if model.pipes[i].name == pipe_name:
            return model.pipes[i]
    return None


def _get_pipe_size_and_pressure(pipe: Pipe) -> tuple[float, float]:
    """Extract size (inch) and pressure (barg) from a pipe."""
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


def _apply_criteria_to_pipe(
    model: Model,
    pipe_name: str,
    state: str,
    code: str,
    skipped: list[str],
) -> bool:
    """Apply sizing criteria to a single pipe. Returns True if applied, False if skipped."""
    from pykorf.use_case.sizing_criteria import lookup_criteria

    pipe = _get_pipe_by_name(model, pipe_name)
    if pipe is None:
        logger.debug("apply_criteria_pipe_not_found", pipe_name=pipe_name)
        skipped.append(pipe_name)
        return False

    size_inch, pressure_barg = _get_pipe_size_and_pressure(pipe)
    vals = lookup_criteria(state, code, size_inch, pressure_barg)

    if vals is None:
        logger.debug(
            "apply_criteria_no_entry",
            pipe_name=pipe_name,
            state=state,
            code=code,
            size_inch=size_inch,
            pressure_barg=pressure_barg,
        )
        skipped.append(pipe_name)
        return False

    logger.info(
        "criteria_code_resolved",
        pipe=pipe_name,
        code=code,
        state=state,
        max_dp=vals.max_dp,
        min_vel=vals.min_vel,
        max_vel=vals.max_vel,
    )

    pipe.criteria_code = code
    pipe.max_dp_criteria = vals.max_dp
    pipe.max_velocity_criteria = vals.max_vel
    pipe.min_velocity_criteria = vals.min_vel

    logger.info(
        "apply_criteria_applied",
        pipe_name=pipe_name,
        state=state,
        code=code,
        max_dp=vals.max_dp,
        max_vel=vals.max_vel,
        min_vel=vals.min_vel,
        size_inch=size_inch,
        pressure_barg=pressure_barg,
    )
    return True


def _handle_set_criteria(
    model: Model,
    pipes: list[tuple[int, str]],
    existing: dict[str, dict],
) -> dict:
    """Apply saved criteria to pipe SIZ parameters."""
    logger.debug(
        "set_criteria_start",
        total_pipes=len(pipes),
        existing_entries=len(existing),
    )
    applied = 0
    skipped: list[str] = []

    for _, pipe_name in pipes:
        saved = existing.get(pipe_name, {})
        state = saved.get("state", "")
        code = saved.get("criteria", "")
        if not state or not code:
            logger.debug(
                "set_criteria_skipped_no_data",
                pipe_name=pipe_name,
                has_state=bool(state),
                has_code=bool(code),
            )
            continue

        if _apply_criteria_to_pipe(model, pipe_name, state, code, skipped):
            applied += 1

    logger.debug(
        "set_criteria_complete",
        applied=applied,
        skipped_count=len(skipped),
        skipped_pipes=skipped,
    )
    return {"applied": applied, "skipped": skipped}


def _seed_from_kdf(
    model: Model,
    pipes: list[tuple[int, str]],
    existing: dict[str, dict],
) -> dict[str, dict]:
    """Pre-fill *existing* from each pipe's SIZ[0] criteria code in the KDF.

    Only fills pipes that have no saved entry (or whose saved entry has both
    state and criteria empty).  This is non-destructive — user-saved data
    always takes priority.

    Args:
        model: Active model.
        pipes: List of (index, pipe_name) tuples.
        existing: Saved criteria dict (may be empty).

    Returns:
        Updated copy of *existing* with KDF-sourced entries merged in.
    """
    from pykorf.use_case.sizing_criteria import code_to_state

    pipe_by_name = _build_pipe_lookup(model)
    merged = {k: dict(v) for k, v in existing.items()}

    for _, pipe_name in pipes:
        saved = merged.get(pipe_name, {})
        if saved.get("state") or saved.get("criteria"):
            continue  # already populated — don't overwrite

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


def _precompute_criteria_values(
    model: Model,
    pipes: list[tuple[int, str]],
    codes: dict,
) -> dict[str, dict[str, dict]]:
    """Precompute CriteriaValues for every (pipe, state:code) combination.

    Returns a dict keyed by pipe name, each value being a dict of
    ``"state:code"`` → ``{"max_dp", "max_vel", "min_vel"}``.
    Used by the template to update read-only columns live in the browser.
    """
    from pykorf.use_case.sizing_criteria import lookup_criteria

    result: dict[str, dict[str, dict]] = {}
    for _, pipe_name in pipes:
        pipe = _get_pipe_by_name(model, pipe_name)
        if pipe is None:
            result[pipe_name] = {}
            continue
        size_inch, pressure_barg = _get_pipe_size_and_pressure(pipe)
        pipe_vals: dict[str, dict] = {}
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


def _compute_pipe_calcs(model: Model, pipes: list[tuple[int, str]]) -> dict:
    """Return per-pipe calculated results for display in the criteria table.

    Returns:
        { pipe_name: { "dp_calc": float|None, "vel_calc": float|None, "rho_v2_calc": float|None } }
    """
    lookup = _build_pipe_lookup(model)
    result: dict[str, dict] = {}
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


def _render_page(
    kdf_path: Path | str | None,
    pipes: list[tuple[int, str]],
    existing: dict[str, dict],
    codes: dict,
    pipe_criteria_values: dict,
    pipe_calcs: dict,
    set_result: dict | None = None,
    predict_result: dict | None = None,
):
    """Render the pipe criteria template with all required context."""
    from pykorf.use_case.sizing_criteria import FLUID_LABELS

    return render_template(
        "pipe_criteria.html",
        kdf_path=str(kdf_path or ""),
        pipes=pipes,
        existing=existing,
        codes=codes,
        fluid_labels=FLUID_LABELS,
        pipe_criteria_values=pipe_criteria_values,
        pipe_calcs=pipe_calcs,
        set_result=set_result,
        predict_result=predict_result,
    )


@bp.route("/model/pipe-criteria", methods=["GET", "POST"])
def pipe_criteria():
    """Render and handle the Pipe Sizing Criteria assignment table."""
    model = require_model()
    if is_redirect(model):
        return model

    from pykorf.use_case.pykorf_file import get_pipe_criteria, set_pipe_criteria
    from pykorf.use_case.sizing_criteria import all_codes_by_type

    kdf_path = _sess.get_kdf_path()
    pipes = _get_pipes_list(model)
    codes = all_codes_by_type()
    existing = get_pipe_criteria(kdf_path) if kdf_path else {}
    existing = _seed_from_kdf(model, pipes, existing)

    set_result = None
    predict_result = None

    if request.method == "POST":
        action = request.form.get("action", "set_criteria")
        logger.debug("pipe_criteria_post", action=action, kdf_path=str(kdf_path or ""))

        if action == "predict":
            logger.debug("predict_action_triggered")
            existing, predict_result = _handle_predict_action(model, pipes, existing)
            pipe_criteria_values = _precompute_criteria_values(model, pipes, codes)
            pipe_calcs = _compute_pipe_calcs(model, pipes)
            return _render_page(
                kdf_path,
                pipes,
                existing,
                codes,
                pipe_criteria_values,
                pipe_calcs,
                set_result,
                predict_result,
            )

        updated = _extract_form_data(pipes)

        if kdf_path:
            set_pipe_criteria(kdf_path, updated)
        existing = updated

        set_result = _handle_set_criteria(model, pipes, existing)
        if kdf_path:
            model.io.save(kdf_path)
            _sess.reload()

    pipe_criteria_values = _precompute_criteria_values(model, pipes, codes)
    pipe_calcs = _compute_pipe_calcs(model, pipes)
    return _render_page(
        kdf_path,
        pipes,
        existing,
        codes,
        pipe_criteria_values,
        pipe_calcs,
        set_result,
        predict_result,
    )
