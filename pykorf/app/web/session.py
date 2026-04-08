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
_lock = threading.Lock()


def load(model: Model, kdf_path: Path) -> None:
    """Store *model* as the active model.

    Args:
        model: Loaded KorfModel instance.
        kdf_path: Source .kdf file path.
    """
    global _model, _kdf_path
    with _lock:
        _model = model
        _kdf_path = kdf_path


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
    global _model
    with _lock:
        if _kdf_path is None:
            return
        from pykorf import Model

        _model = Model(_kdf_path)


def clear() -> None:
    """Unload the current model."""
    global _model, _kdf_path
    with _lock:
        _model = None
        _kdf_path = None
