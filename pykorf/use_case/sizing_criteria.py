"""Sizing criteria loader from TOML reference files.

Provides helpers for loading and querying the three sizing criteria tables:
  - sizing_criteria_liquid.toml
  - sizing_criteria_gas.toml
  - sizing_criteria_twophase.toml
"""

from __future__ import annotations

import tomllib
from functools import cache
from pathlib import Path
from typing import NamedTuple


class CriteriaValues(NamedTuple):
    """Resolved sizing criteria bounds for a single pipe lookup.

    All values use SI/engineering units as stored in the TOML tables.
    None means the criterion is not specified / does not apply.
    """

    max_dp: float | None  # kPa/100m; None = no dP criterion
    max_vel: float | None  # m/s; None = no max velocity criterion
    min_vel: float  # m/s
    rho_v2_min: float | None = None  # Pa; None = not applicable
    rho_v2_max: float | None = None  # Pa; None = not applicable


_CRITERIA_DIR = Path(__file__).parent.parent / "reports"

_FILES: dict[str, str] = {
    "liquid": "sizing_criteria_liquid.toml",
    "gas": "sizing_criteria_gas.toml",
    "two_phase": "sizing_criteria_twophase.toml",
}

FLUID_LABELS: dict[str, str] = {
    "liquid": "Liquid",
    "gas": "Gas / Steam",
    "two_phase": "Two-Phase",
}


@cache
def load_criteria(fluid_type: str) -> list[dict]:
    """Return all entries for a fluid type.

    Args:
        fluid_type: One of "liquid", "gas", "two_phase".

    Returns:
        List of criteria dicts as stored in the TOML file.
    """
    path = _CRITERIA_DIR / _FILES[fluid_type]
    with open(path, "rb") as f:
        return tomllib.load(f)["criteria"]


def get_codes(fluid_type: str) -> list[tuple[str, str]]:
    """Return unique (code, label) pairs suitable for a <select> dropdown.

    Args:
        fluid_type: One of "liquid", "gas", "two_phase".

    Returns:
        List of (code, "code — service description") in first-occurrence order.
    """
    seen: dict[str, str] = {}
    for entry in load_criteria(fluid_type):
        code = entry["code"]
        if code not in seen:
            seen[code] = entry["service"]
    return [(code, f"{code} \u2014 {svc}") for code, svc in seen.items()]


def all_codes_by_type() -> dict[str, list[tuple[str, str]]]:
    """Return {fluid_type: [(code, label), ...]} for all three types.

    Returns:
        Dict with keys "liquid", "gas", "two_phase".
    """
    return {ft: get_codes(ft) for ft in _FILES}


@cache
def code_to_state(code: str) -> str | None:
    """Return the fluid type that owns *code*, or None if not found.

    Checks all three criteria tables in order: liquid → gas → two_phase.

    Args:
        code: Sizing criteria code (e.g. ``"P-DIS"``, ``"P-SUC-BUB"``).

    Returns:
        One of ``"liquid"``, ``"gas"``, ``"two_phase"``, or ``None``.
    """
    for fluid_type in _FILES:
        for entry in load_criteria(fluid_type):
            if entry["code"] == code:
                return fluid_type
    return None


def predict_state(liquid_fractions: list[float]) -> str | None:
    """Predict fluid state from liquid fraction values (``Pipe.LF``).

    Liquid fraction is 0.0 (all vapour) to 1.0 (all liquid).  The average
    across all cases is used so a multi-case pipe is treated consistently.

    Rules:
      - ``lf >= 0.99`` → ``"liquid"``
      - ``lf <= 0.01`` → ``"gas"``
      - otherwise      → ``"two_phase"``

    Args:
        liquid_fractions: List of per-case LF values from ``Pipe.LF`` (0.0-1.0).
            Empty or all-None lists return ``None``.

    Returns:
        ``"liquid"``, ``"gas"``, ``"two_phase"``, or ``None`` if undetermined.
    """
    valid = [v for v in liquid_fractions if v is not None]
    if not valid:
        return None
    avg_lf = sum(valid) / len(valid)
    if avg_lf >= 0.99:
        return "liquid"
    if avg_lf <= 0.01:
        return "gas"
    return "two_phase"


def predict_criteria(fluid_type: str, pipe_name: str) -> str | None:
    """Predict the best sizing criteria code for a pipe.

    Args:
        fluid_type: One of ``"liquid"``, ``"gas"``, ``"two_phase"``.
        pipe_name: Pipe name from the KDF model.

    Returns:
        Criteria code string, or ``None`` if no prediction can be made.
    """
    # TODO: implement heuristic matching — e.g. infer service from pipe tag
    #       convention (P- prefix → pump line, C- → compressor, etc.) and
    #       map to a default code per fluid_type.
    return None


def _entry_to_criteria(entry: dict) -> CriteriaValues:
    """Convert a raw TOML entry dict to a CriteriaValues NamedTuple."""
    dp_raw = entry["dp"][1]
    dp_max: float | None = None if dp_raw == 0.0 else float(dp_raw)

    vel_raw = entry["vel"][1]
    vel_max: float | None = None if vel_raw == 0.0 else float(vel_raw)

    vel_min = entry["vel"][0]

    raw = entry.get("rho_v2")
    if raw is None:
        rho_v2_min, rho_v2_max = None, None
    elif isinstance(raw, list):
        # Two-phase: [min, max]
        rho_v2_min, rho_v2_max = float(raw[0]), float(raw[1])
    else:
        # Gas: single upper-limit value; 0 = not specified
        v = float(raw)
        rho_v2_min, rho_v2_max = (0.0, v) if v > 0.0 else (None, None)

    return CriteriaValues(
        max_dp=dp_max,
        max_vel=vel_max,
        min_vel=vel_min,
        rho_v2_min=rho_v2_min,
        rho_v2_max=rho_v2_max,
    )


@cache
def lookup_criteria(
    fluid_type: str,
    code: str,
    pipe_size_inch: float = 9999.0,
    pressure_barg: float = 9999.0,
) -> CriteriaValues | None:
    """Find the best matching criteria entry for a pipe.

    For liquid/two_phase: match is determined by ``line_size`` (first entry
    where ``pipe_size_inch <= line_size``).
    For gas: match is determined by ``pressure`` (first entry where
    ``pressure_barg <= pressure``).

    Args:
        fluid_type: One of "liquid", "gas", "two_phase".
        code: Criteria code string (e.g. "P-SUC-BUB").
        pipe_size_inch: Nominal pipe diameter in inches (default 9999 = no limit).
        pressure_barg: Operating pressure in barg (default 9999 = no limit).

    Returns:
        CriteriaValues(max_dp, max_vel, min_vel), or None if code not found.
    """
    entries = [e for e in load_criteria(fluid_type) if e["code"] == code]
    if not entries:
        return None

    if fluid_type == "gas":
        entries_sorted = sorted(entries, key=lambda e: e.get("pressure", 9999))
        for entry in entries_sorted:
            if pressure_barg <= entry.get("pressure", 9999):
                return _entry_to_criteria(entry)
        return _entry_to_criteria(entries_sorted[-1])
    else:
        entries_sorted = sorted(entries, key=lambda e: e.get("line_size", 9999))
        for entry in entries_sorted:
            if pipe_size_inch <= entry.get("line_size", 9999):
                return _entry_to_criteria(entry)
        return _entry_to_criteria(entries_sorted[-1])
