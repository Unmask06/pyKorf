"""Configuration management for pyKorf use case TUI.

Handles loading and saving user preferences like the last used KDF file path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import appdirs


# Default config location
APP_NAME = "pyKorf"
CONFIG_FILENAME = "config.json"


def get_config_dir() -> Path:
    """Get the platform-specific config directory."""
    dirs = appdirs.user_config_dir(APP_NAME)
    path = Path(dirs)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_config_path() -> Path:
    """Get the path to the config file."""
    return get_config_dir() / CONFIG_FILENAME


def load_config() -> dict[str, Any]:
    """Load configuration from disk.

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
    """Save configuration to disk.

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
