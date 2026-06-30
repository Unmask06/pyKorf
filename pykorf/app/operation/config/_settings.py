"""Non-path user settings: license, trial, SharePoint, interaction, timestamps."""

from __future__ import annotations

from typing import Any

from pykorf.app.operation.config._core import load_config, save_config


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


def get_doc_register_db_last_imported() -> str | None:
    """Get the ISO timestamp of when Document Register DB was last built from Excel.

    Returns:
        ISO format timestamp string, or None if DB has never been built.
    """
    config = load_config()
    return config.get("doc_register_db_last_imported")


def set_doc_register_db_last_imported(timestamp: str) -> None:
    """Save the ISO timestamp of when Document Register DB was last built from Excel.

    Args:
        timestamp: ISO format timestamp string (e.g. from datetime.isoformat()).
    """
    config = load_config()
    config["doc_register_db_last_imported"] = timestamp
    save_config(config)


def get_doc_register_sp_site_url() -> str | None:
    """Get the SharePoint site base URL for Document Register links.

    Returns:
        The SharePoint site URL (e.g., 'https://tenant.sharepoint.com'), or None.
    """
    config = load_config()
    return config.get("doc_register_sp_site_url")


def set_doc_register_sp_site_url(url: str) -> None:
    """Save the SharePoint site base URL for Document Register links.

    Args:
        url: The SharePoint site URL string.
    """
    config = load_config()
    config["doc_register_sp_site_url"] = url.strip().rstrip("/")
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


def get_skip_sp_override() -> bool:
    """Check if SharePoint override validation should be skipped.

    Returns:
        True if validation should be skipped (allow local paths only).
        False by default (SharePoint overrides required).
    """
    config = load_config()
    return config.get("skip_sp_override", False)


def set_skip_sp_override(skip: bool) -> None:
    """Save the skip SharePoint override preference.

    Args:
        skip: True to skip validation, False to require overrides.
    """
    config = load_config()
    config["skip_sp_override"] = skip
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


def get_project_info_overrides() -> dict[str, Any]:
    """Get user project info overrides from config.json.

    Returns:
        Flat dict of project info overrides stored under the "project_info" key.
        Returns empty dict if none set.
    """
    config = load_config()
    return config.get("project_info", {})


def set_project_info_overrides(overrides: dict[str, Any]) -> None:
    """Persist user project info overrides to config.json.

    Args:
        overrides: Flat dict of field overrides, e.g. ``{"company1": "ACME"}``.
    """
    config = load_config()
    config["project_info"] = overrides
    save_config(config)


def get_whats_new_last_seen_version() -> str | None:
    """Get the app version for which the user has already seen the "What's New" modal.

    Returns:
        Version string (e.g. ``"0.47.0"``) or ``None`` if never seen.
    """
    config = load_config()
    return config.get("whats_new_last_seen_version")


def set_whats_new_last_seen_version(version: str) -> None:
    """Record that the user has seen the "What's New" modal for the given version.

    Args:
        version: The app version (e.g. ``"0.47.0"``) the user acknowledged.
    """
    config = load_config()
    config["whats_new_last_seen_version"] = version
    save_config(config)
