"""Core configuration load/save operations and cache management."""

from __future__ import annotations

import json
from typing import Any

from pykorf.app.exceptions import UseCaseError
from pykorf.app.operation.config.paths import get_config_path

_config_cache: dict[str, Any] | None = None


def clear_config_cache() -> None:
    """Clear the in-memory config cache.

    Used in tests to ensure fresh config reads after patching get_config_path.
    """
    global _config_cache
    _config_cache = None


def load_config() -> dict[str, Any]:
    """Load user configuration from disk.

    Returns:
        Dictionary of configuration values. Returns empty dict if file doesn't exist.
    """
    global _config_cache
    if _config_cache is not None:
        return _config_cache.copy()

    config_path = get_config_path()
    if not config_path.exists():
        _config_cache = {}
        return {}
    try:
        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                _config_cache = data
            else:
                _config_cache = {}
            return _config_cache.copy()
    except (json.JSONDecodeError, OSError):
        _config_cache = {}
        return {}


def save_config(config: dict[str, Any]) -> None:
    """Save user configuration to disk.

    Args:
        config: Dictionary of configuration values to save.

    Raises:
        UseCaseError: If saving the configuration file fails.
    """
    global _config_cache
    config_path = get_config_path()
    try:
        tmp_path = config_path.with_suffix(".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            tmp_path.replace(config_path)
            _config_cache = config.copy()
        finally:
            tmp_path.unlink(missing_ok=True)
    except OSError as e:
        raise UseCaseError(f"Failed to save configuration: {e}") from e
