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
