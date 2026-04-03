"""App-wide preferences route: /preferences."""

from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path

from flask import Blueprint, render_template, request

bp = Blueprint("preferences", __name__)

# Default SharePoint site URL shown as placeholder in the UI
DEFAULT_SP_SITE_URL = "https://cc7ges.sharepoint.com"


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
    from pykorf.license import validate_license_key
    from pykorf.use_case.preferences import (
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
    from pykorf.use_case.web.sharepoint import clear_cache

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
                doc_register_sp_site_url=get_doc_register_sp_site_url(),
                doc_register_db_last_imported=_format_timestamp(
                    get_doc_register_db_last_imported()
                ),
                dr_flash=dr_flash,
            )

        if action == "add":
            local = (request.form.get("local_path") or "").strip().rstrip("\\/")
            sp_url = (request.form.get("sp_url") or "").strip().rstrip("/")
            if local and sp_url:
                overrides[local] = sp_url
                set_sp_overrides(overrides)
                clear_cache()
                flash = {"type": "success", "msg": "Override added."}
            else:
                flash = {
                    "type": "warning",
                    "msg": "Both local path and SharePoint URL are required.",
                }

        elif action == "delete":
            local = (request.form.get("local_path") or "").strip()
            if local in overrides:
                del overrides[local]
                set_sp_overrides(overrides)
                clear_cache()
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
                clear_cache()
                flash = {"type": "success", "msg": "Override updated."}
            else:
                flash = {
                    "type": "warning",
                    "msg": "Both local path and SharePoint URL are required.",
                }

        elif action == "set_doc_register_config":
            from pykorf.use_case.web.doc_register.excel_to_db import build_db_from_excel

            excel_path = (request.form.get("dr_excel_path") or "").strip()
            sp_site_url = (request.form.get("dr_sp_site_url") or "").strip()

            changed = False
            if excel_path and excel_path != get_doc_register_excel_path():
                set_doc_register_excel_path(excel_path)
                changed = True
            if sp_site_url and sp_site_url != get_doc_register_sp_site_url():
                set_doc_register_sp_site_url(sp_site_url)
                changed = True

            if changed and excel_path and Path(excel_path).is_file():
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
        doc_register_sp_site_url=get_doc_register_sp_site_url(),
        doc_register_sp_site_url_default=DEFAULT_SP_SITE_URL,
        doc_register_db_last_imported=_format_timestamp(get_doc_register_db_last_imported()),
        dr_flash=dr_flash,
    )
