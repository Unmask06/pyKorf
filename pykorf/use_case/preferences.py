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


def get_global_parameters_selected() -> list[str]:
    """Get the list of selected global parameters IDs.

    Returns:
        List of parameter IDs that were last selected.
    """
    config = load_config()
    return config.get("global_settings_selected", [])


def set_global_parameters_selected(setting_ids: list[str]) -> None:
    """Save the selected global parameters IDs.

    Args:
        setting_ids: List of parameter IDs to save as selected.
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


def get_last_report_path() -> str | None:
    """Get the last used report output path.

    Returns:
        The last used report path, or None if not set.
    """
    config = load_config()
    return config.get("last_report_path")


def set_last_report_path(path: str | Path) -> None:
    """Save the last used report output path.

    Args:
        path: The report path to save.
    """
    config = load_config()
    config["last_report_path"] = str(path)
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


def get_pms_excel_last_imported() -> str | None:
    """Get the ISO timestamp of when PMS data was last imported from Excel.

    Returns:
        ISO format timestamp string, or None if PMS has never been imported.
    """
    config = load_config()
    return config.get("pms_excel_last_imported")


def set_pms_excel_last_imported(timestamp: str) -> None:
    """Save the ISO timestamp of when PMS data was last imported from Excel.

    Args:
        timestamp: ISO format timestamp string (e.g. from datetime.isoformat()).
    """
    config = load_config()
    config["pms_excel_last_imported"] = timestamp
    save_config(config)


def get_sp_overrides() -> dict[str, str]:
    """Get user-configured SharePoint path overrides.

    Returns a mapping of local folder paths to their correct SharePoint URLs.
    Used when OneDrive stores only the library root in the registry but the
    synced folder is actually a subfolder (IsFolderScope = 1).

    Returns:
        Dict mapping local path strings to SharePoint URL strings.
    """
    config = load_config()
    return config.get("sp_overrides", {})


def set_sp_overrides(overrides: dict[str, str]) -> None:
    """Save user-configured SharePoint path overrides.

    Args:
        overrides: Dict mapping local path strings to SharePoint URL strings.
    """
    config = load_config()
    config["sp_overrides"] = overrides
    save_config(config)


def get_trial_start() -> str | None:
    """Get the ISO date string of when the trial period started.

    Returns:
        ISO date string (e.g. "2026-04-02"), or None if not yet set.
    """
    config = load_config()
    return config.get("trial_start")


def set_trial_start(iso_date: str) -> None:
    """Persist the trial start date.

    Args:
        iso_date: ISO date string (e.g. ``date.today().isoformat()``).
    """
    config = load_config()
    config["trial_start"] = iso_date
    save_config(config)


def get_license_key() -> str | None:
    """Get the stored license key.

    Returns:
        License key string, or None if no key has been entered.
    """
    config = load_config()
    return config.get("license_key")


def set_license_key(key: str) -> None:
    """Persist a license key.

    Args:
        key: The license key string to store.
    """
    config = load_config()
    config["license_key"] = key
    save_config(config)


def get_stream_excel_last_imported() -> str | None:
    """Get the ISO timestamp of when Stream data was last imported from Excel.

    Returns:
        ISO format timestamp string, or None if Stream data has never been imported.
    """
    config = load_config()
    return config.get("stream_excel_last_imported")


def set_stream_excel_last_imported(timestamp: str) -> None:
    """Save the ISO timestamp of when Stream data was last imported from Excel.

    Args:
        timestamp: ISO format timestamp string (e.g. from datetime.isoformat()).
    """
    config = load_config()
    config["stream_excel_last_imported"] = timestamp
    save_config(config)
