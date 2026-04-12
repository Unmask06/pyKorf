"""FastAPI dependency injection helpers."""

from __future__ import annotations

from fastapi import HTTPException

from pykorf.app.api import session_state as _sess


async def require_model():
    """Return the active model or raise HTTPException.

    Automatically reloads the model if the KDF file has been modified
    externally (e.g., by KORF GUI).

    Returns:
        Active KorfModel instance.

    Raises:
        HTTPException: 409 if no model is loaded (client should redirect to /).
    """
    was_stale = await _sess.is_stale()
    if was_stale:
        await _sess.reload()
    model = await _sess.get_model()
    if model is None:
        raise HTTPException(
            status_code=409,
            detail="No model loaded. Please open a KDF file first.",
        )
    return model


def pipe_names(model) -> list[str]:
    """Return sorted pipe name list for tables and dropdowns.

    Args:
        model: Loaded KorfModel.

    Returns:
        Sorted list of non-empty pipe names.
    """
    return sorted(
        model.pipes[idx].name
        for idx in range(1, model.num_pipes + 1)
        if model.pipes[idx].name
    )
