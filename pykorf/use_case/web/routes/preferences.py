"""App-wide preferences route: /preferences."""

from __future__ import annotations

from flask import Blueprint, render_template, request

bp = Blueprint("preferences", __name__)


@bp.route("/preferences", methods=["GET", "POST"])
def preferences_page():
    """Render and handle the global preferences page (SharePoint overrides, etc.)."""
    from pykorf.use_case.preferences import get_sp_overrides, set_sp_overrides
    from pykorf.use_case.web.sharepoint import clear_cache

    flash: dict[str, str] | None = None

    if request.method == "POST":
        action = request.form.get("action", "")
        overrides = get_sp_overrides()

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

    overrides = get_sp_overrides()
    edit_key = request.args.get("edit", "").strip()
    edit_entry = (
        {"local": edit_key, "sp_url": overrides.get(edit_key, "")}
        if edit_key and edit_key in overrides
        else None
    )
    return render_template("preferences.html", overrides=overrides, flash=flash, edit_entry=edit_entry)
