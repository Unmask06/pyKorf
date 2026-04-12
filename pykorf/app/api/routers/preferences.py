"""Preferences API: /api/preferences/*."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter

from pykorf.app.api.schemas import (
    AddSpOverrideRequest,
    DeleteSpOverrideRequest,
    DocRegisterRebuildResponse,
    EditSpOverrideRequest,
    LicenseValidationResponse,
    PreferencesResponse,
    SetDocRegisterConfigRequest,
    SetLicenseKeyRequest,
    SetSkipSpRequest,
)
from pykorf.app.operation.config.preferences import (
    get_doc_register_db_last_imported,
    get_doc_register_excel_path,
    get_doc_register_sp_site_url,
    get_license_key,
    get_sp_overrides,
    get_skip_sp_override,
    set_doc_register_excel_path,
    set_doc_register_sp_site_url,
    set_license_key,
    set_sp_overrides,
    set_skip_sp_override,
)
from pykorf.app.operation.integration.license import validate_license_key
from pykorf.app.operation.integration.sharepoint import clear_cache
from pykorf.core.log import get_logger

logger = get_logger(__name__)
router = APIRouter()

DEFAULT_SP_SITE_URL = "https://cc7ges.sharepoint.com"


def _invalidate_all_caches() -> None:
    clear_cache()


@router.get("/", response_model=PreferencesResponse)
async def get_preferences():
    """Return all preference settings."""
    overrides = get_sp_overrides()
    return PreferencesResponse(
        sp_overrides=overrides,
        skip_sp_override=get_skip_sp_override(),
        license_key=get_license_key(),
        doc_register_excel_path=get_doc_register_excel_path(),
        doc_register_sp_site_url=get_doc_register_sp_site_url(),
        doc_register_db_last_imported=get_doc_register_db_last_imported(),
        sp_overrides_configured=len(overrides) > 0,
        default_doc_register_url="",
    )


@router.post("/sp-overrides/add")
async def add_sp_override(req: AddSpOverrideRequest):
    """Add a new SharePoint override."""
    from urllib.parse import urlparse

    if not req.local_path or not req.sp_url:
        return {"success": False, "error": "Both local path and SharePoint URL are required."}
    if not Path(req.local_path).is_dir():
        return {"success": False, "error": f"Local path does not exist: {req.local_path}"}
    parsed = urlparse(req.sp_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return {"success": False, "error": f"Invalid SharePoint URL: {req.sp_url}"}

    overrides = get_sp_overrides()
    overrides[req.local_path] = req.sp_url
    set_sp_overrides(overrides)
    _invalidate_all_caches()
    return {"success": True, "message": "Override added."}


@router.post("/sp-overrides/edit")
async def edit_sp_override(req: EditSpOverrideRequest):
    """Edit an existing SharePoint override."""
    overrides = get_sp_overrides()
    if req.original_local_path in overrides:
        del overrides[req.original_local_path]
    overrides[req.local_path] = req.sp_url
    set_sp_overrides(overrides)
    _invalidate_all_caches()
    return {"success": True, "message": "Override updated."}


@router.post("/sp-overrides/delete")
async def delete_sp_override(req: DeleteSpOverrideRequest):
    """Delete a SharePoint override."""
    overrides = get_sp_overrides()
    if req.local_path in overrides:
        del overrides[req.local_path]
        set_sp_overrides(overrides)
        _invalidate_all_caches()
        return {"success": True, "message": "Override removed."}
    return {"success": False, "error": "Override not found."}


@router.post("/skip-sp")
async def set_skip_sp(req: SetSkipSpRequest):
    """Toggle skip SharePoint override validation."""
    set_skip_sp_override(req.skip)
    return {"success": True, "skip_sp_override": req.skip}


@router.post("/license", response_model=LicenseValidationResponse)
async def set_license(req: SetLicenseKeyRequest):
    """Validate and save a license key."""
    if not req.license_key:
        return LicenseValidationResponse(valid=False, error="Please enter a license key.")
    valid, expiry, err = validate_license_key(req.license_key)
    if valid:
        set_license_key(req.license_key)
        return LicenseValidationResponse(valid=True, expiry=str(expiry))
    return LicenseValidationResponse(valid=False, expiry=str(expiry) if expiry else None, error=err)


@router.post("/doc-register", response_model=DocRegisterRebuildResponse)
async def set_doc_register_config(req: SetDocRegisterConfigRequest):
    """Save Document Register configuration and rebuild DB if Excel path changed."""
    from pykorf.app.doc_register.excel_to_db import build_db_from_excel
    from pykorf.app.operation.integration.sharepoint import get_local_path_from_sp_url

    excel_path = req.excel_path
    sp_site_url = req.sp_site_url

    # Convert SharePoint URL to local path if needed
    if excel_path and excel_path.startswith("https://"):
        converted_path = get_local_path_from_sp_url(excel_path)
        if converted_path is None:
            return DocRegisterRebuildResponse(
                error=(
                    "SharePoint URL could not be converted to local path. "
                    "No matching override found."
                )
            )
        excel_path = converted_path

    # Validate local path exists
    if excel_path and not Path(excel_path).is_file():
        return DocRegisterRebuildResponse(error=f"Excel file not found: {excel_path}")

    changed = False
    if excel_path and excel_path != get_doc_register_excel_path():
        set_doc_register_excel_path(excel_path)
        changed = True
    if sp_site_url and sp_site_url != get_doc_register_sp_site_url():
        set_doc_register_sp_site_url(sp_site_url)
        changed = True

    if changed and excel_path:
        try:
            async with asyncio.timeout(120):
                await asyncio.to_thread(build_db_from_excel, Path(excel_path), sp_site_url or "")
            return DocRegisterRebuildResponse(
                success=True, message="Config saved and database rebuilt."
            )
        except Exception as exc:
            return DocRegisterRebuildResponse(
                success=False,
                message="Config saved, but DB rebuild failed.",
                error=str(exc),
            )

    return DocRegisterRebuildResponse(success=True, message="Document Register config saved.")
