r"""Resolve local OneDrive-synced file paths to SharePoint URLs.

When the OneDrive sync client syncs a SharePoint document library to a local
folder, Windows stores the mapping in the registry under::

    HKCU\SOFTWARE\SyncEngines\Providers\OneDrive\{GUID}

Each sub-key contains:
  ``MountPoint``   - local folder root  (e.g. ``C:\Users\u\Company\ProjectSite\Documents``)
  ``UrlNamespace`` - SharePoint URL root (e.g. ``https://company.sharepoint.com/sites/ProjectSite/Documents``)

This module reads those mappings and translates any local path that falls
inside a synced folder to its equivalent SharePoint URL.  On non-Windows
platforms or when OneDrive is not installed every function returns ``None``
gradually.

No third-party packages required — only the standard library ``winreg``
module (available on CPython for Windows).
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from urllib.parse import quote

import structlog


# ── Registry helpers ──────────────────────────────────────────────────────────

_SYNC_ENGINES_KEY = r"SOFTWARE\SyncEngines\Providers\OneDrive"
_CACHE_TTL_SECONDS = 300

_sync_roots_cache: list[tuple[str, str]] | None = None
_cache_timestamp: float = 0.0


def _read_sync_roots() -> list[tuple[str, str]]:
    """Read all (MountPoint, UrlNamespace) pairs from the OneDrive registry key.

    Uses TTL-based caching (5 minute default) to avoid repeated registry reads.
    Returns an empty list on non-Windows or when OneDrive is not installed.

    Returns:
        List of ``(local_mount_point, sharepoint_url_namespace)`` tuples,
        sorted longest-first so the most specific match wins.
    """
    global _sync_roots_cache, _cache_timestamp

    logger = structlog.get_logger()

    now = time.time()
    if _sync_roots_cache is not None and (now - _cache_timestamp) < _CACHE_TTL_SECONDS:
        return _sync_roots_cache
    if os.name != "nt":
        return []

    import winreg  # type: ignore[import]

    results: list[tuple[str, str]] = []
    try:
        root = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _SYNC_ENGINES_KEY)
    except OSError as exc:
        logger.debug("sharepoint._read_sync_roots registry access failed", error=str(exc))
        return []

    try:
        idx = 0
        while True:
            try:
                guid = winreg.EnumKey(root, idx)
            except OSError:
                break
            idx += 1

            try:
                sub = winreg.OpenKey(root, guid)
            except OSError:
                continue

            try:
                mount = winreg.QueryValueEx(sub, "MountPoint")[0]
                url_ns = winreg.QueryValueEx(sub, "UrlNamespace")[0]
                if mount and url_ns:
                    results.append((str(mount), str(url_ns)))
            except OSError:
                pass
            finally:
                sub.Close()
    finally:
        root.Close()

    _sync_roots_cache = sorted(results, key=lambda t: -len(t[0]))
    _cache_timestamp = time.time()
    return _sync_roots_cache


def is_sharepoint_synced(local_path: str | Path) -> bool:
    """Return ``True`` if *local_path* lives inside a OneDrive-synced folder.

    Args:
        local_path: Absolute local file or directory path.

    Returns:
        ``True`` when the path maps to a known SharePoint sync root.
    """
    return get_sharepoint_url(local_path) is not None


def get_sharepoint_url(local_path: str | Path) -> str | None:
    r"""Convert a locally synced file path to its SharePoint URL.

    Reads the OneDrive sync-root registry mappings and returns the
    corresponding ``https://`` URL for files that live inside a synced
    document library.  Returns ``None`` for paths that are not synced or
    when called on a non-Windows platform.

    Args:
        local_path: Absolute local path to a file or folder.

    Returns:
        SharePoint URL string, or ``None`` if not resolvable.

    Example::

        # OneDrive syncs  C:\Users\alice\Contoso\ProjectA\Documents
        #              to https://contoso.sharepoint.com/sites/ProjectA/Documents

        url = get_sharepoint_url(r"C:\Users\alice\Contoso\ProjectA\Documents\P&ID-001.pdf")
        # "https://contoso.sharepoint.com/sites/ProjectA/Documents/P%26ID-001.pdf"
    """
    # Normalise to forward-slash string for comparison
    lp = str(local_path).replace("\\", "/").rstrip("/")

    # User-configured overrides take priority over registry entries.
    # Used when OneDrive stores only the library root (IsFolderScope=1) but
    # the synced folder is actually a subfolder deep in the library.
    from pykorf.use_case.preferences import get_sp_overrides

    for local_root, sp_url in sorted(get_sp_overrides().items(), key=lambda t: -len(t[0])):
        mp = local_root.replace("\\", "/").rstrip("/")
        if lp.lower().startswith(mp.lower()):
            relative = lp[len(mp) :]
            return sp_url.rstrip("/") + quote(relative, safe="/.-_~")

    sync_roots = _read_sync_roots()
    if not sync_roots:
        return None

    for mount_point, url_namespace in sync_roots:
        mp = mount_point.replace("\\", "/").rstrip("/")
        if lp.lower().startswith(mp.lower()):
            relative = lp[len(mp) :]  # e.g. "/folder/file.pdf"
            # URL-encode only characters that must be encoded in a URL path;
            # keep slashes, hyphens, dots, and most printable chars intact so
            # the URL remains readable.
            relative_encoded = quote(relative, safe="/.-_~")
            url = url_namespace.rstrip("/") + relative_encoded
            return url

    return None


def clear_cache() -> None:
    """Invalidate the cached registry data.

    Call this if you suspect the OneDrive sync configuration changed
    during the server's lifetime (rare, but possible).
    """
    global _sync_roots_cache, _cache_timestamp
    _sync_roots_cache = None
    _cache_timestamp = 0.0
