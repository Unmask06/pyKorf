"""User-configurable file and folder path preferences."""

from __future__ import annotations

from pathlib import Path

from pykorf.app.operation.config._core import load_config, save_config


def get_last_kdf_path() -> str | None:
    """Get the last used KDF file path.

    Returns:
        The last used KDF file path, or None if not set or the file no longer exists.
    """
    config = load_config()
    path = config.get("last_kdf_path")
    if path and not Path(path).is_file():
        config.pop("last_kdf_path", None)
        save_config(config)
        return None
    return path


def set_last_kdf_path(path: str | Path) -> None:
    """Save the last used KDF file path.

    Args:
        path: The KDF file path to save.
    """
    config = load_config()
    config["last_kdf_path"] = str(path)
    save_config(config)


def get_recent_files(max_count: int = 20) -> list[str]:
    """Get the list of recently used KDF file paths.

    Filters out paths that no longer exist and persists the cleaned list.

    Args:
        max_count: Maximum number of recent files to return.

    Returns:
        List of valid recent file paths, most recent first.
    """
    config = load_config()
    recent = config.get("recent_files", [])[:max_count]
    valid = [p for p in recent if Path(p).is_file()]
    if len(valid) != len(recent):
        config["recent_files"] = valid
        save_config(config)
    return valid


def add_recent_file(path: str | Path) -> None:
    """Add a file path to the recent files list.

    Moves existing entries to the front and caps the list at 20 entries.

    Args:
        path: The KDF file path to add.
    """
    config = load_config()
    recent = config.get("recent_files", [])
    path_str = str(path)
    if path_str in recent:
        recent.remove(path_str)
    recent.insert(0, path_str)
    config["recent_files"] = recent[:20]
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
    config["recent_files"] = recent[:20]
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


def get_doc_register_excel_path() -> str | None:
    """Get the Document Register Excel source file path.

    Returns:
        The Document Register Excel file path, or None if not set.
    """
    config = load_config()
    return config.get("doc_register_excel_path")


def set_doc_register_excel_path(path: str | Path) -> None:
    """Save the Document Register Excel source file path.

    Args:
        path: The Document Register Excel file path to save.
    """
    config = load_config()
    config["doc_register_excel_path"] = str(path)
    save_config(config)


def get_pinned_folders() -> list[str]:
    """Get list of pinned folder paths from config.json.

    Returns:
        List of absolute folder paths. Returns empty list if none set.
    """
    config = load_config()
    return config.get("pinned_folders", [])


def add_pinned_folder(path: str) -> None:
    """Add a folder path to the pinned folders list.

    Args:
        path: Absolute folder path to pin. Skipped if already pinned.
    """
    config = load_config()
    pinned = config.get("pinned_folders", [])
    if path not in pinned:
        pinned.append(path)
        config["pinned_folders"] = pinned
        save_config(config)


def remove_pinned_folder(path: str) -> None:
    """Remove a folder path from the pinned folders list.

    Args:
        path: Absolute folder path to unpin. No-op if not pinned.
    """
    config = load_config()
    pinned = config.get("pinned_folders", [])
    if path in pinned:
        pinned.remove(path)
        config["pinned_folders"] = pinned
        save_config(config)
