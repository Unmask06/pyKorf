r"""Configuration and data files management for pyKorf.

Handles:
- User preferences (last used KDF file path)
- PMS (Piping Material Specification) JSON files
- Stream data JSON files
- Default configuration directory structure

All configuration files are stored in:
- Windows: %APPDATA%\\pyKorf\\config.json (user preferences)
- Windows: %APPDATA%\\pyKorf\\data\\ (PMS, stream data files)
- macOS: ~/Library/Application Support/pyKorf/
- Linux: ~/.config/pyKorf/
"""

from __future__ import annotations

import json
import logging
import os
import platform
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

APP_NAME = "pyKorf"
CONFIG_FILENAME = "config.json"
DATA_SUBDIR = "data"


def _get_platform_config_dir() -> Path:
    """Get the platform-specific config directory for pyKorf.

    Returns:
        - Windows: %APPDATA%/pyKorf/
        - macOS: ~/Library/Application Support/pyKorf/
        - Linux: ~/.config/pyKorf/
    """
    system = platform.system()

    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / APP_NAME
        return Path.home() / "AppData" / "Roaming" / APP_NAME
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        return Path.home() / ".config" / APP_NAME


# Default paths - project config folder
PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "config"

# Legacy config folder for migration
LEGACY_CONFIG_DIR = PROJECT_ROOT / "config"
MIGRATION_MARKER = ".migration_complete"


def ensure_config_dir() -> Path:
    """Ensure the config directory exists.

    Returns:
        Path to the config directory.
    """
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_CONFIG_DIR


def get_config_dir() -> Path:
    """Get the platform-specific config directory for user preferences."""
    path = _get_platform_config_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_config_path() -> Path:
    """Get the path to the user config file.

    Returns:
        Path to config.json in the config directory.
    """
    return get_config_dir() / CONFIG_FILENAME


def get_data_dir() -> Path:
    r"""Get the data directory for PMS and stream files.

    Returns:
        Path to the data subdirectory (e.g., %APPDATA%\\pyKorf\\data\\).
    """
    path = get_config_dir() / DATA_SUBDIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _needs_migration() -> bool:
    """Check if migration from legacy config folder is needed.

    Returns:
        True if legacy folder exists and migration hasn't been done.
    """
    if not LEGACY_CONFIG_DIR.exists():
        return False

    marker = get_config_dir() / MIGRATION_MARKER
    return not marker.exists()


def _migrate_from_legacy() -> None:
    """Migrate configuration files from project config folder to roaming directory."""
    if not _needs_migration():
        return

    logger.info("Migrating config files from %s to %s", LEGACY_CONFIG_DIR, get_config_dir())

    data_dir = get_data_dir()
    migrated_files = []

    try:
        for item in LEGACY_CONFIG_DIR.iterdir():
            if item.is_file() and item.suffix == ".json":
                dest = data_dir / item.name
                if not dest.exists():
                    shutil.copy2(item, dest)
                    migrated_files.append(item.name)
                    logger.info("Migrated: %s", item.name)

        # Create migration marker
        marker = get_config_dir() / MIGRATION_MARKER
        marker.write_text(" ".join(migrated_files), encoding="utf-8")

        if migrated_files:
            logger.info("Migration complete. Migrated %d files.", len(migrated_files))
    except Exception as e:
        logger.warning("Migration failed: %s", e)


def ensure_data_dir() -> Path:
    """Ensure the data directory exists and perform migration if needed.

    Returns:
        Path to the data directory.
    """
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)

    # Perform migration from legacy folder if needed
    _migrate_from_legacy()

    return data_dir


# Backward compatibility alias
ensure_config_dir = ensure_data_dir


def load_config() -> dict[str, Any]:
    """Load user configuration from disk.

    Returns:
        Dictionary of configuration values. Returns empty dict if file doesn't exist.
    """
    config_path = get_config_path()
    if not config_path.exists():
        return {}
    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)  # type: ignore[no-any-return]
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(config: dict[str, Any]) -> None:
    """Save user configuration to disk.

    Args:
        config: Dictionary of configuration values to save.
    """
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def get_last_kdf_path() -> str | None:
    """Get the last used KDF file path.

    Returns:
        The last used KDF file path, or None if not set.
    """
    config = load_config()
    return config.get("last_kdf_path")


def set_last_kdf_path(path: str | Path) -> None:
    """Save the last used KDF file path.

    Args:
        path: The KDF file path to save.
    """
    config = load_config()
    config["last_kdf_path"] = str(path)
    save_config(config)


def get_last_interaction() -> dict[str, Any]:
    """Get the last interaction data.

    Returns:
        Dictionary containing last interaction data, or empty dict if not set.
    """
    config = load_config()
    return config.get("last_interaction", {})


def set_last_interaction(screen_name: str, data: dict[str, Any]) -> None:
    """Save the last interaction data.

    Args:
        screen_name: Name of the screen/interaction.
        data: Dictionary of interaction data to save.
    """
    config = load_config()
    if "last_interaction" not in config:
        config["last_interaction"] = {}
    config["last_interaction"]["screen"] = screen_name
    config["last_interaction"]["data"] = data
    save_config(config)


# =============================================================================
# PMS (Piping Material Specification) Data Files
# =============================================================================


def get_pms_path(filename: str = "pms.json") -> Path:
    """Get the path to a PMS JSON file.

    Args:
        filename: Name of the PMS file (default: pms.json)

    Returns:
        Path to the PMS file in the data directory.
    """
    safe_filename = Path(filename).name
    return ensure_data_dir() / safe_filename


def load_pms_data(filename: str = "pms.json") -> dict[str, Any]:
    """Load PMS data from a JSON file.

    Args:
        filename: Name of the PMS file to load.

    Returns:
        Dictionary containing PMS data.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    pms_path = get_pms_path(filename)
    with open(pms_path, encoding="utf-8") as f:
        return json.load(f)


def save_pms_data(data: dict[str, Any], filename: str = "pms.json") -> None:
    """Save PMS data to a JSON file.

    Args:
        data: Dictionary containing PMS data.
        filename: Name of the PMS file to save.
    """
    pms_path = get_pms_path(filename)
    with open(pms_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def import_pms_from_excel(
    excel_path: str | Path,
    output_filename: str = "pms.json",
) -> Path:
    """Import PMS data from an Excel file and save as JSON.

    Reads all sheets from the Excel file, using each sheet name as the material.

    Args:
        excel_path: Path to the Excel file containing PMS data.
        output_filename: Name for the output JSON file.

    Returns:
        Path to the created JSON file.

    Raises:
        FileNotFoundError: If the Excel file doesn't exist.
        ImportError: If required Excel libraries are not installed.
    """
    from pykorf.use_case.pms import convert_pms_excel

    excel_path = Path(excel_path)
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    output_path = get_pms_path(output_filename)
    convert_pms_excel(excel_path, output_path)

    return output_path


# =============================================================================
# Stream Data Files
# =============================================================================


def get_stream_path(filename: str = "stream_data.json") -> Path:
    """Get the path to a stream data JSON file.

    Args:
        filename: Name of the stream data file (default: stream_data.json)

    Returns:
        Path to the stream data file in the data directory.
    """
    safe_filename = Path(filename).name
    return ensure_data_dir() / safe_filename


def load_stream_data(filename: str = "stream_data.json") -> dict[str, Any]:
    """Load stream data from a JSON file.

    Args:
        filename: Name of the stream data file to load.

    Returns:
        Dictionary containing stream data.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    stream_path = get_stream_path(filename)
    with open(stream_path, encoding="utf-8") as f:
        return json.load(f)


def save_stream_data(data: dict[str, Any], filename: str = "stream_data.json") -> None:
    """Save stream data to a JSON file.

    Args:
        data: Dictionary containing stream data.
        filename: Name of the stream data file to save.
    """
    stream_path = get_stream_path(filename)
    with open(stream_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def import_stream_from_excel(
    excel_path: str | Path,
    output_filename: str = "stream_data.json",
) -> Path:
    """Import stream data from an Excel file and save as JSON.

    Uses the same logic as convert_hmb_excel() but saves to the data directory.

    Args:
        excel_path: Path to the Excel file containing stream data.
        output_filename: Name for the output JSON file.

    Returns:
        Path to the created JSON file.

    Raises:
        FileNotFoundError: If the Excel file doesn't exist.
        ImportError: If required Excel libraries are not installed.
    """
    from pykorf.use_case.hmb import convert_hmb_excel

    excel_path = Path(excel_path)
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    output_path = get_stream_path(output_filename)
    convert_hmb_excel(excel_path, output_path)

    return output_path


# =============================================================================
# Global Settings Preferences
# =============================================================================


def get_global_settings_selected() -> list[str]:
    """Get the list of selected global settings IDs.

    Returns:
        List of setting IDs that were last selected.
    """
    config = load_config()
    return config.get("global_settings_selected", [])


def set_global_settings_selected(setting_ids: list[str]) -> None:
    """Save the selected global settings IDs.

    Args:
        setting_ids: List of setting IDs to save as selected.
    """
    config = load_config()
    config["global_settings_selected"] = setting_ids
    save_config(config)


# =============================================================================
# TUI Helper Functions
# =============================================================================


def list_config_files() -> dict[str, list[str]]:
    """List all configuration files in the data directory.

    Returns:
        Dictionary with keys 'pms', 'streams', 'other' containing lists of filenames.
    """
    data_dir = ensure_data_dir()

    pms_files = []
    stream_files = []
    other_files = []

    for f in data_dir.iterdir():
        if f.is_file() and f.suffix == ".json":
            name = f.name.lower()
            if "pms" in name:
                pms_files.append(f.name)
            elif "stream" in name:
                stream_files.append(f.name)
            else:
                other_files.append(f.name)

    return {"pms": sorted(pms_files), "streams": sorted(stream_files), "other": sorted(other_files)}
