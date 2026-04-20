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
    uninstall        - Remove app (preserve data)
    reinstall        - Full reinstall from failure state

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
import re
import shutil
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

APPDATA_DIR = Path(os.environ.get("APPDATA", "")) / "pyKorf"
VENV_DIR = APPDATA_DIR / ".venv"
VERSION_FILE = APPDATA_DIR / "VERSION"
SIGNATURE_FILE = APPDATA_DIR / ".venv_signature"
LAST_CHECK_FILE = APPDATA_DIR / ".last_update_check"
GITHUB_API_URL = "https://api.github.com/repos/Unmask06/pykorf/releases/latest"
GITHUB_RELEASE_URL = "https://github.com/Unmask06/pykorf/releases/latest/download"

UPDATE_CHECK_INTERVAL = timedelta(hours=12)

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
    parser.add_argument("--full", action="store_true", help="Full uninstall (removes data)")
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
        ensure_last_check_file()
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
    ensure_last_check_file()
    write_version_from_pyproject()

    log.info("OK  Installation complete")
    return 0


def cmd_launch(port: int, debug: bool, no_debug: bool, force_update: bool) -> int:
    """Main launch flow: check update, repair, start app.

    If venv is broken, ALWAYS check for updates (force=True) before repair.
    If venv is OK, use normal interval-based update check.
    """
    venv_ok = venv_is_valid()

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

    return start_app(port, debug, no_debug)


def should_check_update() -> bool:
    """Return True if we haven't checked in 12 hours."""
    if not LAST_CHECK_FILE.exists():
        return True

    try:
        content = LAST_CHECK_FILE.read_text().strip()
        if not content:
            return True
        last_check = datetime.fromisoformat(content)
        return datetime.now() - last_check >= UPDATE_CHECK_INTERVAL
    except Exception:
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

    def fetch() -> dict:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            latest_version = data.get("tag_name", "").lstrip("v")
            return {
                "latest": latest_version,
                "current": get_installed_version(),
                "available": latest_version != get_installed_version(),
                "zip_url": f"{GITHUB_RELEASE_URL}/pykorf-v{get_bat_major()}.zip",
                "bat_url": f"{GITHUB_RELEASE_URL}/pykorf.bat",
            }

    success, result = retry_operation(fetch)

    if success:
        ensure_last_check_file()
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

    zip_path = APPDATA_DIR / "_update.zip"
    extract_dir = APPDATA_DIR / "_update_extract"

    log.info("Downloading update...")

    success, error = retry_operation(lambda: download_file(zip_url, zip_path))

    if not success:
        log.error("Update download failed")
        log.debug(f"URL: {zip_url}")
        log.debug(f"Error: {error}")
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

    overlay_update(extract_dir)

    zip_path.unlink(missing_ok=True)
    shutil.rmtree(extract_dir, ignore_errors=True)

    old_sig = read_signature()
    new_sig = compute_signature()

    if old_sig != new_sig:
        log.info("Dependencies changed, rebuilding venv...")
        result = repair_venv()
        if result != 0:
            log.error("Venv rebuild failed after update")
            return 1
    else:
        log.debug("Dependencies unchanged, skipping venv rebuild")

    write_signature()
    write_version(update_info.get("latest", ""))
    ensure_last_check_file()

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

    for item in extract_dir.iterdir():
        if item.name in preserve:
            continue

        dest = APPDATA_DIR / item.name

        if dest.exists():
            if dest.is_dir():
                shutil.rmtree(dest, ignore_errors=True)
            else:
                dest.unlink(missing_ok=True)

        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)


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
    result = subprocess.run(
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


def compute_signature() -> str:
    """Hash dependency-relevant state."""
    pyproject_path = APPDATA_DIR / "pyproject.toml"

    if not pyproject_path.exists():
        return ""

    content = pyproject_path.read_bytes()
    content = re.sub(rb'^version = "[^"]+"\n', b"", content, flags=re.MULTILINE)

    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    bat_major = get_bat_major()
    content += f"\nPY={py_version}\nBAT_MAJOR={bat_major}\n".encode()

    return hashlib.sha256(content).hexdigest()


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
    update_info = get_update_info(force=force)

    if update_info:
        current = update_info.get("current", "unknown")
        latest = update_info.get("latest", "unknown")
        available = update_info.get("available", False)

        if available:
            log.info(f"Update available: {current} -> {latest}")
        else:
            log.info(f"No update available (current: {current})")

        log.debug(f"Details: {update_info}")
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
    """Remove app, preserve data unless --full."""
    if not APPDATA_DIR.exists():
        log.info("pyKorf is not installed")
        return 0

    preserve = [] if full else ["data", "config.json"]

    log.info("Removing application...")

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

    if full:
        shutil.rmtree(APPDATA_DIR, ignore_errors=True)
        log.info("OK  pyKorf completely removed")
    else:
        log.info("OK  Application removed (data preserved)")

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

    zip_url = f"{GITHUB_RELEASE_URL}/pykorf-v{get_bat_major()}.zip"
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
    ensure_last_check_file()
    write_version_from_pyproject()

    log.info("OK  Reinstall complete")
    return 0


def get_installed_version() -> str:
    """Read VERSION file."""
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text().strip()
    return "0.0.0"


def write_version(version: str) -> None:
    """Write VERSION file."""
    if version:
        VERSION_FILE.write_text(version)


def write_version_from_pyproject() -> None:
    """Extract version from pyproject.toml and write VERSION file."""
    pyproject_path = APPDATA_DIR / "pyproject.toml"

    if not pyproject_path.exists():
        return

    try:
        import tomllib

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            version = data.get("project", {}).get("version", "")
            if version:
                VERSION_FILE.write_text(version)
    except Exception:
        pass


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


def ensure_last_check_file() -> None:
    """Create/update last check timestamp."""
    LAST_CHECK_FILE.write_text(datetime.now().isoformat())


def get_bat_major() -> str:
    """Extract BAT_MAJOR from bat_version.txt or pyproject.toml."""
    bat_version_file = APPDATA_DIR / "bat_version.txt"

    if bat_version_file.exists():
        version = bat_version_file.read_text().strip()
        return version.split(".")[0] if version else "0"

    pyproject_path = APPDATA_DIR / "pyproject.toml"

    if pyproject_path.exists():
        try:
            import tomllib

            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
                launcher = data.get("tool", {}).get("pykorf", {}).get("launcher", {})
                bat_major = launcher.get("bat-major", "0")
                return str(bat_major)
        except Exception:
            pass

    return "0"


if __name__ == "__main__":
    sys.exit(main())
