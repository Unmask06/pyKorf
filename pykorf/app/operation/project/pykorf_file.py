"""Sidecar .pykorf file — persists user-defined metadata alongside a .kdf file.

The .pykorf file lives in the same directory as the .kdf file and shares
its stem (e.g. model.kdf → model.pykorf).  It is a UTF-8 JSON file with
a top-level version field so future keys can be added without breaking reads.

Current schema (v2)::

    {
      "version": 2,
      "justifications": {
        "1": "Approved by engineering lead",
        "5": "Temporary design exception",
        ...
      }
    }

Justifications are keyed by **pipe index** (stable across renames).
Version 1 used pipe names as keys; migration to v2 happens automatically
on first load.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pykorf.app.exceptions import UseCaseError

_VERSION = 2

_logger = logging.getLogger(__name__)


def get_pykorf_path(kdf_path: Path) -> Path:
    """Return the .pykorf sidecar path for a given .kdf file.

    Args:
        kdf_path: Path to the .kdf model file.

    Returns:
        Path with same stem and directory, extension replaced by .pykorf.
    """
    return kdf_path.with_suffix(".pykorf")


def _migrate_v1_to_v2(data: dict, kdf_path: Path) -> dict:
    """Migrate justifications from name-keyed (v1) to idx-keyed (v2).

    Resolves each pipe name to its current index in the KDF file.
    Justifications for pipes that no longer exist are dropped.
    """
    justifications = data.get("justifications", {})
    if not justifications:
        return data

    all_numeric = all(isinstance(k, str) and k.isdigit() for k in justifications)
    if all_numeric:
        return data

    try:
        from pykorf.core.model import Model

        model = Model(kdf_path)
        name_to_idx: dict[str, int] = {
            pipe.name: idx for idx, pipe in model.pipes.items() if idx != 0 and pipe.name
        }
    except Exception:
        _logger.warning("Could not load KDF for justification migration; keeping raw keys")
        return data

    migrated: dict[str, str] = {}
    for key, value in justifications.items():
        if isinstance(key, str) and key.isdigit():
            migrated[key] = value
        elif key in name_to_idx:
            migrated[str(name_to_idx[key])] = value
        else:
            _logger.info("Dropping orphaned justification for pipe '%s' (not found in KDF)", key)

    data["justifications"] = migrated
    return data


def _load(kdf_path: Path) -> dict:
    path = get_pykorf_path(kdf_path)
    if not path.is_file():
        return {"version": _VERSION}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise UseCaseError(f"Failed to load {path.name}: {e}") from e

    file_version = data.get("version", 1)
    if file_version < 2:
        data = _migrate_v1_to_v2(data, kdf_path)
        data["version"] = _VERSION
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass
    return data


def _save(kdf_path: Path, data: dict) -> None:
    data["version"] = _VERSION
    path = get_pykorf_path(kdf_path)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        raise UseCaseError(f"Failed to save {path.name}: {e}") from e


def get_justifications(
    kdf_path: Path, valid_pipe_indices: set[int] | None = None
) -> dict[int, str]:
    """Load justifications from the .pykorf sidecar.

    Args:
        kdf_path: Path to the .kdf model file.
        valid_pipe_indices: If provided, justifications for pipe indices not
            in this set are pruned (removed from the returned dict **and**
            persisted back to disk so the file stays clean).

    Returns:
        Dict mapping pipe index to justification text.
        Empty dict if no sidecar exists or no justifications key.
    """
    data = _load(kdf_path)
    raw: dict = data.get("justifications", {})
    result: dict[int, str] = {}
    for k, v in raw.items():
        if isinstance(k, str) and k.isdigit():
            result[int(k)] = v

    if valid_pipe_indices is not None:
        pruned = {idx: text for idx, text in result.items() if idx in valid_pipe_indices}
        if len(pruned) != len(result):
            dropped = set(result) - set(pruned)
            _logger.info("Pruned justifications for missing pipe indices: %s", dropped)
            result = pruned
            data["justifications"] = {str(k): v for k, v in result.items()}
            try:
                _save(kdf_path, data)
            except UseCaseError:
                pass

    return result


def set_justifications(kdf_path: Path, justifications: dict[int, str]) -> None:
    """Save justifications to the .pykorf sidecar.

    Merges into any existing .pykorf data so other sections are preserved.

    Args:
        kdf_path: Path to the .kdf model file.
        justifications: Dict mapping pipe index to justification text.
    """
    data = _load(kdf_path)
    data["justifications"] = {str(k): v for k, v in justifications.items()}
    _save(kdf_path, data)
