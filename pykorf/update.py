"""Update checking functionality for pyKorf."""

import subprocess
import sys
from typing import Any

import requests

GITHUB_REPO = "Unmask06/pykorf"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def _normalize_version(version: str) -> str:
    """Strip leading 'v' from version string."""
    return version.lstrip("v")


def _parse_version(version: str) -> tuple[int, ...]:
    """Parse version string into tuple of integers."""
    normalized = _normalize_version(version)
    parts = normalized.split(".")
    result = []
    for part in parts:
        try:
            result.append(int(part))
        except ValueError:
            break
    return tuple(result) if result else (0,)


def _compare_versions(current: str, latest: str) -> int:
    """Compare semantic versions.

    Returns:
        -1 if current < latest
         0 if current == latest
         1 if current > latest
    """
    current_parts = _parse_version(current)
    latest_parts = _parse_version(latest)

    if current_parts < latest_parts:
        return -1
    elif current_parts > latest_parts:
        return 1
    return 0


def get_latest_version(timeout: float = 3.0) -> str | None:
    """Fetch latest release version from GitHub.

    Args:
        timeout: Request timeout in seconds

    Returns:
        Version string (e.g., "v0.3.0") or None on error
    """
    try:
        response = requests.get(GITHUB_API_URL, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data.get("tag_name")
    except Exception:
        return None


def check_for_update(current_version: str, timeout: float = 3.0) -> dict[str, Any] | None:
    """Check if update is available.

    Args:
        current_version: Current pyKorf version string
        timeout: Request timeout in seconds

    Returns:
        Dict with 'latest_version' and 'release_url' or None if up-to-date/error
    """
    latest_version = get_latest_version(timeout)
    if not latest_version:
        return None

    if _compare_versions(current_version, latest_version) < 0:
        try:
            response = requests.get(GITHUB_API_URL, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            release_url = data.get("html_url", "")
        except Exception:
            release_url = ""

        return {
            "latest_version": _normalize_version(latest_version),
            "release_url": release_url,
        }
    return None


def install_update() -> tuple[bool, str]:
    """Run pip install --upgrade pykorf.

    Returns:
        Tuple of (success, message)
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pykorf"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            return True, "Update complete!"
        else:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            return False, f"Update failed: {error_msg}"

    except subprocess.TimeoutExpired:
        return False, "Update timed out"
    except Exception as e:
        return False, f"Update failed: {e!s}"
