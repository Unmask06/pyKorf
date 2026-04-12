"""Single-user in-process model state for the FastAPI web UI.

No cookies, no sessions — the server holds exactly one model at a time,
matching how the terminal TUI works. Async-compatible using asyncio.Lock.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykorf.core.model import Model

_model: Model | None = None
_kdf_path: Path | None = None
_model_mtime: float | None = None
_lock = asyncio.Lock()


async def load(model: Model, kdf_path: Path) -> None:
    """Store *model* as the active model.

    Args:
        model: Loaded KorfModel instance.
        kdf_path: Source .kdf file path.
    """
    global _model, _kdf_path, _model_mtime
    async with _lock:
        _model = model
        _kdf_path = kdf_path
        _model_mtime = kdf_path.stat().st_mtime if kdf_path.exists() else None


async def get_model() -> Model | None:
    """Return the active model, or ``None`` if none is loaded."""
    async with _lock:
        return _model


async def get_kdf_path() -> Path | None:
    """Return the active model's source path, or ``None``."""
    async with _lock:
        return _kdf_path


async def has_model() -> bool:
    """Return True if a model is currently loaded."""
    async with _lock:
        return _model is not None


async def reload() -> None:
    """Re-parse the active KDF file and replace the in-memory model.

    Call this after any operation that writes the KDF to disk.
    Does nothing if no model is currently loaded.
    """
    global _model, _model_mtime
    async with _lock:
        if _kdf_path is None:
            return
        from pykorf.core.model import Model

        _model = Model(_kdf_path)
        _model_mtime = _kdf_path.stat().st_mtime if _kdf_path.exists() else None


async def clear() -> None:
    """Unload the current model."""
    global _model, _kdf_path, _model_mtime
    async with _lock:
        _model = None
        _kdf_path = None
        _model_mtime = None


async def is_stale() -> bool:
    """Check if the KDF file on disk is newer than the in-memory model.

    Returns:
        True if the file has been modified externally since last load/save.
    """
    async with _lock:
        if _kdf_path is None or _model_mtime is None:
            return False
        if not _kdf_path.exists():
            return False
        try:
            file_mtime = _kdf_path.stat().st_mtime
            return file_mtime > _model_mtime
        except OSError:
            return False


# --- Sync convenience accessors for use inside asyncio.to_thread() ---
# These read the module-level state without acquiring the async lock,
# which is safe because uvicorn runs a single-threaded event loop.


def get_model_sync() -> Model | None:
    """Sync: Return the active model, or ``None``."""
    return _model


def get_kdf_path_sync() -> Path | None:
    """Sync: Return the active model's source path, or ``None``."""
    return _kdf_path


def has_model_sync() -> bool:
    """Sync: Return True if a model is currently loaded."""
    return _model is not None


def reload_sync() -> None:
    """Sync: Re-parse the active KDF file and replace the in-memory model.

    Only call this from code that runs inside the same event loop
    (e.g. from a function passed to asyncio.to_thread that needs
    to update state after model.save()).
    """
    global _model, _model_mtime
    if _kdf_path is None:
        return
    from pykorf.core.model import Model

    _model = Model(_kdf_path)
    _model_mtime = _kdf_path.stat().st_mtime if _kdf_path.exists() else None


def load_sync(model: Model, kdf_path: Path) -> None:
    """Sync: Store *model* as the active model.

    Only call this from code that runs inside the same event loop.
    """
    global _model, _kdf_path, _model_mtime
    _model = model
    _kdf_path = kdf_path
    _model_mtime = kdf_path.stat().st_mtime if kdf_path.exists() else None


def clear_sync() -> None:
    """Sync: Unload the current model."""
    global _model, _kdf_path, _model_mtime
    _model = None
    _kdf_path = None
    _model_mtime = None


def is_stale_sync() -> bool:
    """Sync: Check if the KDF file on disk is newer than the in-memory model.

    Returns:
        True if the file has been modified externally since last load/save.
    """
    if _kdf_path is None or _model_mtime is None:
        return False
    if not _kdf_path.exists():
        return False
    try:
        file_mtime = _kdf_path.stat().st_mtime
        return file_mtime > _model_mtime
    except OSError:
        return False
