"""Doc Register API: /api/doc-register/*."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Query

from pykorf.app.api.schemas import (
    DocRegisterConfigResponse,
    DocRegisterRebuildResponse,
    DocRegisterSearchEddrRequest,
    DocRegisterSearchEddrResponse,
    DocRegisterSearchFilesRequest,
    DocRegisterSearchFilesResponse,
    DocRegisterSearchQueryRequest,
    DocRegisterSearchQueryResponse,
    DocRegisterStatusResponse,
    EddrResult,
    EmptyRequest,
    QueryEntryResult,
    SetDocRegisterConfigRequest,
)
from pykorf.app.doc_register.db_ops import (
    get_db_stats,
    search_eddr_by_title,
    search_query_by_name,
    search_query_entries,
)
from pykorf.app.doc_register.excel_to_db import (
    build_db_from_excel,
    get_db_path,
    is_excel_stale,
)
from pykorf.app.operation.config.config import (
    get_doc_register_excel_path,
    get_doc_register_sp_site_url,
    set_doc_register_excel_path,
    set_doc_register_sp_site_url,
)
from pykorf.core.log import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/status", response_model=DocRegisterStatusResponse)
async def api_status() -> DocRegisterStatusResponse:
    """Return Document Register configuration and DB status."""
    excel_path = get_doc_register_excel_path()
    sp_site_url = get_doc_register_sp_site_url()
    db_path = get_db_path()
    db_exists = db_path.is_file()
    stale = is_excel_stale() if excel_path else False
    stats = get_db_stats() if db_exists else {"eddr_count": 0, "query_count": 0, "db_exists": False}

    return DocRegisterStatusResponse(
        excel_path=excel_path,
        sp_site_url=sp_site_url,
        db_exists=db_exists,
        is_stale=stale,
        db_stats=stats,
    )


@router.get("/search-eddr", response_model=DocRegisterSearchEddrResponse)
async def api_search_eddr(
    req: Annotated[DocRegisterSearchEddrRequest, Query()],
) -> DocRegisterSearchEddrResponse:
    """Search EDDR entries by title."""
    if not req.q.strip():
        return DocRegisterSearchEddrResponse()
    results = search_eddr_by_title(req.q)
    return DocRegisterSearchEddrResponse(results=[EddrResult(**r) for r in results])


@router.get("/search-query", response_model=DocRegisterSearchQueryResponse)
async def api_search_query(
    req: Annotated[DocRegisterSearchQueryRequest, Query()],
) -> DocRegisterSearchQueryResponse:
    """Search query entries by document number."""
    if not req.doc_no.strip():
        return DocRegisterSearchQueryResponse()
    results = search_query_by_name(req.doc_no)
    return DocRegisterSearchQueryResponse(results=[QueryEntryResult(**r) for r in results])


@router.get("/search-files", response_model=DocRegisterSearchFilesResponse)
async def api_search_files(
    req: Annotated[DocRegisterSearchFilesRequest, Query()],
) -> DocRegisterSearchFilesResponse:
    """Search query entries by name or path."""
    if len(req.q.strip()) < 2:
        return DocRegisterSearchFilesResponse()
    results = search_query_entries(req.q)
    return DocRegisterSearchFilesResponse(results=[QueryEntryResult(**r) for r in results])


@router.post("/rebuild-db", response_model=DocRegisterRebuildResponse)
async def api_rebuild_db(_: EmptyRequest) -> DocRegisterRebuildResponse:
    """Force rebuild the Document Register database from Excel."""
    excel_path_str = get_doc_register_excel_path()
    if not excel_path_str:
        return DocRegisterRebuildResponse(error="No Excel path configured. Set it in Preferences.")

    excel_path = Path(excel_path_str)
    if not excel_path.is_file():
        return DocRegisterRebuildResponse(error=f"Excel file not found: {excel_path_str}")

    sp_site_url = get_doc_register_sp_site_url() or ""

    try:
        async with asyncio.timeout(120):
            await asyncio.to_thread(build_db_from_excel, excel_path, sp_site_url)
        stats = get_db_stats()
        logger.info("doc_register.rebuild_complete", stats=stats)
        return DocRegisterRebuildResponse(
            success=True,
            message=(
                f"DB rebuilt: {stats['eddr_count']} EDDR entries, "
                f"{stats['query_count']} query entries"
            ),
            stats=stats,
        )
    except Exception as exc:
        logger.error("doc_register.rebuild_failed", error=str(exc))
        return DocRegisterRebuildResponse(error=str(exc))


@router.post("/config", response_model=DocRegisterConfigResponse)
async def api_config(req: SetDocRegisterConfigRequest) -> DocRegisterConfigResponse:
    """Save Document Register configuration."""
    if req.excel_path:
        set_doc_register_excel_path(req.excel_path.strip())
    if req.sp_site_url:
        set_doc_register_sp_site_url(req.sp_site_url.strip())

    return DocRegisterConfigResponse(
        excel_path=get_doc_register_excel_path(),
        sp_site_url=get_doc_register_sp_site_url(),
    )
