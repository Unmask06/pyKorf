"""Path browser API: /api/browse."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Blueprint, jsonify, request

from pykorf.use_case.web.sharepoint import get_sharepoint_url, is_sharepoint_synced

bp = Blueprint("browse", __name__)

# File extensions surfaced per filter mode
_EXT_MAP: dict[str, set[str]] = {
    "kdf": {".kdf"},
    "excel": {".xlsx", ".xls"},
    "json": {".json"},
    "any": set(),  # empty = show all files
}


def _is_safe_path(path: Path) -> bool:
    """Check if path is within allowed browsing roots.

    Prevents path traversal attacks by restricting browsing to:
    - User's home directory
    - Windows drive roots (on Windows)

    Args:
        path: Resolved Path to validate.

    Returns:
        True if path is within allowed roots.
    """
    try:
        resolved = path.resolve()
    except (OSError, ValueError):
        return False

    home = Path.home().resolve()

    if os.name == "nt":
        allowed_roots = [home] + [
            Path(f"{d}:\\") for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if Path(f"{d}:\\").exists()
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


@bp.route("/api/browse")
def api_browse():
    """Return directory listing for the path browser widget.

    Query params:
        path (str): Directory path to list. Defaults to the user's home directory.
        filter (str): One of ``kdf``, ``excel``, ``json``, ``any``. Controls which
            files are included. Directories are always shown.

    Returns:
        JSON ``{current, parent, drives, dirs, files}`` where *drives* is a
        non-empty list only on Windows.
    """
    raw = (request.args.get("path") or "").strip()
    fmode = (request.args.get("filter") or "any").lower()
    ext_filter = _EXT_MAP.get(fmode, set())

    if raw:
        target = Path(raw)
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

    dirs: list[dict] = []
    files: list[dict] = []

    for entry in sorted(entries, key=lambda e: (not e.is_dir(), e.name.lower())):
        try:
            if entry.is_dir() and not entry.name.startswith("."):
                dirs.append(
                    {
                        "name": entry.name,
                        "path": str(entry),
                        "synced": is_sharepoint_synced(entry),
                    }
                )
            elif entry.is_file():
                if not ext_filter or entry.suffix.lower() in ext_filter:
                    sp_url = get_sharepoint_url(entry)
                    files.append(
                        {
                            "name": entry.name,
                            "path": str(entry),
                            "sharepoint_url": sp_url,
                        }
                    )
        except PermissionError:
            continue

    parent = str(target.parent) if target != target.parent else None

    drives: list[str] = []
    if os.name == "nt":
        import string

        drives = [f"{d}:\\" for d in string.ascii_uppercase if Path(f"{d}:\\").exists()]

    return jsonify(
        {
            "current": str(target),
            "current_sp_url": current_sp_url,
            "parent": parent,
            "drives": drives,
            "dirs": dirs,
            "files": files,
        }
    )
