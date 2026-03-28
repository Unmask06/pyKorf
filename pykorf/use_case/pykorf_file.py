"""Sidecar .pykorf file — persists user-defined metadata alongside a .kdf file.

The .pykorf file lives in the same directory as the .kdf file and shares
its stem (e.g. model.kdf → model.pykorf).  It is a UTF-8 JSON file with
a top-level version field so future keys can be added without breaking reads.

Current schema::

    {
      "version": 1,
      "pipe_criteria": {
        "L1": {"state": "liquid", "criteria": "P-SUC-BUB"},
        "L2": {"state": "gas",    "criteria": "GAS-GEN"},
        ...
      }
    }
"""

from __future__ import annotations

import json
from pathlib import Path

_VERSION = 1


def get_pykorf_path(kdf_path: Path) -> Path:
    """Return the .pykorf sidecar path for a given .kdf file.

    Args:
        kdf_path: Path to the .kdf model file.

    Returns:
        Path with same stem and directory, extension replaced by .pykorf.
    """
    return kdf_path.with_suffix(".pykorf")


def _load(kdf_path: Path) -> dict:
    path = get_pykorf_path(kdf_path)
    if not path.is_file():
        return {"version": _VERSION}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save(kdf_path: Path, data: dict) -> None:
    data["version"] = _VERSION
    path = get_pykorf_path(kdf_path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_pipe_criteria(kdf_path: Path) -> dict[str, dict]:
    """Load pipe → {state, criteria} mapping from the .pykorf sidecar.

    Args:
        kdf_path: Path to the .kdf model file.

    Returns:
        Dict mapping pipe name to {"state": str, "criteria": str}.
        Empty dict if no sidecar exists yet.
    """
    return _load(kdf_path).get("pipe_criteria", {})


def set_pipe_criteria(kdf_path: Path, criteria: dict[str, dict]) -> None:
    """Save pipe → {state, criteria} mapping to the .pykorf sidecar.

    Merges into any existing .pykorf data so other sections are preserved.

    Args:
        kdf_path: Path to the .kdf model file.
        criteria: Dict mapping pipe name to {"state": str, "criteria": str}.
    """
    data = _load(kdf_path)
    data["pipe_criteria"] = criteria
    _save(kdf_path, data)
