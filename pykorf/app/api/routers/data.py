"""Data API: /api/data/*."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter

from pykorf.app.api import session_state as _sess
from pykorf.app.api.deps import require_model
from pykorf.app.api.schemas import ApplyDataResponse, ApplyHmbRequest, ApplyPmsRequest
from pykorf.core.log import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _apply_pms_from_source(model, pms_source: Path) -> None:
    """Apply PMS from a given source (Excel or JSON) to the model."""
    from pykorf.app.operation.data_import.pms import apply_pms as _apply_pms, import_pms_from_excel

    if pms_source.suffix.lower() in (".xlsx", ".xls"):
        json_path = import_pms_from_excel(pms_source)
        _apply_pms(json_path, model, save=False)
    else:
        _apply_pms(pms_source, model, save=False)

    model.save()
    # Note: caller must await _sess.reload() after asyncio.to_thread returns.
    # Do NOT call reload_sync() here — it writes module-level globals from a
    # worker thread without the asyncio.Lock, causing a data race.
    from pykorf.app.operation.config.config import set_pms_excel_last_imported
    set_pms_excel_last_imported(datetime.now(UTC).isoformat())
    logger.info("pms_applied", pms_source=str(pms_source))


def apply_pms_if_stale(model) -> bool:
    """Apply PMS from the configured Excel file if it has been updated.

    Returns:
        True if PMS was applied (caller should await _sess.reload()).
    """
    from pykorf.app.operation.config.config import get_pms_excel_path
    from pykorf.app.operation.data_import.pms import is_pms_excel_stale

    if not is_pms_excel_stale():
        return False
    pms_path = get_pms_excel_path()
    if not pms_path:
        return False
    pms_source = Path(pms_path)
    if not pms_source.is_file():
        return False
    try:
        _apply_pms_from_source(model, pms_source)
        return True
    except Exception as exc:
        logger.warning("auto_apply_pms_failed", error=str(exc))
        return False


@router.post("/apply-pms", response_model=ApplyDataResponse)
async def apply_pms(req: ApplyPmsRequest):
    """Apply PMS data from Excel or JSON file."""
    model = await require_model()
    messages = []
    errors = []

    pms_source_str = req.pms_source.strip()
    if not pms_source_str:
        errors.append("PMS source file path is required.")
        return ApplyDataResponse(success=False, errors=errors)

    from pykorf.app.operation.config.config import get_pms_excel_path, set_pms_excel_path

    # If empty, try saved path
    if not pms_source_str:
        pms_excel = get_pms_excel_path()
        if pms_excel:
            pms_source_str = pms_excel

    pms_source = Path(pms_source_str)
    if not pms_source.is_file():
        errors.append(f"PMS data file not found: {pms_source}")
        return ApplyDataResponse(success=False, errors=errors)

    try:
        await asyncio.to_thread(_apply_pms_from_source, model, pms_source)
        await _sess.reload()
        set_pms_excel_path(pms_source)
        messages.append({"type": "success", "message": "PMS data applied and saved successfully."})
    except Exception as exc:
        logger.error("pms_apply_error", error=str(exc))
        errors.append(f"Error applying PMS: {exc}")

    return ApplyDataResponse(success=len(errors) == 0, messages=messages, errors=errors)


@router.post("/apply-hmb", response_model=ApplyDataResponse)
async def apply_hmb(req: ApplyHmbRequest):
    """Apply HMB data from Excel or JSON file."""
    model = await require_model()
    messages = []
    errors = []

    hmb_source_str = req.hmb_source.strip()
    if not hmb_source_str:
        errors.append("HMB source file path is required.")
        return ApplyDataResponse(success=False, errors=errors)

    hmb_source = Path(hmb_source_str)
    if not hmb_source.is_file():
        errors.append(f"HMB data file not found: {hmb_source}")
        return ApplyDataResponse(success=False, errors=errors)

    try:
        from pykorf.app.operation.data_import.hmb import apply_hmb as _apply_hmb
        from pykorf.app.operation.config.config import set_last_hmb_path

        def _do_apply():
            _apply_hmb(hmb_source, model, save=False)
            model.save()

        await asyncio.to_thread(_do_apply)
        await _sess.reload()
        set_last_hmb_path(hmb_source)
        messages.append({"type": "success", "message": "HMB data applied and saved successfully."})
    except Exception as exc:
        logger.error("hmb_apply_error", error=str(exc))
        errors.append(f"Error applying HMB: {exc}")

    return ApplyDataResponse(success=len(errors) == 0, messages=messages, errors=errors)
