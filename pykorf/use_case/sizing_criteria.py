"""Sizing criteria loader from TOML reference files.

Provides helpers for loading and querying the three sizing criteria tables:
  - sizing_criteria_liquid.toml
  - sizing_criteria_gas.toml
  - sizing_criteria_twophase.toml
"""

from __future__ import annotations

import tomllib
from pathlib import Path

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


def lookup_criteria(
    fluid_type: str,
    code: str,
    pipe_size_inch: float = 9999.0,
    pressure_barg: float = 9999.0,
) -> dict | None:
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
        Matching criteria dict, or None if the code is not found.
    """
    entries = [e for e in load_criteria(fluid_type) if e["code"] == code]
    if not entries:
        return None

    if fluid_type == "gas":
        entries_sorted = sorted(entries, key=lambda e: e.get("pressure", 9999))
        for entry in entries_sorted:
            if pressure_barg <= entry.get("pressure", 9999):
                return entry
        return entries_sorted[-1]
    else:
        entries_sorted = sorted(entries, key=lambda e: e.get("line_size", 9999))
        for entry in entries_sorted:
            if pipe_size_inch <= entry.get("line_size", 9999):
                return entry
        return entries_sorted[-1]
