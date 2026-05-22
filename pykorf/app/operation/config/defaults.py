"""Factory defaults with user config fallback for SharePoint URLs.

This module provides a unified fallback layer:
1. Check user config (config.json)
2. Fall back to factory defaults (project_defaults.toml)
3. Return empty string if neither is configured
"""

from __future__ import annotations

import tomllib
from importlib.resources import files
from typing import Any

# Load factory defaults once at module level (self-contained, no circular imports)
_FACTORY_DEFAULTS = tomllib.loads(
    files("pykorf.app").joinpath("project_defaults.toml").read_bytes().decode("utf-8")
)
_SHAREPOINT_DEFAULTS = _FACTORY_DEFAULTS.get("sharepoint", {})
_GLOBAL_PARAM_DEFAULTS = _FACTORY_DEFAULTS.get("global_parameters", {})


def get_factory_defaults() -> dict[str, Any]:
    """Get the cached factory defaults from project_defaults.toml.

    Returns:
        Full factory defaults dict with keys: company, project, engineering, sharepoint.
    """
    return _FACTORY_DEFAULTS


def get_doc_register_url() -> str:
    """Get Document Register URL: config.json → project_defaults.toml → empty string.

    Returns:
        Document Register Excel URL or local path from user config,
        factory default from project_defaults.toml, or empty string.
    """
    from pykorf.app.operation.config.preferences import get_doc_register_excel_path

    # 1. Check user config (config.json)
    user_path = get_doc_register_excel_path()
    if user_path:
        return user_path

    # 2. Fall back to factory defaults (project_defaults.toml)
    return _SHAREPOINT_DEFAULTS.get("doc_register_url", "")


def get_pms_excel_url() -> str:
    """Get PMS Excel URL: config.json → project_defaults.toml → empty string.

    Returns:
        PMS Excel URL or local path from user config,
        factory default from project_defaults.toml, or empty string.
    """
    from pykorf.app.operation.config.preferences import get_pms_excel_path

    # 1. Check user config (config.json)
    user_path = get_pms_excel_path()
    if user_path:
        return user_path

    # 2. Fall back to factory defaults (project_defaults.toml)
    return _SHAREPOINT_DEFAULTS.get("pms_excel_url", "")


def get_default_sp_site_url() -> str:
    """Get default SharePoint site URL: config.json → project_defaults.toml → empty string.

    Returns:
        SharePoint site URL from user config,
        factory default from project_defaults.toml, or empty string.
    """
    from pykorf.app.operation.config.preferences import get_doc_register_sp_site_url

    # 1. Check user config (config.json)
    user_url = get_doc_register_sp_site_url()
    if user_url:
        return user_url

    # 2. Fall back to factory defaults (project_defaults.toml)
    return _SHAREPOINT_DEFAULTS.get("default_site_url", "")


def get_default_dp_margin() -> float:
    """Get default dp_margin from project_defaults.toml."""
    return float(_GLOBAL_PARAM_DEFAULTS.get("dp_margin", 1.25))


def get_default_shutoff_margin() -> float:
    """Get default shutoff_margin from project_defaults.toml."""
    return float(_GLOBAL_PARAM_DEFAULTS.get("shutoff_margin", 1.20))


def get_default_min_pump_elevation() -> float:
    """Get default min_pump_elevation from project_defaults.toml."""
    return float(_GLOBAL_PARAM_DEFAULTS.get("min_pump_elevation", 0.5))


def get_default_min_vel_coeff() -> float:
    """Get default min_vel_coeff from project_defaults.toml."""
    return float(_GLOBAL_PARAM_DEFAULTS.get("min_vel_coeff", 0.1))
