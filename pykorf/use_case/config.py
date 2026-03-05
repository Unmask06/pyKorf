"""Configuration and data files management for pyKorf.

Handles:
- User preferences (last used KDF file path)
- PMS (Piping Material Specification) JSON files
- Stream data JSON files
- Default configuration directory structure

All data files are stored in the project /config folder by default.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import appdirs


# App configuration
APP_NAME = "pyKorf"
CONFIG_FILENAME = "config.json"

# Default paths - project config folder
PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "config"


def ensure_config_dir() -> Path:
    """Ensure the config directory exists.

    Returns:
        Path to the config directory.
    """
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_CONFIG_DIR


def get_config_dir() -> Path:
    """Get the platform-specific config directory for user preferences."""
    dirs = appdirs.user_config_dir(APP_NAME)
    path = Path(dirs)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_config_path() -> Path:
    """Get the path to the user config file."""
    return get_config_dir() / CONFIG_FILENAME


def load_config() -> dict[str, Any]:
    """Load user configuration from disk.

    Returns:
        Dictionary of configuration values. Returns empty dict if file doesn't exist.
    """
    config_path = get_config_path()
    if not config_path.exists():
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
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
        Path to the PMS file in the config directory.
    """
    return ensure_config_dir() / filename


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
    with open(pms_path, "r", encoding="utf-8") as f:
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

    # Convert Excel to JSON using existing function
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
        Path to the stream data file in the config directory.
    """
    return ensure_config_dir() / filename


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
    with open(stream_path, "r", encoding="utf-8") as f:
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

    Uses the same logic as convert_hmb_excel() but saves to the config directory.

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

    # Convert Excel to JSON using existing HMB converter
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
    """List all configuration files in the config directory.

    Returns:
        Dictionary with keys 'pms', 'streams', 'other' containing lists of filenames.
    """
    ensure_config_dir()

    pms_files = []
    stream_files = []
    other_files = []

    for f in DEFAULT_CONFIG_DIR.iterdir():
        if f.is_file() and f.suffix == ".json":
            name = f.name.lower()
            if "pms" in name:
                pms_files.append(f.name)
            elif "stream" in name:
                stream_files.append(f.name)
            else:
                other_files.append(f.name)

    return {"pms": sorted(pms_files), "streams": sorted(stream_files), "other": sorted(other_files)}
