"""FastAPI dependency injection helpers."""

from __future__ import annotations

from fastapi import HTTPException

from pykorf.app.api import session_state as _sess


async def require_model():
    """Return the active model or raise HTTPException.

    Automatically reloads the model if the KDF file has been modified
    externally (e.g., by KORF GUI). Flags the reload so middleware can
    set the ``X-Model-Stale: true`` response header for the frontend toast.

    Returns:
        Active KorfModel instance.

    Raises:
        HTTPException: 409 if no model is loaded (client should redirect to /).
    """
    was_stale = await _sess.is_stale()
    if was_stale:
        await _sess.reload()
        _sess.flag_reload()
    model = await _sess.get_model()
    if model is None:
        raise HTTPException(
            status_code=409,
            detail="No model loaded. Please open a KDF file first.",
        )
    return model


async def persist(model) -> None:
    """Save model changes to disk and reload session state.

    Centralizes the save + reload pattern used by every mutating endpoint.
    model.save() is run in a thread to avoid blocking the event loop.
    """
    import asyncio

    await asyncio.to_thread(model.save)
    await _sess.reload()


def pipe_names(model) -> list[str]:
    """Return sorted pipe name list for tables and dropdowns.

    Args:
        model: Loaded KorfModel.

    Returns:
        Sorted list of non-empty pipe names.
    """
    return sorted(
        model.pipes[idx].name for idx in range(1, len(model.pipes) + 1) if model.pipes[idx].name
    )


def is_real_pipe(pipe) -> bool:
    """Return True if the pipe is not a dummy pipe.

    Dummy pipes have names starting with 'd' (e.g. 'd1').
    """
    return bool(pipe.name and not pipe.name.startswith("d"))
