"""Session API: /api/session/*."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from pykorf.app.api import session_state as _sess
from pykorf.app.api.schemas import (
    EmptyRequest,
    OpenInKorfResponse,
    SessionCloseResponse,
    SessionOpenRequest,
    SessionReloadResponse,
    SessionStatusResponse,
)
from pykorf.core.log import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _get_username() -> str:
    return os.environ.get("USERNAME") or os.environ.get("USER") or "there"


def _check_setup() -> tuple[bool, bool, bool]:
    """Check whether mandatory preferences are configured."""
    from pykorf.app.operation.config.config import (
        get_doc_register_excel_path,
        get_skip_sp_override,
        get_sp_overrides,
    )

    skip_sp = get_skip_sp_override()
    sp_ok = bool(get_sp_overrides()) if not skip_sp else True
    excel_path = get_doc_register_excel_path()
    doc_register_ok = bool(excel_path and Path(excel_path).is_file())
    setup_ok = True if skip_sp else (sp_ok and doc_register_ok)
    return setup_ok, sp_ok, doc_register_ok


@router.get("/status", response_model=SessionStatusResponse, operation_id="getSessionStatus")
async def session_status() -> SessionStatusResponse:
    """Return current session status, recent files, and setup check."""
    from pykorf import __version__
    from pykorf.app.operation.config.config import get_recent_files, get_skip_sp_override
    from pykorf.app.update_check import is_update_available

    model_loaded = await _sess.has_model()
    kdf_path_val = await _sess.get_kdf_path()
    kdf_mtime = None
    if kdf_path_val:
        try:
            import datetime

            mtime = kdf_path_val.stat().st_mtime
            kdf_mtime = datetime.datetime.fromtimestamp(mtime).strftime("%d %b %H:%M")
        except OSError:
            pass

    setup_ok, sp_ok, doc_register_ok = _check_setup()

    return SessionStatusResponse(
        model_loaded=model_loaded,
        kdf_path=str(kdf_path_val) if kdf_path_val else None,
        kdf_mtime=kdf_mtime,
        recent_files=get_recent_files() or [],
        setup_ok=setup_ok,
        sp_ok=sp_ok,
        doc_register_ok=doc_register_ok,
        skip_sp_override=get_skip_sp_override(),
        username=_get_username(),
        update_available=is_update_available(),
        version=__version__,
    )


@router.post("/open", response_model=SessionStatusResponse, operation_id="openFile")
async def open_file(req: SessionOpenRequest) -> SessionStatusResponse:
    """Load a KDF file into the global model state."""
    from pykorf.app.operation.config.config import record_opened_file

    setup_ok, sp_ok, doc_register_ok = _check_setup()
    if not setup_ok:
        raise HTTPException(
            status_code=400,
            detail="Complete the required setup in Preferences before opening a model.",
        )

    kdf_path_str = req.kdf_path.strip().strip('"')
    path = Path(kdf_path_str)

    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    from pykorf.core.model import Model

    model = await asyncio.to_thread(Model, path)
    record_opened_file(str(path))
    await _sess.load(model, path)
    logger.info("model_loaded", kdf_path=str(path))

    return await session_status()


@router.post("/reload", response_model=SessionReloadResponse, operation_id="reloadModel")
async def reload_model(_: EmptyRequest) -> SessionReloadResponse:
    """Re-parse the KDF from disk."""
    await _sess.reload()
    logger.info("model_reloaded")
    return SessionReloadResponse(message="Model reloaded from disk")


@router.post("/close", response_model=SessionCloseResponse, operation_id="closeModel")
async def close_model(_: EmptyRequest) -> SessionCloseResponse:
    """Unload the current model."""
    await _sess.clear()
    return SessionCloseResponse(message="Model unloaded")


@router.post("/open-in-korf", response_model=OpenInKorfResponse, operation_id="openModelInKorf")
async def open_model_in_korf() -> OpenInKorfResponse:
    """Open the current KDF file in the external Korf application."""
    kdf_path = await _sess.get_kdf_path()
    if kdf_path is None:
        raise HTTPException(status_code=400, detail="No model loaded.")

    try:
        from pykorf.app.automation import launch_ui

        launch_ui(kdf_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to launch Korf", exc_info=exc)
        raise HTTPException(status_code=500, detail=f"Failed to launch Korf: {exc}")

    logger.info("Korf launched", kdf_path=str(kdf_path))
    return OpenInKorfResponse(message="Korf opened with current model.")
