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

from pykorf.core.log import get_logger


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

    logger = get_logger(__name__)

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
    from pykorf.app.operation.config.preferences import get_sp_overrides

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


def get_local_path_from_sp_url(sp_url: str) -> str | None:
    r"""Convert a SharePoint URL to its local OneDrive-synced path.

    Reads the user-configured SharePoint overrides and returns the
    corresponding local path for SharePoint URLs that match a configured
    override mapping. Returns ``None`` if no match is found.

    This is the reverse operation of :func:`get_sharepoint_url`.

    Args:
        sp_url: SharePoint URL string (e.g. ``https://tenant.sharepoint.com/sites/...``).

    Returns:
        Local path string if a matching override is found, ``None`` otherwise.

    Example::

        # User configured override:
        # Local: C:\Users\alice\OneDrive - CC7\ProjectA\Documents
        # SP URL: https://cc7ges.sharepoint.com/sites/ProjectA/Documents

        local = get_local_path_from_sp_url(
            "https://cc7ges.sharepoint.com/sites/ProjectA/Documents/file.pdf"
        )
        # "C:\\Users\\alice\\OneDrive - CC7\\ProjectA\\Documents\\file.pdf"
    """
    from urllib.parse import unquote

    from pykorf.app.operation.config.preferences import get_sp_overrides

    logger = get_logger(__name__)

    # Normalize SP URL: decode, replace forward slashes with backslashes
    sp_url_normalized = unquote(sp_url).replace("/", "\\").rstrip("\\")

    # Check against user-configured overrides (most specific first)
    overrides = get_sp_overrides()
    if not overrides:
        logger.debug("no_sp_overrides_configured")
        return None

    for local_root, sp_root in sorted(overrides.items(), key=lambda t: -len(t[1])):
        sp_root_normalized = unquote(sp_root).replace("/", "\\").rstrip("\\")
        if sp_url_normalized.lower().startswith(sp_root_normalized.lower()):
            relative = sp_url_normalized[len(sp_root_normalized) :].lstrip("\\/")

            # Security: Prevent path traversal attacks
            # Normalize and verify the resulting path stays within local_root
            safe_path = Path(local_root.rstrip("\\/")).joinpath(relative)
            try:
                safe_path_resolved = safe_path.resolve()
                local_root_resolved = Path(local_root.rstrip("\\/")).resolve()
                if not str(safe_path_resolved).startswith(str(local_root_resolved)):
                    logger.warning(
                        "path_traversal_attempt_blocked",
                        sp_url=sp_url,
                        attempted_path=str(safe_path),
                    )
                    return None
            except (OSError, ValueError) as e:
                logger.warning(
                    "path_normalization_failed",
                    sp_url=sp_url,
                    error=str(e),
                )
                return None

            local_path = str(safe_path)
            logger.info(
                "sp_url_converted_to_local",
                sp_url=sp_url,
                local_path=local_path,
            )
            return local_path

    logger.debug("sp_url_no_matching_override", sp_url=sp_url)
    return None
