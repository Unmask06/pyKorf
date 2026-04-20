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

JSON Output Format:
    {"status": "success|error|warning|info", "message": "...", "action": "...", "details": {...}}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

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


def download_file(url: str, dest: Path, timeout: int = DOWNLOAD_TIMEOUT) -> None:
    """Download file with timeout using urlopen."""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        dest.write_bytes(resp.read())


def json_response(status: str, message: str, action: str, details: dict | None = None) -> dict:
    """Create standardized JSON response."""
    return {
        "status": status,
        "message": message,
        "action": action,
        "details": details or {},
        "timestamp": datetime.now().isoformat(),
    }


def print_json(response: dict) -> None:
    """Print JSON response to stdout (single line for batch parsing)."""
    print(json.dumps(response, separators=(",", ":")))


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
    parser.add_argument("--full", action="store_true", help="Full uninstall")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--no-debug", action="store_true")
    args = parser.parse_args()

    commands = {
        "install": lambda: cmd_install(),
        "launch": lambda: cmd_launch(args.port, args.debug, args.no_debug),
        "check-update": lambda: cmd_check_update(),
        "apply-update": lambda: cmd_apply_update(),
        "repair-venv": lambda: cmd_repair_venv(),
        "uninstall": lambda: cmd_uninstall(args.full),
        "reinstall": lambda: cmd_reinstall(),
    }

    try:
        response = commands[args.command]()
        print_json(response)
        return 0 if response["status"] in ("success", "info") else 1
    except Exception as e:
        print_json(
            json_response(
                "error",
                f"Unexpected error: {e}",
                args.command,
                {"exception": str(e)},
            )
        )
        return 1


def cmd_install() -> dict:
    """First-time install or repair-mode for existing users."""
    if not APPDATA_DIR.exists():
        APPDATA_DIR.mkdir(parents=True, exist_ok=True)

    if VENV_DIR.exists() and venv_is_valid():
        print_json(json_response("info", "Detected existing installation", "install"))
        ensure_last_check_file()
        write_signature()
        return json_response("success", "Installation valid", "install")

    if VENV_DIR.exists():
        print_json(json_response("info", "Existing venv needs repair", "install"))
        return repair_venv()

    print_json(json_response("info", "Creating virtual environment...", "install"))

    success, error = retry_operation(
        lambda: subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            check=True,
            capture_output=True,
        )
    )

    if not success:
        return json_response(
            "error",
            "Failed to create virtual environment",
            "install",
            {"error": str(error)},
        )

    if not VENV_DIR.joinpath("Scripts/python.exe").exists():
        return json_response(
            "error",
            "Venv creation incomplete - python.exe missing",
            "install",
        )

    print_json(json_response("info", "Installing dependencies...", "install"))

    success, error = retry_operation(pip_install)

    if not success:
        return json_response(
            "error",
            "Failed to install dependencies",
            "install",
            {"error": str(error)},
        )

    write_signature()
    ensure_last_check_file()
    write_version_from_pyproject()

    return json_response("success", "Installation complete", "install")


def cmd_launch(port: int, debug: bool, no_debug: bool) -> dict:
    """Main launch flow: check update, repair, start app."""
    if should_check_update():
        print_json(json_response("info", "Checking for updates...", "launch"))
        update_info = get_update_info()

        if update_info and update_info.get("available"):
            print_json(
                json_response(
                    "info",
                    f"Update available: {update_info['current']} → {update_info['latest']}",
                    "update",
                    update_info,
                )
            )
            result = apply_update(update_info)
            if result["status"] == "error":
                print_json(result)
                return json_response(
                    "warning",
                    "Update failed, launching existing version",
                    "launch",
                    {"update_error": result["message"]},
                )

    if not venv_is_valid():
        print_json(json_response("info", "Venv needs repair...", "launch"))
        result = repair_venv()
        if result["status"] == "error":
            print_json(result)
            return json_response(
                "error",
                "Venv repair failed, attempting reinstall",
                "launch",
                {"repair_error": result["message"]},
            )

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


def get_update_info() -> dict | None:
    """Query GitHub API for latest release with retry."""

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

    print_json(
        json_response(
            "warning",
            "GitHub API request failed",
            "check-update",
            {"error": str(result)},
        )
    )
    return None


def apply_update(update_info: dict) -> dict:
    """Download and apply update from GitHub."""
    zip_url = update_info.get("zip_url", "")
    if not zip_url:
        return json_response("error", "No update URL available", "apply-update")

    zip_path = APPDATA_DIR / "_update.zip"
    extract_dir = APPDATA_DIR / "_update_extract"

    print_json(json_response("info", "Downloading update...", "apply-update"))

    def download():
        download_file(zip_url, zip_path, timeout=DOWNLOAD_TIMEOUT)

    success, error = retry_operation(download)

    if not success:
        return json_response(
            "error",
            "Update download failed",
            "apply-update",
            {"error": str(error)},
        )

    print_json(json_response("info", "Extracting update...", "apply-update"))

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
    except Exception as e:
        zip_path.unlink(missing_ok=True)
        shutil.rmtree(extract_dir, ignore_errors=True)
        return json_response(
            "error",
            "Update extraction failed",
            "apply-update",
            {"error": str(e)},
        )

    overlay_update(extract_dir)

    zip_path.unlink(missing_ok=True)
    shutil.rmtree(extract_dir, ignore_errors=True)

    old_sig = read_signature()
    new_sig = compute_signature()

    if old_sig != new_sig:
        print_json(
            json_response("info", "Dependencies changed, rebuilding venv...", "apply-update")
        )
        result = repair_venv()
        if result["status"] == "error":
            return json_response(
                "error",
                "Venv rebuild failed after update",
                "apply-update",
                {"repair_error": result["message"]},
            )
    else:
        print_json(
            json_response("info", "Dependencies unchanged, skipping venv rebuild", "apply-update")
        )

    write_signature()
    write_version(update_info.get("latest", ""))
    ensure_last_check_file()

    return json_response(
        "success",
        f"Updated to {update_info.get('latest', '')}",
        "apply-update",
        {"version": update_info.get("latest", "")},
    )


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


def repair_venv() -> dict:
    """Rebuild venv and reinstall dependencies."""
    print_json(json_response("info", "Removing existing venv...", "repair-venv"))

    if VENV_DIR.exists():
        shutil.rmtree(VENV_DIR, ignore_errors=True)

    print_json(json_response("info", "Creating virtual environment...", "repair-venv"))

    success, error = retry_operation(
        lambda: subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            check=True,
            capture_output=True,
        )
    )

    if not success:
        return json_response(
            "error",
            "Failed to create virtual environment",
            "repair-venv",
            {"error": str(error)},
        )

    print_json(json_response("info", "Installing dependencies...", "repair-venv"))

    success, error = retry_operation(pip_install)

    if not success:
        return json_response(
            "error",
            "Failed to install dependencies",
            "repair-venv",
            {"error": str(error)},
        )

    write_signature()

    return json_response("success", "Venv repaired", "repair-venv")


def pip_install() -> None:
    """Run pip install -e . in venv."""
    python_exe = VENV_DIR / "Scripts" / "python.exe"

    if not python_exe.exists():
        raise FileNotFoundError(f"python.exe not found: {python_exe}")

    result = subprocess.run(
        [str(python_exe), "-m", "pip", "install", "-e", str(APPDATA_DIR), "--quiet"],
        cwd=str(APPDATA_DIR),
        capture_output=True,
        check=True,
    )


def pip_install_no_cache() -> None:
    """Run pip install without cache (fallback)."""
    python_exe = VENV_DIR / "Scripts" / "python.exe"

    subprocess.run(
        [
            str(python_exe),
            "-m",
            "pip",
            "install",
            "-e",
            str(APPDATA_DIR),
            "--quiet",
            "--no-cache-dir",
        ],
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


def start_app(port: int, debug: bool, no_debug: bool) -> dict:
    """Launch pykorf.exe and exit gracefully."""
    pykorf_exe = VENV_DIR / "Scripts" / "pykorf.exe"

    if not pykorf_exe.exists():
        print_json(json_response("error", "pykorf.exe not found", "launch"))
        return handle_launch_failure(9009, port, debug, no_debug)

    args = [str(pykorf_exe)]
    if debug:
        args.append("--debug")
    if no_debug:
        args.append("--no-debug")
    args.extend(["--port", str(port)])

    print_json(
        json_response(
            "info",
            "Launching pyKorf...",
            "launch",
            {"port": port},
        )
    )

    try:
        proc = subprocess.Popen(args, cwd=str(APPDATA_DIR))
    except Exception as e:
        return handle_launch_failure(-1, port, debug, no_debug, str(e))

    for _ in range(APP_STARTUP_WAIT):
        time.sleep(1)
        if proc.poll() is not None:
            break

    if proc.poll() is None:
        print_json(
            json_response(
                "success",
                "pyKorf started",
                "launch",
                {"port": port, "pid": proc.pid},
            )
        )
        sys.exit(0)

    return handle_launch_failure(proc.returncode or -1, port, debug, no_debug)


def handle_launch_failure(
    exit_code: int, port: int, debug: bool, no_debug: bool, error_msg: str | None = None
) -> dict:
    """Handle app launch failure with repair/reinstall cascade."""
    print_json(
        json_response(
            "warning",
            f"pyKorf exited with code {exit_code}, attempting repair...",
            "launch",
            {"exit_code": exit_code, "error": error_msg},
        )
    )

    result = repair_venv()

    if result["status"] == "success":
        print_json(json_response("info", "Venv repaired, retrying launch...", "launch"))

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
            print_json(
                json_response(
                    "success",
                    "pyKorf started after repair",
                    "launch",
                    {"port": port, "pid": proc.pid, "repaired": True},
                )
            )
            sys.exit(0)

        return handle_reinstall(
            port, debug, no_debug, f"Launch failed after repair: {proc.returncode}"
        )

    return handle_reinstall(port, debug, no_debug, f"Repair failed: {result['message']}")


def handle_reinstall(port: int, debug: bool, no_debug: bool, reason: str) -> dict:
    """Attempt full reinstall when repair fails."""
    print_json(
        json_response(
            "warning",
            "Repair failed, attempting full reinstall...",
            "reinstall",
            {"reason": reason},
        )
    )

    result = cmd_reinstall()

    if result["status"] == "success":
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
                print_json(
                    json_response(
                        "success",
                        "pyKorf started after reinstall",
                        "launch",
                        {"port": port, "pid": proc.pid, "reinstalled": True},
                    )
                )
                sys.exit(0)
        except Exception:
            pass

    return json_response(
        "error",
        "pyKorf failed to start after reinstall",
        "launch",
        {"reinstall_error": result.get("message", "Unknown error")},
    )


def cmd_check_update() -> dict:
    """Query GitHub API and return update info."""
    update_info = get_update_info()

    if update_info:
        return json_response(
            "success",
            "Update check complete",
            "check-update",
            update_info,
        )

    return json_response(
        "error",
        "Failed to check for updates",
        "check-update",
    )


def cmd_apply_update() -> dict:
    """Apply update (called manually or by launch)."""
    update_info = get_update_info()

    if not update_info:
        return json_response("error", "Could not get update info", "apply-update")

    if not update_info.get("available"):
        return json_response(
            "info",
            f"No update available (current: {update_info['current']})",
            "apply-update",
            update_info,
        )

    return apply_update(update_info)


def cmd_repair_venv() -> dict:
    """Manual venv repair command."""
    return repair_venv()


def cmd_uninstall(full: bool) -> dict:
    """Remove app, preserve data unless --full."""
    if not APPDATA_DIR.exists():
        return json_response("info", "pyKorf is not installed", "uninstall")

    preserve = [] if full else ["data", "config.json"]

    print_json(json_response("info", "Removing application...", "uninstall"))

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
        return json_response("success", "pyKorf completely removed", "uninstall")

    return json_response(
        "success",
        "Application removed, data preserved",
        "uninstall",
        {"preserved": preserve},
    )


def cmd_reinstall() -> dict:
    """Full reinstall from failure state."""
    print_json(json_response("info", "Starting full reinstall...", "reinstall"))

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

    print_json(json_response("info", "Downloading latest release...", "reinstall"))

    zip_url = f"{GITHUB_RELEASE_URL}/pykorf-v{get_bat_major()}.zip"
    zip_path = Path(os.environ.get("TEMP", "")) / "pykorf_reinstall.zip"

    def download():
        download_file(zip_url, zip_path, timeout=DOWNLOAD_TIMEOUT)

    success, error = retry_operation(download)

    if not success:
        return json_response(
            "error",
            "Failed to download release",
            "reinstall",
            {"error": str(error)},
        )

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(APPDATA_DIR)
        zip_path.unlink(missing_ok=True)
    except Exception as e:
        zip_path.unlink(missing_ok=True)
        return json_response(
            "error",
            "Failed to extract release",
            "reinstall",
            {"error": str(e)},
        )

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

    print_json(json_response("info", "Creating fresh installation...", "reinstall"))

    success, error = retry_operation(
        lambda: subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            check=True,
            capture_output=True,
        )
    )

    if not success:
        return json_response(
            "error",
            "Failed to create venv",
            "reinstall",
            {"error": str(error)},
        )

    success, error = retry_operation(pip_install)

    if not success:
        return json_response(
            "error",
            "Failed to install dependencies",
            "reinstall",
            {"error": str(error)},
        )

    write_signature()
    ensure_last_check_file()
    write_version_from_pyproject()

    return json_response(
        "success",
        "Reinstall complete",
        "reinstall",
        {"preserved": preserved},
    )


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
