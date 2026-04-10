"""Single-user in-process model state for the local web UI.

No cookies, no sessions — the server holds exactly one model at a time,
matching how the terminal TUI works.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykorf import Model

_model: Model | None = None
_kdf_path: Path | None = None
_model_mtime: float | None = None
_lock = threading.Lock()


def load(model: Model, kdf_path: Path) -> None:
    """Store *model* as the active model.

    Args:
        model: Loaded KorfModel instance.
        kdf_path: Source .kdf file path.
    """
    global _model, _kdf_path, _model_mtime
    with _lock:
        _model = model
        _kdf_path = kdf_path
        _model_mtime = kdf_path.stat().st_mtime if kdf_path.exists() else None


def get_model() -> Model | None:
    """Return the active model, or ``None`` if none is loaded.

    Returns:
        Active KorfModel or None.
    """
    with _lock:
        return _model


def get_kdf_path() -> Path | None:
    """Return the active model's source path, or ``None``.

    Returns:
        Path to the .kdf file or None.
    """
    with _lock:
        return _kdf_path


def has_model() -> bool:
    """Return True if a model is currently loaded.

    Returns:
        True when a model is in memory.
    """
    with _lock:
        return _model is not None


def reload() -> None:
    """Re-parse the active KDF file and replace the in-memory model.

    Call this after any operation that writes the KDF to disk so the
    displayed state always matches what was actually persisted.
    Does nothing if no model is currently loaded.
    """
    global _model, _model_mtime
    with _lock:
        if _kdf_path is None:
            return
        from pykorf import Model

        _model = Model(_kdf_path)
        _model_mtime = _kdf_path.stat().st_mtime if _kdf_path.exists() else None


def clear() -> None:
    """Unload the current model."""
    global _model, _kdf_path, _model_mtime
    with _lock:
        _model = None
        _kdf_path = None
        _model_mtime = None


def is_stale() -> bool:
    """Check if the KDF file on disk is newer than the in-memory model.

    Returns:
        True if the file has been modified externally since last load/save.
    """
    global _kdf_path, _model_mtime
    with _lock:
        if _kdf_path is None or _model_mtime is None:
            return False
        if not _kdf_path.exists():
            return False
        try:
            file_mtime = _kdf_path.stat().st_mtime
            return file_mtime > _model_mtime
        except OSError:
            return False
