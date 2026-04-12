"""Browse API: /api/browse."""

from __future__ import annotations

import os
import string
from pathlib import Path

from fastapi import APIRouter, Query

from pykorf.app.api.schemas import BrowseEntryDir, BrowseEntryFile, BrowseResponse, PinnedFoldersResponse
from pykorf.app.operation.integration.sharepoint import get_sharepoint_url, is_sharepoint_synced
from pykorf.app.operation.config.preferences import (
    get_pinned_folders,
    add_pinned_folder,
    remove_pinned_folder,
)
from pykorf.core.log import get_logger

logger = get_logger(__name__)
router = APIRouter()

_EXT_MAP: dict[str, set[str]] = {
    "kdf": {".kdf"},
    "excel": {".xlsx", ".xls"},
    "json": {".json"},
    "any": set(),
}

_cached_drives: list[Path] | None = None


def _get_available_drives() -> list[Path]:
    """Get list of available drives, cached to avoid slow repeated checks."""
    global _cached_drives
    if _cached_drives is not None:
        return _cached_drives
    
    _cached_drives = [Path.home()]
    if os.name == "nt":
        for d in string.ascii_uppercase:
            try:
                drive = Path(f"{d}:\\")
                if drive.exists():
                    _cached_drives.append(drive)
            except (OSError, PermissionError):
                continue
    return _cached_drives


def invalidate_drive_cache() -> None:
    """Invalidate the cached drive list. Call when drives may have changed."""
    global _cached_drives
    _cached_drives = None


def _is_safe_path(path: Path) -> bool:
    try:
        resolved = path.resolve()
    except (OSError, ValueError):
        return False
    allowed_roots = _get_available_drives()
    for root in allowed_roots:
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


@router.get("", response_model=BrowseResponse)
async def api_browse(
    path: str = Query("", alias="path"),
    filter: str = Query("any", alias="filter"),
):
    """Return directory listing for the path browser widget."""
    ext_filter = _EXT_MAP.get(filter.lower(), set())

    if path:
        target = Path(path.strip())
        if not target.is_dir():
            target = target.parent if target.parent.is_dir() else Path.home()
    else:
        target = Path.home()

    try:
        target = target.resolve()
        if not _is_safe_path(target):
            target = Path.home().resolve()
        entries = list(target.iterdir())
    except (PermissionError, OSError):
        target = Path.home().resolve()
        entries = list(target.iterdir())

    current_sp_url = get_sharepoint_url(target)

    dirs = []
    files = []

    for entry in sorted(entries, key=lambda e: (not e.is_dir(), e.name.lower())):
        try:
            if entry.is_dir() and not entry.name.startswith("."):
                dirs.append(
                    BrowseEntryDir(
                        name=entry.name,
                        path=str(entry),
                        synced=is_sharepoint_synced(entry),
                    )
                )
            elif entry.is_file():
                if not ext_filter or entry.suffix.lower() in ext_filter:
                    sp_url = get_sharepoint_url(entry)
                    files.append(
                        BrowseEntryFile(
                            name=entry.name,
                            path=str(entry),
                            sharepoint_url=sp_url,
                        )
                    )
        except PermissionError:
            continue

    parent = str(target.parent) if target != target.parent else None

    drives = [str(d) for d in _get_available_drives() if os.name == "nt" and d.anchor.endswith(":\\")]

    pinned = get_pinned_folders()

    return BrowseResponse(
        current=str(target),
        current_sp_url=current_sp_url,
        parent=parent,
        drives=drives,
        pinned_folders=pinned,
        dirs=dirs,
        files=files,
    )


@router.post("/pin", response_model=PinnedFoldersResponse)
async def pin_folder(folder: str = Query(..., alias="folder")) -> PinnedFoldersResponse:
    """Pin a folder for quick access in the path browser."""
    p = Path(folder)
    if not p.is_dir():
        return PinnedFoldersResponse(success=False, error=f"Not a valid directory: {folder}")
    add_pinned_folder(str(p.resolve()))
    return PinnedFoldersResponse(pinned_folders=get_pinned_folders())


@router.post("/unpin", response_model=PinnedFoldersResponse)
async def unpin_folder(folder: str = Query(..., alias="folder")) -> PinnedFoldersResponse:
    """Unpin a folder from quick access."""
    remove_pinned_folder(folder)
    return PinnedFoldersResponse(pinned_folders=get_pinned_folders())
