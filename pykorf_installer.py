#!/usr/bin/env python3
"""pyKorf Installer - Standalone installation helper.

Uses ONLY stdlib (no external dependencies).
Called by pykorf.bat using global Python: py -3.13 pykorf_installer.py <cmd>

Commands:
    install          - First-time installation (create venv, pip install)
    launch           - Check update, repair if needed, start app
    check-update     - Query GitHub API, compare versions
    apply-update     - Download and apply update from GitHub
    repair-venv      - Rebuild/reinstall venv if needed
    uninstall        - Remove app only (preserves data/config - no confirmation)
    reinstall        - Full reinstall from failure state

Flags:
    --full           - Full uninstall (removes everything, requires confirmation)

Exit Codes:
    0 - Success
    1 - Error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import time
import traceback
import urllib.request
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

APPDATA_DIR = Path(os.environ.get("APPDATA", "")) / "pyKorf"
VENV_DIR = APPDATA_DIR / ".venv"
VERSION_FILE = APPDATA_DIR / "VERSION"
SIGNATURE_FILE = APPDATA_DIR / ".venv_signature"
GITHUB_API_URL = "https://api.github.com/repos/Unmask06/pykorf/releases/latest"
GITHUB_RELEASE_URL = "https://github.com/Unmask06/pykorf/releases/latest/download"

MAX_RETRIES = 3
RETRY_DELAY_BASE = 5
API_TIMEOUT = 15
DOWNLOAD_TIMEOUT = 120
APP_STARTUP_WAIT = 10


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging with minimal output for users, detailed for errors."""
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "  %(message)s" if not verbose else "  %(levelname)s: %(message)s"

    logging.basicConfig(
        level=level,
        format=fmt,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger("installer")

    if verbose:
        logger.debug("Verbose mode enabled")
        logger.debug(f"APPDATA_DIR: {APPDATA_DIR}")
        logger.debug(
            f"Python: {sys.executable} ({sys.version_info.major}.{sys.version_info.minor})"
        )

    return logger


log: logging.Logger = logging.getLogger("installer")


def download_file(url: str, dest: Path, timeout: int = DOWNLOAD_TIMEOUT) -> None:
    """Download file with timeout using urlopen."""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        dest.write_bytes(resp.read())


def retry_operation(
    func: Callable[[], Any],
    retries: int = MAX_RETRIES,
    delay_base: int = RETRY_DELAY_BASE,
) -> tuple[bool, Any]:
    """Execute operation with retry logic. Returns (success, result_or_error)."""
    last_error = None

    for attempt in range(retries):
        try:
            result = func()
            return True, result
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                log.debug(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {delay_base * (attempt + 1)}s..."
                )
                time.sleep(delay_base * (attempt + 1))

    return False, last_error


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="pyKorf Installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "command",
        choices=[
            "install",
            "launch",
            "check-update",
            "apply-update",
            "repair-venv",
            "uninstall",
            "reinstall",
        ],
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Full uninstall (removes all data, requires confirmation)",
    )
    parser.add_argument("--port", type=int, default=8000, help="Port for web UI")
    parser.add_argument("--debug", action="store_true", help="Run app in debug mode")
    parser.add_argument("--no-debug", action="store_true", help="Run app without debug output")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument(
        "--force-update", action="store_true", help="Force update check (skip interval)"
    )
    args = parser.parse_args()

    global log
    log = setup_logging(args.verbose)

    commands = {
        "install": lambda: cmd_install(),
        "launch": lambda: cmd_launch(args.port, args.debug, args.no_debug, args.force_update),
        "check-update": lambda: cmd_check_update(args.force_update),
        "apply-update": lambda: cmd_apply_update(args.force_update),
        "repair-venv": lambda: cmd_repair_venv(),
        "uninstall": lambda: cmd_uninstall(args.full),
        "reinstall": lambda: cmd_reinstall(),
    }

    try:
        return commands[args.command]()
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        if args.verbose:
            log.debug(traceback.format_exc())
        return 1


def cmd_install() -> int:
    """First-time install or repair-mode for existing users."""
    if not APPDATA_DIR.exists():
        APPDATA_DIR.mkdir(parents=True, exist_ok=True)

    if VENV_DIR.exists() and venv_is_valid():
        log.info("Detected existing installation")
        write_signature()
        log.info("OK  Installation valid")
        return 0

    if VENV_DIR.exists():
        log.info("Existing venv needs repair")
        return repair_venv()

    log.info("Creating virtual environment...")

    success, error = retry_operation(
        lambda: subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            check=True,
            capture_output=True,
        )
    )

    if not success:
        log.error("Failed to create virtual environment")
        if error:
            log.debug(f"Error details: {error}")
        return 1

    if not VENV_DIR.joinpath("Scripts/python.exe").exists():
        log.error("Venv creation incomplete - python.exe missing")
        return 1

    log.info("Installing dependencies...")

    success, error = retry_operation(pip_install)

    if not success:
        log.error("Failed to install dependencies")
        if error:
            log.debug(f"Error details: {error}")
        return 1

    write_signature()
    write_version_from_pyproject()

    log.info("OK  Installation complete")
    return 0


def cmd_launch(port: int, debug: bool, no_debug: bool, force_update: bool) -> int:
    """Main launch flow: check update, repair, start app.

    If venv is broken, ALWAYS check for updates (force=True) before repair.
    If venv is OK, use normal interval-based update check.
    """
    venv_ok = venv_is_valid()
    log.debug(f"Venv valid: {venv_ok}")

    if not venv_ok:
        log.info("Venv needs repair")

        update_info = get_update_info(force=True)
        if update_info and update_info.get("available"):
            current = update_info.get("current", "unknown")
            latest = update_info.get("latest", "unknown")
            log.info(f"Update available: {current} -> {latest}")

            result = apply_update(update_info)
            if result != 0:
                log.warning("Update failed, continuing with repair")
        else:
            log.debug("No update available or check failed")

        result = repair_venv()
        if result != 0:
            log.error("Venv repair failed, attempting reinstall")
            return cmd_reinstall()

    elif should_check_update() or force_update:
        log.info("Checking for updates...")
        update_info = get_update_info(force=force_update)

        if update_info and update_info.get("available"):
            current = update_info.get("current", "unknown")
            latest = update_info.get("latest", "unknown")
            log.info(f"Update available: {current} -> {latest}")

            result = apply_update(update_info)
            if result != 0:
                log.warning("Update failed, launching existing version")
        else:
            if update_info:
                log.info(f"No update available (current: {update_info.get('current', 'unknown')})")
            else:
                log.debug("Update check returned no info")

    return start_app(port, debug, no_debug)


def should_check_update() -> bool:
    """Return True to always check for updates."""
    return True


def get_update_info(force: bool = False) -> dict | None:
    """Query GitHub API for latest release.

    Args:
        force: If True, always check (ignore interval). If False, use interval.

    Returns:
        dict with version info, or None if check failed or skipped.
    """
    if not force and not should_check_update():
        log.debug("Update check skipped (interval not elapsed)")
        return None

    current_version = get_installed_version()
    log.debug(f"Current installed version: {current_version}")

    def fetch() -> dict:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        log.debug(f"Fetching GitHub API: {GITHUB_API_URL}")
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            latest_version = data.get("tag_name", "").lstrip("v")
            log.debug(f"Latest release from GitHub: {latest_version}")
            log.debug(f"Full API response: {json.dumps(data, indent=2)}")
            return {
                "latest": latest_version,
                "current": current_version,
                "available": latest_version != current_version,
                "zip_url": f"{GITHUB_RELEASE_URL}/pykorf-latest.zip",
                "bat_url": f"{GITHUB_RELEASE_URL}/pykorf.bat",
            }

    success, result = retry_operation(fetch)

    if success:
        log.debug(f"Update check result: {result}")
        return result

    log.warning("GitHub API request failed")
    log.debug(f"Error: {result}")
    return None


def apply_update(update_info: dict) -> int:
    """Download and apply update from GitHub."""
    zip_url = update_info.get("zip_url", "")
    if not zip_url:
        log.error("No update URL available")
        return 1

    current_version = update_info.get("current", "unknown")
    latest_version = update_info.get("latest", "unknown")
    log.debug(f"Applying update: {current_version} -> {latest_version}")
    log.debug(f"Download URL: {zip_url}")

    zip_path = APPDATA_DIR / "_update.zip"
    extract_dir = APPDATA_DIR / "_update_extract"

    log.info("Downloading update...")

    success, error = retry_operation(lambda: download_file(zip_url, zip_path))

    if not success:
        log.error("Update download failed")
        log.error(f"URL: {zip_url}")
        log.error(f"Error: {error}")
        return 1

    log.info("Extracting update...")

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
    except Exception as e:
        zip_path.unlink(missing_ok=True)
        shutil.rmtree(extract_dir, ignore_errors=True)
        log.error("Update extraction failed")
        log.debug(f"Error: {e}")
        return 1

    # Read old deps BEFORE overlay (to compare properly)
    old_deps = parse_dependencies(APPDATA_DIR / "pyproject.toml")

    overlay_update(extract_dir)

    zip_path.unlink(missing_ok=True)
    shutil.rmtree(extract_dir, ignore_errors=True)

    # Read new deps AFTER overlay
    new_deps = parse_dependencies(APPDATA_DIR / "pyproject.toml")

    if old_deps != new_deps:
        log.info("Dependencies changed, syncing...")
        result = sync_dependencies()
        if result != 0:
            log.error("Dependency sync failed, attempting full rebuild...")
            result = repair_venv()
            if result != 0:
                log.error("Venv rebuild failed after update")
                return 1
    else:
        log.info("Dependencies unchanged, skipping venv operations")

    write_signature()
    write_version(update_info.get("latest", ""))

    log.info(f"OK  Updated to {update_info.get('latest', '')}")
    return 0


def overlay_update(extract_dir: Path) -> None:
    """Overlay update files, preserving data/config/venv."""
    preserve = [
        "data",
        "config.json",
        ".venv",
        ".venv_signature",
        ".last_update_check",
        "VERSION",
    ]

    log.debug(f"Overlaying update from {extract_dir}")
    log.debug(f"Preserving: {preserve}")

    for item in extract_dir.iterdir():
        if item.name in preserve:
            log.debug(f"Preserving: {item.name}")
            continue

        dest = APPDATA_DIR / item.name

        if dest.exists():
            if dest.is_dir():
                log.debug(f"Removing directory: {dest}")
                shutil.rmtree(dest, ignore_errors=True)
            else:
                log.debug(f"Removing file: {dest}")
                dest.unlink(missing_ok=True)

        if item.is_dir():
            log.debug(f"Copying directory: {item.name}")
            shutil.copytree(item, dest)
        else:
            log.debug(f"Copying file: {item.name}")
            shutil.copy2(item, dest)

    log.debug("Overlay complete")


def repair_venv() -> int:
    """Rebuild venv and reinstall dependencies."""
    if VENV_DIR.exists():
        log.debug("Removing existing venv...")
        shutil.rmtree(VENV_DIR, ignore_errors=True)

    log.info("Creating virtual environment...")

    success, error = retry_operation(
        lambda: subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            check=True,
            capture_output=True,
        )
    )

    if not success:
        log.error("Failed to create virtual environment")
        log.debug(f"Error: {error}")
        return 1

    log.info("Installing dependencies...")

    success, error = retry_operation(pip_install)

    if not success:
        log.error("Failed to install dependencies")
        log.debug(f"Error: {error}")
        return 1

    write_signature()

    log.info("OK  Venv repaired")
    return 0


def pip_install() -> None:
    """Install package using uv if available, else pip.

    Tries uv first for faster installation (2-10x faster than pip).
    Falls back to pip if uv is not available.
    """
    python_exe = VENV_DIR / "Scripts" / "python.exe"

    if not python_exe.exists():
        raise FileNotFoundError(f"python.exe not found: {python_exe}")

    # Try uv first (much faster)
    try:
        subprocess.run(
            ["uv", "pip", "install", "-e", str(APPDATA_DIR)],
            cwd=str(APPDATA_DIR),
            capture_output=True,
            check=True,
            timeout=300,
        )
        log.debug("Installed using uv")
        return
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        log.debug("uv not available or failed, falling back to pip")

    # Fallback to pip
    subprocess.run(
        [str(python_exe), "-m", "pip", "install", "-e", str(APPDATA_DIR), "--quiet"],
        cwd=str(APPDATA_DIR),
        capture_output=True,
        check=True,
    )


def venv_is_valid() -> bool:
    """Check if venv exists and pykorf is installed."""
    python_exe = VENV_DIR / "Scripts" / "python.exe"
    pykorf_exe = VENV_DIR / "Scripts" / "pykorf.exe"

    if not python_exe.exists() or not pykorf_exe.exists():
        return False

    current_sig = compute_signature()
    stored_sig = read_signature()

    if not stored_sig:
        return True

    return current_sig == stored_sig


def parse_dependencies(pyproject_path: Path) -> dict[str, list[str]]:
    """Extract dependencies from pyproject.toml, normalized and sorted.

    Returns dict with keys: 'main', 'dev', 'docs', etc. from dependency-groups.
    """
    if not pyproject_path.exists():
        return {}

    try:
        import tomllib

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
    except Exception:
        return {}

    deps: dict[str, list[str]] = {}

    # Main dependencies from [project.dependencies]
    main_deps = data.get("project", {}).get("dependencies", [])
    if main_deps:
        deps["main"] = sorted([d.strip() for d in main_deps if d.strip()])

    # Dependency groups from [dependency-groups]
    dep_groups = data.get("dependency-groups", {})
    for group_name, group_deps in dep_groups.items():
        if group_deps:
            deps[group_name] = sorted([d.strip() for d in group_deps if d.strip()])

    # Default groups from [tool.uv]
    uv_config = data.get("tool", {}).get("uv", {})
    default_groups = uv_config.get("default-groups", [])
    if default_groups:
        deps["uv_default_groups"] = sorted(default_groups)

    return deps


def compute_signature() -> str:
    """Hash only dependency-relevant content (ignores version, formatting, comments)."""
    deps = parse_dependencies(APPDATA_DIR / "pyproject.toml")

    if not deps:
        return ""

    # Include Python version in signature since deps may differ per version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"

    # Create canonical string representation
    parts = [f"PY={py_version}"]
    for key in sorted(deps.keys()):
        parts.append(f"[{key}]")
        parts.extend(deps[key])

    content = "\n".join(parts)
    return hashlib.sha256(content.encode()).hexdigest()


def deps_changed() -> bool:
    """Check if dependencies changed since last signature was stored."""
    current_sig = compute_signature()
    stored_sig = read_signature()

    if not stored_sig:
        return True

    return current_sig != stored_sig


def sync_dependencies() -> int:
    """Sync dependencies using uv sync (incremental, no full rebuild).

    Tries uv sync first, falls back to pip install if uv unavailable.
    """
    python_exe = VENV_DIR / "Scripts" / "python.exe"

    if not python_exe.exists():
        log.error("Python not found in venv")
        return 1

    # Try uv sync first (much faster, handles incremental updates)
    try:
        result = subprocess.run(
            ["uv", "sync"],
            cwd=str(APPDATA_DIR),
            capture_output=True,
            timeout=300,
        )
        if result.returncode == 0:
            log.debug("Dependencies synced using uv")
            return 0
        log.debug(f"uv sync failed with code {result.returncode}")
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        log.debug(f"uv sync unavailable or timed out: {e}")

    # Fallback: pip install -e . --quiet
    try:
        result = subprocess.run(
            [str(python_exe), "-m", "pip", "install", "-e", str(APPDATA_DIR), "--quiet"],
            cwd=str(APPDATA_DIR),
            capture_output=True,
            timeout=300,
        )
        if result.returncode == 0:
            log.debug("Dependencies synced using pip")
            return 0
        log.error(f"pip install failed with code {result.returncode}")
        return 1
    except subprocess.TimeoutExpired:
        log.error("pip install timed out")
        return 1


def start_app(port: int, debug: bool, no_debug: bool) -> int:
    """Launch pykorf.exe and exit gracefully."""
    pykorf_exe = VENV_DIR / "Scripts" / "pykorf.exe"

    if not pykorf_exe.exists():
        log.error("pykorf.exe not found")
        return handle_launch_failure(-1, port, debug, no_debug, "pykorf.exe missing")

    args = [str(pykorf_exe)]
    if debug:
        args.append("--debug")
    if no_debug:
        args.append("--no-debug")
    args.extend(["--port", str(port)])

    log.info("Launching pyKorf...")

    try:
        proc = subprocess.Popen(args, cwd=str(APPDATA_DIR))
    except Exception as e:
        return handle_launch_failure(-1, port, debug, no_debug, str(e))

    for _ in range(APP_STARTUP_WAIT):
        time.sleep(1)
        if proc.poll() is not None:
            break

    if proc.poll() is None:
        log.info(f"OK  pyKorf started (port {port})")
        return 0

    return handle_launch_failure(proc.returncode or -1, port, debug, no_debug)


def handle_launch_failure(
    exit_code: int, port: int, debug: bool, no_debug: bool, error_msg: str | None = None
) -> int:
    """Handle app launch failure with repair/reinstall cascade."""
    log.warning(f"pyKorf exited with code {exit_code}, attempting repair...")
    if error_msg:
        log.debug(f"Error: {error_msg}")

    result = repair_venv()

    if result == 0:
        log.info("Venv repaired, retrying launch...")

        pykorf_exe = VENV_DIR / "Scripts" / "pykorf.exe"
        args = [str(pykorf_exe)]
        if debug:
            args.append("--debug")
        if no_debug:
            args.append("--no-debug")
        args.extend(["--port", str(port)])

        try:
            proc = subprocess.Popen(args, cwd=str(APPDATA_DIR))
        except Exception as e:
            return handle_reinstall(port, debug, no_debug, f"Retry launch failed: {e}")

        for _ in range(APP_STARTUP_WAIT):
            time.sleep(1)
            if proc.poll() is not None:
                break

        if proc.poll() is None:
            log.info(f"OK  pyKorf started after repair (port {port})")
            return 0

        return handle_reinstall(
            port, debug, no_debug, f"Launch failed after repair: {proc.returncode}"
        )

    return handle_reinstall(port, debug, no_debug, "Repair failed")


def handle_reinstall(port: int, debug: bool, no_debug: bool, reason: str) -> int:
    """Attempt full reinstall when repair fails."""
    log.warning("Repair failed, attempting full reinstall...")
    log.debug(f"Reason: {reason}")

    result = cmd_reinstall()

    if result == 0:
        pykorf_exe = VENV_DIR / "Scripts" / "pykorf.exe"
        args = [str(pykorf_exe)]
        if debug:
            args.append("--debug")
        if no_debug:
            args.append("--no-debug")
        args.extend(["--port", str(port)])

        try:
            proc = subprocess.Popen(args, cwd=str(APPDATA_DIR))
            for _ in range(APP_STARTUP_WAIT):
                time.sleep(1)
                if proc.poll() is not None:
                    break

            if proc.poll() is None:
                log.info(f"OK  pyKorf started after reinstall (port {port})")
                return 0
        except Exception:
            pass

    log.error("pyKorf failed to start after reinstall")
    return 1


def cmd_check_update(force: bool = False) -> int:
    """Query GitHub API and show update info."""
    log.debug(f"Checking for updates (force={force})")
    update_info = get_update_info(force=force)

    if update_info:
        current = update_info.get("current", "unknown")
        latest = update_info.get("latest", "unknown")
        available = update_info.get("available", False)

        if available:
            log.info(f"Update available: {current} -> {latest}")
        else:
            log.info(f"No update available (current: {current})")

        log.debug(f"Full update info: {json.dumps(update_info, indent=2)}")
        return 0

    log.error("Failed to check for updates")
    return 1


def cmd_apply_update(force: bool = False) -> int:
    """Apply update (called manually or by launch)."""
    update_info = get_update_info(force=force)

    if not update_info:
        log.error("Could not get update info")
        return 1

    if not update_info.get("available"):
        log.info(f"No update available (current: {update_info['current']})")
        return 0

    return apply_update(update_info)


def cmd_repair_venv() -> int:
    """Manual venv repair command."""
    return repair_venv()


def cmd_uninstall(full: bool) -> int:
    """Remove app, preserve data unless --full (requires confirmation)."""
    if not APPDATA_DIR.exists():
        log.info("pyKorf is not installed")
        return 0

    if full:
        log.warning(
            "Full uninstall will remove the configuration and preferences of the application"
        )
        log.warning("")
        log.warning("This action cannot be undone!")
        log.warning("")

        try:
            response = input("Type 'yes' to confirm full uninstall: ").strip().lower()
            if response not in ("yes", "y"):
                log.info("Cancelled - no changes made")
                return 0
        except (EOFError, KeyboardInterrupt):
            log.info("Cancelled - no changes made")
            return 0

        log.info("Removing everything...")

        shutil.rmtree(APPDATA_DIR, ignore_errors=True)
        log.info("OK  pyKorf completely removed")
        return 0

    preserve = ["data", "config.json"]

    log.info("Removing application (preserving data)...")

    for item in list(APPDATA_DIR.iterdir()):
        if item.name in preserve:
            continue

        try:
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink(missing_ok=True)
        except Exception:
            pass

    log.info("OK  Application removed (data preserved)")
    log.info("Run with --full to remove everything including data")

    return 0


def cmd_reinstall() -> int:
    """Full reinstall from failure state."""
    log.info("Starting full reinstall...")

    backup_dir = Path(os.environ.get("TEMP", "")) / "pykorf_reinstall_bak"
    backup_dir.mkdir(parents=True, exist_ok=True)

    preserved = {}

    if APPDATA_DIR.joinpath("data").exists():
        try:
            shutil.copytree(APPDATA_DIR / "data", backup_dir / "data")
            preserved["data"] = True
        except Exception:
            preserved["data"] = False

    if APPDATA_DIR.joinpath("config.json").exists():
        try:
            shutil.copy(APPDATA_DIR / "config.json", backup_dir / "config.json")
            preserved["config.json"] = True
        except Exception:
            preserved["config.json"] = False

    shutil.rmtree(APPDATA_DIR, ignore_errors=True)
    APPDATA_DIR.mkdir(parents=True, exist_ok=True)

    log.info("Downloading latest release...")

    zip_url = f"{GITHUB_RELEASE_URL}/pykorf-latest.zip"
    zip_path = Path(os.environ.get("TEMP", "")) / "pykorf_reinstall.zip"

    success, error = retry_operation(lambda: download_file(zip_url, zip_path))

    if not success:
        log.error("Failed to download release")
        log.debug(f"URL: {zip_url}")
        log.debug(f"Error: {error}")
        return 1

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(APPDATA_DIR)
        zip_path.unlink(missing_ok=True)
    except Exception as e:
        zip_path.unlink(missing_ok=True)
        log.error("Failed to extract release")
        log.debug(f"Error: {e}")
        return 1

    if backup_dir.joinpath("data").exists():
        try:
            shutil.copytree(backup_dir / "data", APPDATA_DIR / "data", dirs_exist_ok=True)
        except Exception:
            pass

    if backup_dir.joinpath("config.json").exists():
        try:
            shutil.copy(backup_dir / "config.json", APPDATA_DIR / "config.json")
        except Exception:
            pass

    shutil.rmtree(backup_dir, ignore_errors=True)

    log.info("Creating fresh installation...")

    success, error = retry_operation(
        lambda: subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            check=True,
            capture_output=True,
        )
    )

    if not success:
        log.error("Failed to create venv")
        log.debug(f"Error: {error}")
        return 1

    success, error = retry_operation(pip_install)

    if not success:
        log.error("Failed to install dependencies")
        log.debug(f"Error: {error}")
        return 1

    write_signature()
    write_version_from_pyproject()

    log.info("OK  Reinstall complete")
    return 0


def get_venv_package_version() -> str | None:
    """Query the actual installed pykorf package version from venv."""
    python_exe = VENV_DIR / "Scripts" / "python.exe"
    if not python_exe.exists():
        return None

    try:
        result = subprocess.run(
            [
                str(python_exe),
                "-c",
                "from importlib.metadata import version; print(version('pykorf'))",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            ver = result.stdout.strip()
            if ver:
                return ver
    except Exception:
        pass

    return None


def get_installed_version() -> str:
    """Read actual installed package version, fallback to VERSION file."""
    pkg_version = get_venv_package_version()
    if pkg_version:
        log.debug(f"Package version from venv: {pkg_version}")
        return pkg_version

    if VERSION_FILE.exists():
        version = VERSION_FILE.read_text().strip()
        log.debug(f"VERSION file exists, content: '{version}'")
        return version
    log.debug("VERSION file does not exist")
    return "0.0.0"


def write_version(version: str) -> None:
    """Write VERSION file."""
    if version:
        VERSION_FILE.write_text(version)
        log.debug(f"VERSION file written: {version}")


def write_version_from_pyproject() -> None:
    """Extract version from pyproject.toml and write VERSION file."""
    pyproject_path = APPDATA_DIR / "pyproject.toml"

    if not pyproject_path.exists():
        log.debug(f"pyproject.toml not found at {pyproject_path}")
        return

    try:
        import tomllib

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            version = data.get("project", {}).get("version", "")
            log.debug(f"Version from pyproject.toml: {version}")
            if version:
                VERSION_FILE.write_text(version)
                log.debug(f"VERSION file written from pyproject: {version}")
    except Exception as e:
        log.debug(f"Failed to read version from pyproject.toml: {e}")


def read_signature() -> str:
    """Read stored signature."""
    if SIGNATURE_FILE.exists():
        return SIGNATURE_FILE.read_text().strip()
    return ""


def write_signature() -> None:
    """Write current signature."""
    sig = compute_signature()
    if sig:
        SIGNATURE_FILE.write_text(sig)


if __name__ == "__main__":
    sys.exit(main())
