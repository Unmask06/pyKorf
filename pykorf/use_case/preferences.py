"""User preferences and state management for pyKorf.

Handles:
- User configuration serialization (config.json)
- Recent file paths
- UI state (last interactions)
- Global settings preferences
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pykorf.use_case.paths import get_config_path


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


def get_recent_files(max_count: int = 10) -> list[str]:
    """Get the list of recently used KDF file paths.

    Args:
        max_count: Maximum number of recent files to return.

    Returns:
        List of recent file paths, most recent first.
    """
    config = load_config()
    return config.get("recent_files", [])[:max_count]


def add_recent_file(path: str | Path) -> None:
    """Add a file path to the recent files list.

    Moves existing entries to the front and caps the list at 10 entries.

    Args:
        path: The KDF file path to add.
    """
    config = load_config()
    recent = config.get("recent_files", [])
    path_str = str(path)
    if path_str in recent:
        recent.remove(path_str)
    recent.insert(0, path_str)
    config["recent_files"] = recent[:10]
    save_config(config)


def record_opened_file(path: str | Path) -> None:
    """Record a KDF file as last opened and add to recent files in a single write.

    Combines set_last_kdf_path and add_recent_file into one config read/write.

    Args:
        path: The KDF file path to record.
    """
    config = load_config()
    path_str = str(path)
    config["last_kdf_path"] = path_str
    recent = config.get("recent_files", [])
    if path_str in recent:
        recent.remove(path_str)
    recent.insert(0, path_str)
    config["recent_files"] = recent[:10]
    save_config(config)


def get_last_interaction() -> dict[str, Any]:
    """Get the last interaction data.

    Returns:
        Dictionary containing last interaction data, or empty dict if not set.
    """
    config = load_config()
    return config.get("last_interaction", {}).get("data", {})


def set_last_interaction(screen_name: str, data: dict[str, Any]) -> None:
    """Save the last interaction data.

    Args:
        screen_name: Name of the screen/interaction (kept for API compatibility, not stored).
        data: Dictionary of interaction data to save.
    """
    config = load_config()
    config["last_interaction"] = {"data": data}
    save_config(config)


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


def get_last_batch_folder_path() -> str | None:
    """Get the last used batch folder path.

    Returns:
        The last used folder path for batch mode, or None if not set.
    """
    config = load_config()
    return config.get("last_batch_folder_path")


def set_last_batch_folder_path(path: str | Path) -> None:
    """Save the last used batch folder path.

    Args:
        path: The folder path to save.
    """
    config = load_config()
    config["last_batch_folder_path"] = str(path)
    save_config(config)


def get_last_excel_export_path() -> str | None:
    """Get the last used Excel export path.

    Returns:
        The last used export path, or None if not set.
    """
    config = load_config()
    return config.get("last_excel_export_path")


def set_last_excel_export_path(path: str | Path) -> None:
    """Save the last used Excel export path.

    Args:
        path: The export path to save.
    """
    config = load_config()
    config["last_excel_export_path"] = str(path)
    save_config(config)


def get_last_hmb_path() -> str | None:
    """Get the last used HMB JSON file path.

    Returns:
        The last used HMB file path, or None if not set.
    """
    config = load_config()
    return config.get("last_hmb_path")


def set_last_hmb_path(path: str | Path) -> None:
    """Save the last used HMB JSON file path.

    Args:
        path: The HMB file path to save.
    """
    config = load_config()
    config["last_hmb_path"] = str(path)
    save_config(config)


def get_pms_excel_path() -> str | None:
    """Get the PMS Excel source file path.

    Checks the top-level ``pms_excel_path`` key first, then falls back to
    the path stored inside ``last_interaction.data`` for backward compatibility.

    Returns:
        The PMS Excel file path, or None if not set.
    """
    config = load_config()
    path = config.get("pms_excel_path")
    if not path:
        path = config.get("last_interaction", {}).get("data", {}).get("pms_excel_path")
    return path


def set_pms_excel_path(path: str | Path) -> None:
    """Save the PMS Excel source file path.

    Args:
        path: The PMS Excel file path to save.
    """
    config = load_config()
    config["pms_excel_path"] = str(path)
    save_config(config)


def get_last_excel_import_path() -> str | None:
    """Get the last used Excel import path.

    Returns:
        The last used import path, or None if not set.
    """
    config = load_config()
    return config.get("last_excel_import_path")


def set_last_excel_import_path(path: str | Path) -> None:
    """Save the last used Excel import path.

    Args:
        path: The import path to save.
    """
    config = load_config()
    config["last_excel_import_path"] = str(path)
    save_config(config)
