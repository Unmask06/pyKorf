"""Core application path resolution and directory management for pyKorf.

Handles:
- Platform-specific config directory structure
- Data directory structure
- Legacy configuration migration
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
from pathlib import Path

logger = logging.getLogger("PathManager")

APP_NAME = "pyKorf"
CONFIG_FILENAME = "config.json"
DATA_SUBDIR = "data"

# Default paths - project config folder
PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "config"

# Legacy config folder for migration
LEGACY_CONFIG_DIR = PROJECT_ROOT / "config"
MIGRATION_MARKER = ".migration_complete"


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


def ensure_config_dir() -> Path:
    """Ensure the config directory exists.

    Returns:
        Path to the config directory.
    """
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


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
