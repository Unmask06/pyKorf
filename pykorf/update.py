"""Update checking and installation for pyKorf."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from collections.abc import Callable
from pathlib import Path
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


_DEV_KEYWORDS = frozenset(
    ["ci", "workflow", "mypy", "ruff", "isort", "pre-commit", "pyproject", "lint", "type-check"]
)


def _clean_release_notes(body: str, max_lines: int = 15) -> str:
    r"""Convert raw GitHub release markdown into plain end-user bullet points.

    Keeps only bullet-point lines, strips markdown syntax and developer-only
    entries (CI, linting, type-checking, internal tooling).
    """
    import re

    kept: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "---", "```", "<!--")):
            continue
        if not (stripped.startswith("- ") or stripped.startswith("* ")):
            continue
        lower = stripped.lower()
        if any(kw in lower for kw in _DEV_KEYWORDS):
            continue
        # Strip bold/italic markers
        clean = re.sub(r"\*{1,2}(.*?)\*{1,2}", r"\1", stripped)
        # Strip PR/issue refs like (#123)
        clean = re.sub(r"\s*\((?:closes?\s*)?#\d+\)", "", clean)
        # Strip backtick code spans
        clean = re.sub(r"`([^`]+)`", r"\1", clean)
        # Normalise bullet to •
        clean = re.sub(r"^[-*]\s+", "• ", clean.strip())
        kept.append(clean)

    if not kept:
        return ""
    result = kept[:max_lines]
    if len(kept) > max_lines:
        result.append("  ...")
    return "\n".join(result)


def _get_install_root() -> Path:
    r"""Return the root directory of the current pyKorf installation.

    For the bat-based distribution this is %APPDATA%\pyKorf\ —
    two levels above this file:  pykorf/update.py -> pykorf/ -> install root.
    """
    return Path(__file__).parent.parent


def _deps_changed(old_pyproject: Path, new_pyproject: Path) -> bool:
    """Return True if [project.dependencies] differs between two pyproject.toml files.

    Args:
        old_pyproject: Path to the old pyproject.toml.
        new_pyproject: Path to the new pyproject.toml.

    Returns:
        True if dependencies have changed, False if identical.
    """

    def _get_deps(p: Path) -> list[str]:
        try:
            with open(p, "rb") as f:
                return tomllib.load(f).get("project", {}).get("dependencies", [])
        except Exception:
            return []

    return sorted(_get_deps(old_pyproject)) != sorted(_get_deps(new_pyproject))


def _restore_backup(install_root: Path) -> None:
    """Restore pykorf/ from pykorf.backup/ if it exists.

    Args:
        install_root: Root directory of the pyKorf installation.
    """
    backup = install_root / "pykorf.backup"
    if not backup.exists():
        return
    shutil.rmtree(install_root / "pykorf", ignore_errors=True)
    shutil.copytree(str(backup), str(install_root / "pykorf"))
    shutil.rmtree(backup, ignore_errors=True)


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
    download URL of the release asset zip needed by ``install_update()``.

    Args:
        current_version: Current pyKorf version string
        timeout: Request timeout in seconds

    Returns:
        Dict with ``latest_version``, ``release_url``, ``zipball_url``, and
        optional ``sha256_url`` keys, or None if already up-to-date or on
        network error.
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
        raw_notes = data.get("body") or ""

        # Prefer the release asset zip over GitHub's source zipball so that
        # the update installs the obfuscated distribution, not raw source.
        assets: list[dict[str, Any]] = data.get("assets", [])
        zip_asset = next(
            (
                a
                for a in assets
                if a.get("name", "").endswith(".zip") and "pykorf" in a.get("name", "").lower()
            ),
            None,
        )
        sha256_asset = next(
            (a for a in assets if a.get("name", "").endswith(".sha256")),
            None,
        )

        zipball_url: str = (
            zip_asset["browser_download_url"] if zip_asset else (data.get("zipball_url") or "")
        )
        sha256_url: str | None = sha256_asset["browser_download_url"] if sha256_asset else None

        return {
            "latest_version": _normalize_version(latest_version),
            "release_url": data.get("html_url", ""),
            "zipball_url": zipball_url,
            "sha256_url": sha256_url,
            "release_notes": _clean_release_notes(raw_notes),
        }
    return None


def install_update(
    zipball_url: str,
    progress_callback: Callable[[int, int], None] | None = None,
    sha256_url: str | None = None,
) -> tuple[bool, str]:
    """Download the release zip and install it atomically with rollback.

    Downloads the release asset zip, optionally verifies its SHA256 checksum,
    backs up the current ``pykorf/`` package, then copies the new files in.
    Skips ``.venv`` rebuild if ``[project.dependencies]`` are unchanged (fast
    path ~2 s). On any failure restores from backup.

    Args:
        zipball_url: Release asset zip URL from ``check_for_update()``.
        progress_callback: Optional ``(downloaded_bytes, total_bytes)`` callback.
        sha256_url: Optional URL to a plain-text SHA256 checksum file.

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

        # ── 1b. SHA256 integrity check ───────────────────────────────────────
        if sha256_url:
            try:
                sha256_resp = requests.get(sha256_url, timeout=10)
                sha256_resp.raise_for_status()
                expected_hash = sha256_resp.text.strip().upper()
                actual_hash = hashlib.sha256(zip_path.read_bytes()).hexdigest().upper()
                if actual_hash != expected_hash:
                    return (
                        False,
                        "Integrity check failed — download may be corrupted or tampered with.",
                    )
            except Exception as exc:
                # Non-fatal: log and continue if checksum file is unavailable
                pass

        # ── 2. Extract ───────────────────────────────────────────────────────
        extract_dir = tmp_dir / "extracted"
        try:
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(extract_dir)
        except Exception as exc:
            return False, f"Extraction failed: {exc}"

        # Release asset zips are flat (pykorf/ at root).
        # GitHub source zipballs wrap everything in a top-level folder.
        # Support both: use the subdirectory if pykorf/ is not directly present.
        extracted_root = extract_dir
        if not (extracted_root / "pykorf").exists():
            subdirs = [d for d in extract_dir.iterdir() if d.is_dir()]
            if not subdirs:
                return False, "Unexpected archive structure — no top-level folder found."
            extracted_root = subdirs[0]

        src_pkg = extracted_root / "pykorf"
        if not src_pkg.exists():
            return False, f"Archive missing 'pykorf/' directory: {extracted_root}"

        # ── 3. Backup current pykorf/ ────────────────────────────────────────
        dst_pkg = install_root / "pykorf"
        backup_pkg = install_root / "pykorf.backup"
        old_pyproject = tmp_dir / "pyproject.toml.bak"
        current_pyproject = install_root / "pyproject.toml"

        try:
            if dst_pkg.exists():
                shutil.rmtree(backup_pkg, ignore_errors=True)
                shutil.copytree(str(dst_pkg), str(backup_pkg))
            if current_pyproject.exists():
                shutil.copy2(str(current_pyproject), str(old_pyproject))
        except Exception as exc:
            shutil.rmtree(backup_pkg, ignore_errors=True)
            return False, f"Backup failed: {exc}"

        # ── 4. Install new files (with rollback on failure) ──────────────────
        try:
            shutil.copytree(str(src_pkg), str(dst_pkg), dirs_exist_ok=True)

            for fname in ("pyproject.toml", "VERSION"):
                src_file = extracted_root / fname
                if src_file.exists():
                    shutil.copy2(str(src_file), str(install_root / fname))

            # ── 5. Rebuild venv only if dependencies changed ─────────────────
            new_pyproject = install_root / "pyproject.toml"
            rebuild_venv = (
                _deps_changed(old_pyproject, new_pyproject) if old_pyproject.exists() else True
            )

            if rebuild_venv:
                venv_path = install_root / ".venv"
                uv_exe = shutil.which("uv")
                if not uv_exe:
                    raise RuntimeError("uv not found — please install uv first")

                shutil.rmtree(venv_path, ignore_errors=True)
                subprocess.run(
                    [uv_exe, "venv", "--clear", str(venv_path)],
                    cwd=str(install_root),
                    capture_output=True,
                    timeout=60,
                    check=True,
                )

                venv_python = (
                    venv_path / "Scripts" / "python.exe"
                    if sys.platform == "win32"
                    else venv_path / "bin" / "python"
                )
                result = subprocess.run(
                    [uv_exe, "pip", "install", "--python", str(venv_python), "-e", ".", "--quiet"],
                    cwd=str(install_root),
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode != 0:
                    error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
                    raise RuntimeError(f"Reinstall failed: {error_msg}")

        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode() if exc.stderr else "Unknown error"
            _restore_backup(install_root)
            if old_pyproject.exists():
                shutil.copy2(str(old_pyproject), str(current_pyproject))
            return False, f"Failed to create venv: {stderr}"
        except subprocess.TimeoutExpired:
            _restore_backup(install_root)
            if old_pyproject.exists():
                shutil.copy2(str(old_pyproject), str(current_pyproject))
            return False, "Reinstall timed out."
        except Exception as exc:
            _restore_backup(install_root)
            if old_pyproject.exists():
                shutil.copy2(str(old_pyproject), str(current_pyproject))
            return False, f"Update failed: {exc}"

        # ── 6. Cleanup backup ────────────────────────────────────────────────
        shutil.rmtree(backup_pkg, ignore_errors=True)

        return True, "Update complete — close and reopen pyKorf to use the new version."

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
