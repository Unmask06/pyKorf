"""SharePoint URL resolution API: /api/sharepoint/*."""

from __future__ import annotations

from fastapi import APIRouter

from pykorf.app.api.schemas import OkResponse, ResolveSpUrlRequest
from pykorf.app.operation.integration.sharepoint import get_local_path_from_sp_url
from pykorf.core.log import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/resolve-url", response_model=OkResponse, operation_id="resolveSpUrl")
async def resolve_sp_url(req: ResolveSpUrlRequest) -> OkResponse:
    """Resolve a SharePoint URL to its local OneDrive-synced path.

    Uses user-configured SharePoint overrides first, then falls back to
    OneDrive registry sync roots for automatic conversion.

    Args:
        req: Request containing the SharePoint URL to resolve.

    Returns:
        OkResponse with success=True and message=local_path if resolved,
        or success=False with error message if resolution failed.
    """
    if not req.sp_url or not req.sp_url.startswith("https://"):
        return OkResponse(success=False, error="Invalid SharePoint URL format")

    local_path = get_local_path_from_sp_url(req.sp_url)
    if local_path:
        logger.info("sp_url_resolved", sp_url=req.sp_url, local_path=local_path)
        return OkResponse(success=True, message=local_path)

    logger.warning("sp_url_resolution_failed", sp_url=req.sp_url)
    return OkResponse(
        success=False,
        error=(
            "Could not resolve SharePoint URL to local path. "
            "Ensure the folder is synced via OneDrive or configure a SharePoint Path Override."
        ),
    )
