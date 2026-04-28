"""Sidecar .pykorf file — persists user-defined metadata alongside a .kdf file.

The .pykorf file lives in the same directory as the .kdf file and shares
its stem (e.g. model.kdf → model.pykorf).  It is a UTF-8 JSON file with
a top-level version field so future keys can be added without breaking reads.

Current schema::

    {
      "version": 1,
      "justifications": {
        "L1": "Approved by engineering lead",
        "L2": "Temporary design exception",
        ...
      }
    }
"""

from __future__ import annotations

import json
from pathlib import Path

from pykorf.app.exceptions import UseCaseError

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
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise UseCaseError(f"Failed to load {path.name}: {e}") from e


def _save(kdf_path: Path, data: dict) -> None:
    data["version"] = _VERSION
    path = get_pykorf_path(kdf_path)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        raise UseCaseError(f"Failed to save {path.name}: {e}") from e


def get_justifications(kdf_path: Path) -> dict[str, str]:
    """Load justifications from the .pykorf sidecar.

    Args:
        kdf_path: Path to the .kdf model file.

    Returns:
        Dict mapping pipe name to justification text.
        Empty dict if no sidecar exists or no justifications key.
    """
    return _load(kdf_path).get("justifications", {})


def set_justifications(kdf_path: Path, justifications: dict[str, str]) -> None:
    """Save justifications to the .pykorf sidecar.

    Merges into any existing .pykorf data so other sections are preserved.

    Args:
        kdf_path: Path to the .kdf model file.
        justifications: Dict mapping pipe name to justification text.
    """
    data = _load(kdf_path)
    data["justifications"] = justifications
    _save(kdf_path, data)
