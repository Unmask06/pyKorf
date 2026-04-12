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

router = APIRouter()

_EXT_MAP: dict[str, set[str]] = {
    "kdf": {".kdf"},
    "excel": {".xlsx", ".xls"},
    "json": {".json"},
    "any": set(),
}


def _is_safe_path(path: Path) -> bool:
    try:
        resolved = path.resolve()
    except (OSError, ValueError):
        return False
    home = Path.home().resolve()
    if os.name == "nt":
        allowed_roots = [home] + [
            Path(f"{d}:\\") for d in string.ascii_uppercase if Path(f"{d}:\\").exists()
        ]
    else:
        allowed_roots = [home, Path("/")]
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

    drives = []
    if os.name == "nt":
        drives = [f"{d}:\\" for d in string.ascii_uppercase if Path(f"{d}:\\").exists()]

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
