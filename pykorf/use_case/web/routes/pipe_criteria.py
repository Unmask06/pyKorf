"""Pipe Sizing Criteria route: /model/pipe-criteria."""

from __future__ import annotations

from flask import Blueprint, render_template, request

from pykorf.use_case.web import session as _sess
from pykorf.use_case.web.helpers import is_redirect, require_model

bp = Blueprint("pipe_criteria", __name__)


@bp.route("/model/pipe-criteria", methods=["GET", "POST"])
def pipe_criteria():
    """Render and handle the Pipe Sizing Criteria assignment table."""
    model = require_model()
    if is_redirect(model):
        return model

    from pykorf.use_case.pykorf_file import get_pipe_criteria, set_pipe_criteria
    from pykorf.use_case.sizing_criteria import (
        FLUID_LABELS,
        all_codes_by_type,
        lookup_criteria,
        predict_criteria,
        predict_state,
    )

    kdf_path = _sess.get_kdf_path()

    # Build pipe list: [(index, name), ...]
    pipes = [
        (idx, model.pipes[idx].name)
        for idx in range(1, model.num_pipes + 1)
        if model.pipes[idx].name
    ]

    codes = all_codes_by_type()   # {fluid_type: [(code, label), ...]}
    existing = get_pipe_criteria(kdf_path) if kdf_path else {}
    result = None
    set_result = None
    predict_result = None

    if request.method == "POST":
        action = request.form.get("action", "save_criteria")

        if action == "predict":
            predicted = dict(existing)
            filled = 0
            for _, pipe_name in pipes:
                pipe = next(
                    (model.pipes[i] for i in range(1, model.num_pipes + 1)
                     if model.pipes[i].name == pipe_name),
                    None,
                )
                if pipe is None:
                    continue

                current = predicted.get(pipe_name, {})
                state = current.get("state", "")
                criteria = current.get("criteria", "")

                # Predict state from LF if not already set
                if not state:
                    try:
                        lf_values = pipe.get_fluid().lf or []
                        state = predict_state(lf_values) or ""
                    except Exception:
                        state = ""

                # Predict criteria if not already set
                if not criteria and state:
                    criteria = predict_criteria(state, pipe_name) or ""

                if state or criteria:
                    if state != current.get("state", "") or criteria != current.get("criteria", ""):
                        filled += 1
                    predicted[pipe_name] = {"state": state, "criteria": criteria}

            existing = predicted
            predict_result = {"filled": filled}
            # Do not auto-save — user reviews then clicks Save
            return render_template(
                "pipe_criteria.html",
                kdf_path=str(kdf_path or ""),
                pipes=pipes,
                existing=existing,
                codes=codes,
                fluid_labels=FLUID_LABELS,
                result=result,
                set_result=set_result,
                predict_result=predict_result,
            )

        updated: dict[str, dict] = {}
        for _, pipe_name in pipes:
            state = (request.form.get(f"state_{pipe_name}") or "").strip()
            criteria = (request.form.get(f"criteria_{pipe_name}") or "").strip()
            if state or criteria:
                updated[pipe_name] = {"state": state, "criteria": criteria}

        if kdf_path:
            set_pipe_criteria(kdf_path, updated)
        existing = updated
        result = {"saved": len(updated)}

        if action == "set_criteria":
            from pykorf.elements.pipe import Pipe

            applied = 0
            skipped: list[str] = []
            for _, pipe_name in pipes:
                saved = existing.get(pipe_name, {})
                state = saved.get("state", "")
                code = saved.get("criteria", "")
                if not state or not code:
                    continue

                pipe = next(
                    (model.pipes[i] for i in range(1, model.num_pipes + 1)
                     if model.pipes[i].name == pipe_name),
                    None,
                )
                if pipe is None:
                    skipped.append(pipe_name)
                    continue

                # Determine pipe size and pressure for lookup
                try:
                    size_inch = float(pipe.diameter_inch or 9999)
                except (ValueError, TypeError):
                    size_inch = 9999.0

                pressures = pipe.pressure or []
                try:
                    pressure_barg = pressures[0] / 100.0 if pressures else 9999.0
                except (IndexError, TypeError):
                    pressure_barg = 9999.0

                entry = lookup_criteria(state, code, size_inch, pressure_barg)
                if entry is None:
                    skipped.append(pipe_name)
                    continue

                dp_max = entry["dp"][1] if entry["dp"][1] != 0.0 else 9999.0
                vel_max = entry["vel"][1] if entry["vel"][1] != 0.0 else 9999.0
                vel_min = entry["vel"][0]

                siz_values = ["", dp_max, "kPa/100m", vel_max, vel_min, 120, 10, "m/s"]
                model.set_params(pipe_name, {Pipe.SIZ: siz_values})
                applied += 1

            set_result = {"applied": applied, "skipped": skipped}

    return render_template(
        "pipe_criteria.html",
        kdf_path=str(kdf_path or ""),
        pipes=pipes,
        existing=existing,
        codes=codes,
        fluid_labels=FLUID_LABELS,
        result=result,
        set_result=set_result,
    )
