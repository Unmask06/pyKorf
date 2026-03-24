"""Update checking and installation for pyKorf."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Callable

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


def _get_install_root() -> Path:
    r"""Return the root directory of the current pyKorf installation.

    For the bat-based distribution this is %APPDATA%\pyKorf\ —
    two levels above this file:  pykorf/update.py -> pykorf/ -> install root.
    """
    return Path(__file__).parent.parent


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
    """Check if an update is available.

    Makes a single GitHub API call and returns update info including the
    zipball URL needed by ``install_update()``.

    Args:
        current_version: Current pyKorf version string
        timeout: Request timeout in seconds

    Returns:
        Dict with ``latest_version``, ``release_url``, and ``zipball_url``
        keys, or None if already up-to-date or on network error.
    """
    try:
        response = requests.get(GITHUB_API_URL, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return None

    latest_version = data.get("tag_name")
    if not latest_version:
        return None

    if _compare_versions(current_version, latest_version) < 0:
        return {
            "latest_version": _normalize_version(latest_version),
            "release_url": data.get("html_url", ""),
            "zipball_url": data.get("zipball_url", ""),
        }
    return None


def install_update(
    zipball_url: str,
    progress_callback: Callable[[int, int], None] | None = None,
) -> tuple[bool, str]:
    """Download the release zip and install it in place.

    Downloads the GitHub release zipball, extracts it to a temp directory,
    copies ``pykorf/``, ``pyproject.toml``, and ``VERSION`` into the current
    installation root, then reinstalls with ``pip install -e .``.

    Args:
        zipball_url: GitHub zipball URL from ``check_for_update()``.
        progress_callback: Optional ``(downloaded_bytes, total_bytes)`` callback.

    Returns:
        Tuple of ``(success, message)``.
    """
    install_root = _get_install_root()
    tmp_dir = Path(tempfile.mkdtemp(prefix="pykorf_update_"))

    try:
        # ── 1. Download ──────────────────────────────────────────────────────
        zip_path = tmp_dir / "release.zip"
        try:
            response = requests.get(zipball_url, stream=True, timeout=60)
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0))
            downloaded = 0
            with open(zip_path, "wb") as fh:
                for chunk in response.iter_content(chunk_size=65536):
                    fh.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total)
        except Exception as exc:
            return False, f"Download failed: {exc}"

        # ── 2. Extract ───────────────────────────────────────────────────────
        extract_dir = tmp_dir / "extracted"
        try:
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(extract_dir)
        except Exception as exc:
            return False, f"Extraction failed: {exc}"

        # GitHub zips contain a single top-level folder (e.g. pykorf-0.3.3/)
        subdirs = [d for d in extract_dir.iterdir() if d.is_dir()]
        if not subdirs:
            return False, "Unexpected archive structure — no top-level folder found."
        extracted_root = subdirs[0]

        # ── 3. Copy files into install root ──────────────────────────────────
        src_pkg = extracted_root / "pykorf"
        if not src_pkg.exists():
            return False, f"Archive missing 'pykorf/' directory: {extracted_root}"

        try:
            dst_pkg = install_root / "pykorf"
            shutil.copytree(str(src_pkg), str(dst_pkg), dirs_exist_ok=True)

            for fname in ("pyproject.toml", "VERSION"):
                src_file = extracted_root / fname
                if src_file.exists():
                    shutil.copy2(str(src_file), str(install_root / fname))
        except Exception as exc:
            return False, f"File copy failed: {exc}"

        # ── 4. Reinstall in place ────────────────────────────────────────────
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", ".", "--quiet"],
                cwd=str(install_root),
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
                return False, f"Reinstall failed: {error_msg}"
        except subprocess.TimeoutExpired:
            return False, "Reinstall timed out."
        except Exception as exc:
            return False, f"Reinstall failed: {exc}"

        return True, "Update complete — close and reopen pyKorf to use the new version."

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
