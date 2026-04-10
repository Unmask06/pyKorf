"""Shared helpers for the pyKorf web UI.

Provides model-state accessors used across multiple route Blueprints.
"""

from __future__ import annotations

from typing import Any

from flask import Response, flash, redirect, url_for

from pykorf.app.web import session as _sess


def pipe_names(model: Any) -> list[str]:
    """Return sorted pipe name list for tables and dropdowns.

    Args:
        model: Loaded KorfModel.

    Returns:
        Sorted list of non-empty pipe names.
    """
    return sorted(
        model.pipes[idx].name for idx in range(1, model.num_pipes + 1) if model.pipes[idx].name
    )


def require_model() -> Any:
    """Return the active model or redirect to the file picker.

    Automatically reloads the model if the KDF file has been modified
    externally (e.g., by KORF GUI) since the last load/save.

    Returns:
        Active KorfModel, or a 302 redirect response if no model is loaded.
    """
    if _sess.is_stale():
        _sess.reload()
        flash("Model reloaded from disk - file was modified externally", "info")
    model = _sess.get_model()
    if model is None:
        return redirect(url_for("file_picker.file_picker_page"))
    return model


def is_redirect(obj: Any) -> bool:
    """Return True if *obj* is a Flask redirect response rather than a model.

    Args:
        obj: Value returned by :func:`require_model`.

    Returns:
        True when the value should be returned directly to Flask.
    """
    return isinstance(obj, Response)
