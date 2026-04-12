"""Doc Register API: /api/doc-register/*."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, Query

from pykorf.app.api.schemas import (
    DocRegisterRebuildResponse,
    DocRegisterStatusResponse,
    EddrResult,
    QueryEntryResult,
)
from pykorf.app.operation.config.config import (
    get_doc_register_excel_path,
    get_doc_register_sp_site_url,
    set_doc_register_excel_path,
    set_doc_register_sp_site_url,
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
from pykorf.core.log import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/status", response_model=DocRegisterStatusResponse)
async def api_status():
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


@router.get("/search-eddr", response_model=list[EddrResult])
async def api_search_eddr(q: str = Query("")):
    """Search EDDR entries by title."""
    if not q.strip():
        return []
    results = search_eddr_by_title(q)
    return [EddrResult(**r) for r in results]


@router.get("/search-query", response_model=list[QueryEntryResult])
async def api_search_query(doc_no: str = Query("")):
    """Search query entries by document number."""
    if not doc_no.strip():
        return []
    results = search_query_by_name(doc_no)
    return [QueryEntryResult(**r) for r in results]


@router.get("/search-files", response_model=list[QueryEntryResult])
async def api_search_files(q: str = Query("")):
    """Search query entries by name or path."""
    if len(q.strip()) < 2:
        return []
    results = search_query_entries(q)
    return [QueryEntryResult(**r) for r in results]


@router.post("/rebuild-db", response_model=DocRegisterRebuildResponse)
async def api_rebuild_db():
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


@router.post("/config")
async def api_config(excel_path: str | None = None, sp_site_url: str | None = None):
    """Save Document Register configuration."""
    if excel_path:
        set_doc_register_excel_path(excel_path.strip())
    if sp_site_url:
        set_doc_register_sp_site_url(sp_site_url.strip())

    return {
        "excel_path": get_doc_register_excel_path(),
        "sp_site_url": get_doc_register_sp_site_url(),
    }
