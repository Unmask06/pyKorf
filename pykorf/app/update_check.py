"""Background GitHub release check for in-app update notifications."""

from __future__ import annotations

import json
import threading
import time
import urllib.request

from pykorf import __version__

_GITHUB_API = "https://api.github.com/repos/Unmask06/pykorf/releases/latest"
_CACHE_TTL = 3600  # seconds

_latest_version: str | None = None
_cache_time: float = 0.0
_lock = threading.Lock()
_refreshing = False


def _fetch_latest() -> str | None:
    """Call GitHub API and return the latest version string, or None on failure."""
    try:
        req = urllib.request.Request(
            _GITHUB_API,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "pykorf"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        tag: str = data.get("tag_name", "")
        return tag.lstrip("v") or None
    except Exception:
        return None


def _refresh() -> None:
    global _latest_version, _cache_time, _refreshing
    latest = _fetch_latest()
    with _lock:
        _latest_version = latest
        _cache_time = time.monotonic()
        _refreshing = False


def get_latest_version() -> str | None:
    """Return the cached latest version, triggering a background refresh if stale."""
    global _refreshing
    with _lock:
        stale = (time.monotonic() - _cache_time) > _CACHE_TTL
        already_running = _refreshing
        if stale and not already_running:
            _refreshing = True
    if stale and not already_running:
        threading.Thread(target=_refresh, daemon=True).start()
    with _lock:
        return _latest_version


def is_update_available() -> bool:
    """Return True if a newer version exists on GitHub."""
    latest = get_latest_version()
    if not latest:
        return False
    try:
        from packaging.version import Version

        return Version(latest) > Version(__version__)
    except Exception:
        return latest != __version__


def prefetch() -> None:
    """Kick off an immediate background fetch at app startup to warm the cache."""
    threading.Thread(target=_refresh, daemon=True).start()
