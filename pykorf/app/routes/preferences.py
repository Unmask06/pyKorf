"""App-wide preferences route: /preferences."""

from __future__ import annotations

import time
import tomllib
from datetime import datetime, UTC
from pathlib import Path

from flask import Blueprint, render_template, request

from pykorf.core.log import get_logger
from pykorf.app.operation.integration.license import validate_license_key
from pykorf.app.operation.config.preferences import (
    get_doc_register_db_last_imported,
    get_doc_register_excel_path,
    get_doc_register_sp_site_url,
    get_license_key,
    get_sp_overrides,
    set_doc_register_excel_path,
    set_doc_register_sp_site_url,
    set_license_key,
    set_sp_overrides,
)
from pykorf.app.operation.integration.sharepoint import clear_cache

logger = get_logger(__name__)

bp = Blueprint("preferences", __name__)

# Default SharePoint site URL shown as placeholder in the UI
DEFAULT_SP_SITE_URL = "https://cc7ges.sharepoint.com"

# Config cache with TTL (5 minutes)
_CONFIG_CACHE: dict = {}
_CACHE_TIMESTAMP: float = 0.0
_CONFIG_CACHE_TTL = 300  # seconds


def _get_cached_config() -> dict:
    """Get config values with TTL-based caching.

    Returns:
        Cached config dictionary, refreshed if TTL expired.
    """
    global _CONFIG_CACHE, _CACHE_TIMESTAMP

    now = time.time()
    if _CONFIG_CACHE and (now - _CACHE_TIMESTAMP) < _CONFIG_CACHE_TTL:
        return _CONFIG_CACHE

    # Read config.json
    from pykorf.app.operation.config.paths import get_config_path
    import json

    config_path = get_config_path()
    try:
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
    except (OSError, json.JSONDecodeError):
        config = {}

    _CONFIG_CACHE = config
    _CACHE_TIMESTAMP = now
    return config


def _clear_config_cache() -> None:
    """Clear config cache (call after set operations)."""
    global _CONFIG_CACHE, _CACHE_TIMESTAMP
    _CONFIG_CACHE = {}
    _CACHE_TIMESTAMP = 0.0


def _invalidate_all_caches() -> None:
    """Clear both SharePoint URL cache and config cache.

    Call this after modifying SharePoint overrides to ensure
    changes are immediately visible.
    """
    clear_cache()
    _clear_config_cache()


def _get_project_defaults() -> dict:
    """Load project defaults from project_defaults.toml.

    Returns:
        Dictionary of default values from the TOML file.
    """
    defaults_path = Path(__file__).parent.parent / "project_defaults.toml"
    try:
        with defaults_path.open("rb") as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as e:
        logger.warning("failed_to_load_project_defaults", error=str(e))
        return {}


def _validate_override(local: str, sp_url: str) -> str | None:
    """Validate a SharePoint override entry.

    Checks:
    - Both fields are non-empty
    - Local path exists on disk and is a directory
    - SP URL is well-formed (https scheme + netloc)

    Args:
        local: Local folder path string.
        sp_url: SharePoint URL string.

    Returns:
        Error message string if invalid, None if valid.
    """
    from urllib.parse import urlparse

    if not local or not sp_url:
        return "Both local path and SharePoint URL are required."

    if not Path(local).is_dir():
        return f"Local path does not exist or is not a folder: {local}"

    parsed = urlparse(sp_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return f"SharePoint URL is not valid (must start with http:// or https://): {sp_url}"

    return None


def _format_timestamp(iso_str: str | None) -> str:
    """Format an ISO timestamp for display.

    Args:
        iso_str: ISO format timestamp string.

    Returns:
        Human-readable string like '03 Apr 2026 14:30', or 'Never'.
    """
    if not iso_str:
        return "Never"
    try:
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone().strftime("%d %b %Y %H:%M")
    except (ValueError, TypeError):
        return "Never"


@bp.route("/preferences", methods=["GET", "POST"])
def preferences_page():
    """Render and handle the global preferences page (SharePoint overrides, etc.)."""
    flash: dict[str, str] | None = None
    license_flash: dict[str, str] | None = None
    dr_flash: dict[str, str] | None = None

    if request.method == "POST":
        action = request.form.get("action", "")
        overrides = get_sp_overrides()

        if action == "set_license_key":
            key = (request.form.get("license_key") or "").strip()
            if not key:
                license_flash = {"type": "warning", "msg": "Please enter a license key."}
            else:
                valid, expiry, err = validate_license_key(key)
                if valid:
                    set_license_key(key)
                    _clear_config_cache()
                    license_flash = {
                        "type": "success",
                        "msg": f"License key accepted — valid until {expiry}.",
                    }
                else:
                    license_flash = {"type": "danger", "msg": err}
            overrides = get_sp_overrides()
            edit_key = request.args.get("edit", "").strip()
            edit_entry = (
                {"local": edit_key, "sp_url": overrides.get(edit_key, "")}
                if edit_key and edit_key in overrides
                else None
            )
            current_key = get_license_key()
            return render_template(
                "preferences.html",
                overrides=overrides,
                flash=flash,
                license_flash=license_flash,
                edit_entry=edit_entry,
                current_license_key=current_key,
                doc_register_excel_path=get_doc_register_excel_path(),
                doc_register_sp_site_url=get_doc_register_sp_site_url() or DEFAULT_SP_SITE_URL,
                doc_register_db_last_imported=_format_timestamp(
                    get_doc_register_db_last_imported()
                ),
                dr_flash=dr_flash,
            )

        if action == "add":
            local = (request.form.get("local_path") or "").strip().rstrip("\\/")
            sp_url = (request.form.get("sp_url") or "").strip().rstrip("/")
            err = _validate_override(local, sp_url)
            if err:
                flash = {"type": "danger", "msg": err}
            else:
                overrides[local] = sp_url
                set_sp_overrides(overrides)
                _invalidate_all_caches()
                flash = {"type": "success", "msg": "Override added."}

        elif action == "delete":
            local = (request.form.get("local_path") or "").strip()
            if local in overrides:
                del overrides[local]
                set_sp_overrides(overrides)
                _invalidate_all_caches()
                flash = {"type": "success", "msg": "Override removed."}

        elif action == "edit":
            original_local = (request.form.get("original_local_path") or "").strip().rstrip("\\/")
            new_local = (request.form.get("local_path") or "").strip().rstrip("\\/")
            new_sp_url = (request.form.get("sp_url") or "").strip().rstrip("/")
            if original_local and new_local and new_sp_url:
                if original_local in overrides:
                    del overrides[original_local]
                overrides[new_local] = new_sp_url
                set_sp_overrides(overrides)
                _invalidate_all_caches()
                flash = {"type": "success", "msg": "Override updated."}
            else:
                flash = {
                    "type": "warning",
                    "msg": "Both local path and SharePoint URL are required.",
                }

        elif action == "set_doc_register_config":
            from pykorf.app.doc_register.excel_to_db import build_db_from_excel
            from pykorf.app.operation.integration.sharepoint import get_local_path_from_sp_url

            excel_path = (request.form.get("dr_excel_path") or "").strip()
            sp_site_url = (request.form.get("dr_sp_site_url") or "").strip()

            # Clear cache when config changes
            def _invalidate_and_reload():
                _clear_config_cache()
                return get_doc_register_excel_path(), get_doc_register_sp_site_url()

            # Convert SharePoint URL to local path if needed
            if excel_path and excel_path.startswith("https://"):
                logger.info("detected_sp_url_in_excel_path", excel_path=excel_path)
                converted_path = get_local_path_from_sp_url(excel_path)
                if converted_path is None:
                    dr_flash = {
                        "type": "danger",
                        "msg": (
                            "SharePoint URL could not be converted to local path. "
                            "No matching override found. Please configure the SharePoint "
                            "override above or provide the local path directly."
                        ),
                    }
                    excel_path = None
                else:
                    logger.info(
                        "sp_url_converted",
                        sp_url=excel_path,
                        local_path=converted_path,
                    )
                    excel_path = converted_path

            # Validate local path exists
            if excel_path and not Path(excel_path).is_file():
                dr_flash = {
                    "type": "danger",
                    "msg": f"Excel file not found: {excel_path}",
                }
                excel_path = None

            changed = False
            if excel_path and excel_path != get_doc_register_excel_path():
                set_doc_register_excel_path(excel_path)
                changed = True
            if sp_site_url and sp_site_url != get_doc_register_sp_site_url():
                set_doc_register_sp_site_url(sp_site_url)
                changed = True

            if changed:
                _invalidate_and_reload()
                if excel_path:
                    try:
                        build_db_from_excel(Path(excel_path), sp_site_url)
                        dr_flash = {"type": "success", "msg": "Config saved and database rebuilt."}
                    except Exception as exc:
                        dr_flash = {
                            "type": "warning",
                            "msg": f"Config saved, but DB rebuild failed: {exc}",
                        }
                else:
                    dr_flash = {"type": "success", "msg": "Document Register config saved."}

    # Batch config reads (cached)
    overrides = get_sp_overrides()
    current_key = get_license_key()
    doc_register_excel_path_saved = get_doc_register_excel_path()
    doc_register_sp_site_url_saved = get_doc_register_sp_site_url()
    doc_register_db_last_imported_val = get_doc_register_db_last_imported()

    # Get default Document Register URL from project_defaults.toml (cached)
    defaults = _get_project_defaults()
    default_doc_register_url = defaults.get("sharepoint", {}).get("doc_register_url", "")

    # Use saved path or default if blank
    doc_register_excel_path = doc_register_excel_path_saved or default_doc_register_url

    # Check if SharePoint overrides are configured (required for SP URL conversion)
    sp_overrides_configured = len(overrides) > 0

    edit_key = request.args.get("edit", "").strip()
    edit_entry = (
        {"local": edit_key, "sp_url": overrides.get(edit_key, "")}
        if edit_key and edit_key in overrides
        else None
    )

    return render_template(
        "preferences.html",
        overrides=overrides,
        flash=flash,
        license_flash=license_flash,
        edit_entry=edit_entry,
        current_key=current_key,
        doc_register_excel_path=doc_register_excel_path,
        doc_register_sp_site_url=doc_register_sp_site_url_saved or DEFAULT_SP_SITE_URL,
        doc_register_sp_site_url_default=DEFAULT_SP_SITE_URL,
        doc_register_db_last_imported=_format_timestamp(doc_register_db_last_imported_val),
        dr_flash=dr_flash,
        default_doc_register_url=default_doc_register_url,
        sp_overrides_configured=sp_overrides_configured,
    )
