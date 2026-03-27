"""Flask application for the pyKorf local web UI.

Single-user, local-only server.  Model state is held in a module-level
global (see :mod:`pykorf.use_case.web.session`), matching the terminal TUI
approach.  No cookies, no auth — it's just localhost.

Launch with::

    uv run pykorf --web [--port 8000]
"""

from __future__ import annotations

import threading
import webbrowser
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, redirect, render_template, request, url_for

from pykorf.use_case.web import session as _sess

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_STATIC_DIR = Path(__file__).parent / "static"

app = Flask(
    __name__,
    template_folder=str(_TEMPLATES_DIR),
    static_folder=str(_STATIC_DIR),
)


# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------


def _model_summary(model: Any) -> dict[str, int]:
    """Build element-count summary for template context.

    Args:
        model: Loaded KorfModel.

    Returns:
        Dict of element type → count.
    """
    return {
        "num_pipes": model.num_pipes,
        "num_junctions": model.num_junctions,
        "num_pumps": model.num_pumps,
        "num_valves": model.num_valves,
        "num_feeds": model.num_feeds,
        "num_products": model.num_products,
    }


def _pipe_names(model: Any) -> list[str]:
    """Return sorted pipe name list for <select> / tables.

    Args:
        model: Loaded KorfModel.

    Returns:
        Sorted list of non-empty pipe names.
    """
    names: list[str] = []
    for idx in range(1, model.num_pipes + 1):
        pipe = model.pipes[idx]
        if pipe.name:
            names.append(pipe.name)
    return sorted(names)


def _require_model():
    """Return the active model or redirect to /.

    Returns:
        Active KorfModel.

    Raises:
        werkzeug.exceptions.HTTPException: 302 redirect to / if no model loaded.
    """
    model = _sess.get_model()
    if model is None:
        return redirect(url_for("file_picker"))
    return model


# ---------------------------------------------------------------------------
# File picker
# ---------------------------------------------------------------------------


@app.route("/", methods=["GET"])
def file_picker():
    """Render the KDF file picker page."""
    from pykorf.use_case.config import get_recent_files

    recent: list[str] = get_recent_files() or []
    return render_template("file_picker.html", recent_files=recent)


@app.route("/open", methods=["POST"])
def open_file():
    """Load a KDF file into the global model state."""
    from pykorf import Model
    from pykorf.use_case.config import get_recent_files, record_opened_file

    kdf_path_str = (request.form.get("kdf_path") or "").strip()
    path = Path(kdf_path_str)

    if not path.is_file():
        return render_template(
            "file_picker.html",
            recent_files=get_recent_files() or [],
            error=f"File not found: {path}",
        ), 400

    try:
        model = Model(path)
    except Exception as exc:
        return render_template(
            "file_picker.html",
            recent_files=get_recent_files() or [],
            error=f"Failed to load model: {exc}",
        ), 400

    record_opened_file(str(path))
    _sess.load(model, path)
    return redirect(url_for("main_menu"))


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------


@app.route("/model")
def main_menu():
    """Render the main menu with model summary."""
    model = _require_model()
    if not hasattr(model, "num_pipes"):
        return model  # it's a redirect
    return render_template(
        "main_menu.html",
        kdf_path=str(_sess.get_kdf_path() or ""),
        summary=_model_summary(model),
    )


# ---------------------------------------------------------------------------
# Global Settings
# ---------------------------------------------------------------------------


@app.route("/model/settings", methods=["GET", "POST"])
def global_settings():
    """Render and handle the Global Settings form."""
    model = _require_model()
    if not hasattr(model, "num_pipes"):
        return model  # redirect

    from pykorf.use_case.config import get_global_settings_selected, get_last_interaction
    from pykorf.use_case.global_settings import apply_global_settings, get_global_settings

    settings = get_global_settings()

    if request.method == "GET":
        saved_selections: list[str] = get_global_settings_selected() or []
        interaction_data = get_last_interaction()
        saved_dp_margin = interaction_data.get("dp_margin") or "1.25"
        return render_template(
            "global_settings.html",
            kdf_path=str(_sess.get_kdf_path() or ""),
            settings=settings,
            saved_selections=saved_selections,
            saved_dp_margin=saved_dp_margin,
            result=None,
        )

    # POST — apply settings
    from pykorf.use_case.config import set_global_settings_selected

    selected_ids = [s.id for s in settings if request.form.get(f"setting_{s.id}")]

    dp_margin_str = (request.form.get("dp_margin") or "1.25").strip()
    try:
        dp_margin = float(dp_margin_str)
    except ValueError:
        dp_margin = 1.25

    result_lines: list[tuple[str, str]] = []
    errors: list[str] = []

    if not selected_ids:
        errors.append("No settings selected. Please select at least one setting.")
    else:
        set_global_settings_selected(selected_ids)
        try:
            apply_results = apply_global_settings(model, selected_ids, save=False, dp_margin=dp_margin)
            errs: list[str] = apply_results.pop("_errors", [])
            errors.extend(errs)
            for setting_id, pipes in apply_results.items():
                setting = next(s for s in settings if s.id == setting_id)
                result_lines.append(("success", f"{setting.name}: {len(pipes)} pipe(s) affected"))
                for pipe_name in pipes[:10]:
                    result_lines.append(("info", f"  - {pipe_name}"))
                if len(pipes) > 10:
                    result_lines.append(("info", f"  - … and {len(pipes) - 10} more"))
        except Exception as exc:
            errors.append(f"Error applying settings: {exc}")

    return render_template(
        "global_settings.html",
        kdf_path=str(_sess.get_kdf_path() or ""),
        settings=settings,
        saved_selections=selected_ids,
        saved_dp_margin=dp_margin_str,
        result={"lines": result_lines, "errors": errors},
    )


# ---------------------------------------------------------------------------
# Apply PMS
# ---------------------------------------------------------------------------


@app.route("/model/pms", methods=["GET", "POST"])
def apply_pms():
    """Render and handle the Apply PMS form."""
    model = _require_model()
    if not hasattr(model, "num_pipes"):
        return model

    from pykorf.use_case.config import get_pms_path

    if request.method == "GET":
        return render_template(
            "pms.html",
            kdf_path=str(_sess.get_kdf_path() or ""),
            pms_json_path=str(get_pms_path() or ""),
            result=None,
        )

    pms_source_str = (request.form.get("pms_source") or "").strip()
    pms_source = Path(pms_source_str) if pms_source_str else get_pms_path()

    result_lines: list[tuple[str, str]] = []
    errors: list[str] = []

    if not pms_source or not Path(pms_source).is_file():
        errors.append(f"PMS data file not found: {pms_source}")
    else:
        try:
            from pykorf.use_case.pms import apply_pms as _apply_pms

            _apply_pms(pms_source, model, save=False)
            result_lines.append(("success", "PMS data applied successfully."))
        except Exception as exc:
            errors.append(f"Error applying PMS: {exc}")

    return render_template(
        "pms.html",
        kdf_path=str(_sess.get_kdf_path() or ""),
        pms_json_path=str(pms_source or ""),
        result={"lines": result_lines, "errors": errors},
    )


# ---------------------------------------------------------------------------
# Apply HMB
# ---------------------------------------------------------------------------


@app.route("/model/hmb", methods=["GET", "POST"])
def apply_hmb():
    """Render and handle the Apply HMB form."""
    model = _require_model()
    if not hasattr(model, "num_pipes"):
        return model

    from pykorf.use_case.config import get_stream_path

    if request.method == "GET":
        return render_template(
            "hmb.html",
            kdf_path=str(_sess.get_kdf_path() or ""),
            hmb_json_path=str(get_stream_path() or ""),
            result=None,
        )

    hmb_source_str = (request.form.get("hmb_source") or "").strip()
    hmb_source = Path(hmb_source_str) if hmb_source_str else get_stream_path()

    result_lines: list[tuple[str, str]] = []
    errors: list[str] = []

    if not hmb_source or not Path(hmb_source).is_file():
        errors.append(f"HMB data file not found: {hmb_source}")
    else:
        try:
            from pykorf.use_case.hmb import apply_hmb as _apply_hmb

            _apply_hmb(hmb_source, model, save=False)
            result_lines.append(("success", "HMB data applied successfully."))
        except Exception as exc:
            errors.append(f"Error applying HMB: {exc}")

    return render_template(
        "hmb.html",
        kdf_path=str(_sess.get_kdf_path() or ""),
        hmb_json_path=str(hmb_source or ""),
        result={"lines": result_lines, "errors": errors},
    )


# ---------------------------------------------------------------------------
# Model Info
# ---------------------------------------------------------------------------


@app.route("/model/info")
def model_info():
    """Render the Model Info page with element statistics and pipe list."""
    model = _require_model()
    if not hasattr(model, "num_pipes"):
        return model
    return render_template(
        "model_info.html",
        kdf_path=str(_sess.get_kdf_path() or ""),
        summary=_model_summary(model),
        pipes=_pipe_names(model),
    )


# ---------------------------------------------------------------------------
# Import / Export
# ---------------------------------------------------------------------------


@app.route("/model/import-export", methods=["GET", "POST"])
def import_export():
    """Render and handle the Import/Export page."""
    model = _require_model()
    if not hasattr(model, "num_pipes"):
        return model

    from pykorf.use_case.config import (
        get_last_excel_export_path,
        get_last_excel_import_path,
        set_last_excel_export_path,
        set_last_excel_import_path,
    )

    if request.method == "GET":
        return render_template(
            "import_export.html",
            kdf_path=str(_sess.get_kdf_path() or ""),
            last_export_path=str(get_last_excel_export_path() or ""),
            last_import_path=str(get_last_excel_import_path() or ""),
            result=None,
        )

    action = (request.form.get("action") or "export").strip()
    file_path_str = (request.form.get("file_path") or "").strip()

    result_lines: list[tuple[str, str]] = []
    errors: list[str] = []

    if not file_path_str:
        errors.append("File path is required.")
    else:
        file_path = Path(file_path_str)
        try:
            if action == "export":
                model.io.to_excel(file_path)
                set_last_excel_export_path(str(file_path))
                result_lines.append(("success", f"Exported to: {file_path}"))
            elif action == "import":
                if not file_path.is_file():
                    errors.append(f"File not found: {file_path}")
                else:
                    model.io.from_excel(file_path)
                    set_last_excel_import_path(str(file_path))
                    result_lines.append(("success", f"Imported from: {file_path}"))
            else:
                errors.append(f"Unknown action: {action}")
        except Exception as exc:
            errors.append(f"Error during {action}: {exc}")

    return render_template(
        "import_export.html",
        kdf_path=str(_sess.get_kdf_path() or ""),
        last_export_path=str(get_last_excel_export_path() or ""),
        last_import_path=str(get_last_excel_import_path() or ""),
        result={"lines": result_lines, "errors": errors},
    )


# ---------------------------------------------------------------------------
# Generate Report
# ---------------------------------------------------------------------------


@app.route("/model/report", methods=["GET", "POST"])
def generate_report():
    """Render and handle the Generate Report page."""
    model = _require_model()
    if not hasattr(model, "num_pipes"):
        return model

    from pykorf.use_case.config import get_last_excel_export_path

    if request.method == "GET":
        return render_template(
            "report.html",
            kdf_path=str(_sess.get_kdf_path() or ""),
            last_report_path=str(get_last_excel_export_path() or ""),
            result=None,
        )

    report_path_str = (request.form.get("report_path") or "").strip()

    result_lines: list[tuple[str, str]] = []
    errors: list[str] = []

    if not report_path_str:
        errors.append("Output file path is required.")
    else:
        report_path = Path(report_path_str)
        try:
            import pandas as pd

            from pykorf.use_case.web.references import ReferencesStore

            dfs = model.io.to_dataframes()

            # Prepend a clean References sheet if any exist
            refs_store = ReferencesStore.load(report_path.parent) if report_path else ReferencesStore()
            kdf_path_for_refs = _sess.get_kdf_path()
            if kdf_path_for_refs:
                refs_store = ReferencesStore.load(kdf_path_for_refs)

            with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
                # References sheet first (most useful at the front)
                refs_df = refs_store.to_dataframe()
                if not refs_df.empty:
                    refs_df.to_excel(writer, sheet_name="References", index=False)

                # Basis text as a plain sheet if present
                if refs_store.basis.strip():
                    basis_df = pd.DataFrame({"Design Basis": [refs_store.basis]})
                    basis_df.to_excel(writer, sheet_name="Basis", index=False)

                # Model element sheets
                for sheet_name, df in dfs.items():
                    df.to_excel(writer, sheet_name=sheet_name[:31], index=False)

            n_refs = len(refs_store.references)
            ref_note = f" (+{n_refs} reference(s))" if n_refs else ""
            result_lines.append(("success", f"Report saved to: {report_path}{ref_note}"))
        except Exception as exc:
            errors.append(f"Error generating report: {exc}")

    return render_template(
        "report.html",
        kdf_path=str(_sess.get_kdf_path() or ""),
        last_report_path=report_path_str,
        result={"lines": result_lines, "errors": errors},
    )


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------


@app.route("/model/save", methods=["POST"])
def save_model():
    """Save the in-memory model back to its source .kdf file."""
    model = _require_model()
    if not hasattr(model, "num_pipes"):
        return model
    kdf_path = _sess.get_kdf_path()
    if kdf_path:
        model.io.save(kdf_path)
    return redirect(url_for("main_menu"))


# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------


def _load_refs() -> Any:
    """Load the ReferencesStore for the active model.

    Returns:
        ReferencesStore instance (empty if no model or no sidecar yet).
    """
    from pykorf.use_case.web.references import ReferencesStore

    kdf_path = _sess.get_kdf_path()
    if kdf_path is None:
        return ReferencesStore()
    return ReferencesStore.load(kdf_path)


def _refs_context(kdf_path: Path, store: Any, **extra: Any) -> dict[str, Any]:
    """Build the common template context for the references page.

    Args:
        kdf_path: Active KDF path.
        store: Current ReferencesStore.
        **extra: Additional context variables.

    Returns:
        Template context dict.
    """
    from pykorf.use_case.web.references import CATEGORIES

    return {
        "kdf_path": str(kdf_path),
        "store": store,
        "categories": CATEGORIES,
        "ref_dir": str(kdf_path.parent / "reference"),
        "flash": None,
        "shortcut_result": None,
        **extra,
    }


@app.route("/model/references")
def references_page() -> Any:
    """Render the References manager page.

    Returns:
        HTML response with the references template.
    """
    model = _require_model()
    if not hasattr(model, "num_pipes"):
        return model
    kdf_path = _sess.get_kdf_path()
    store = _load_refs()
    return render_template("references.html", **_refs_context(kdf_path, store))


@app.route("/model/references/basis", methods=["POST"])
def references_save_basis() -> Any:
    """Save only the design basis text.

    Returns:
        Redirect to the references page.
    """
    model = _require_model()
    if not hasattr(model, "num_pipes"):
        return model
    kdf_path = _sess.get_kdf_path()
    store = _load_refs()
    store.basis = request.form.get("basis", "")
    store.save(kdf_path)
    return redirect(url_for("references_page"))


@app.route("/model/references/add", methods=["POST"])
def references_add() -> Any:
    """Add a new reference entry and save.

    Returns:
        Redirect to the references page.
    """
    model = _require_model()
    if not hasattr(model, "num_pipes"):
        return model

    from pykorf.use_case.web.references import Reference

    kdf_path = _sess.get_kdf_path()
    store = _load_refs()

    name = (request.form.get("name") or "").strip()
    link = (request.form.get("link") or "").strip()
    description = (request.form.get("description") or "").strip()
    category = (request.form.get("category") or "Other").strip()

    if name and link:
        store.add(Reference.new(name=name, link=link, description=description, category=category))
        store.save(kdf_path)

    return redirect(url_for("references_page"))


@app.route("/model/references/update", methods=["POST"])
def references_update() -> Any:
    """Update an existing reference by ID and save.

    Returns:
        Redirect to the references page.
    """
    model = _require_model()
    if not hasattr(model, "num_pipes"):
        return model

    kdf_path = _sess.get_kdf_path()
    store = _load_refs()

    ref_id = (request.form.get("ref_id") or "").strip()
    if ref_id:
        store.update(
            ref_id,
            name=(request.form.get("name") or "").strip(),
            link=(request.form.get("link") or "").strip(),
            description=(request.form.get("description") or "").strip(),
            category=(request.form.get("category") or "Other").strip(),
        )
        store.save(kdf_path)

    return redirect(url_for("references_page"))


@app.route("/model/references/delete", methods=["POST"])
def references_delete() -> Any:
    """Delete a reference by ID and save.

    Returns:
        Redirect to the references page.
    """
    model = _require_model()
    if not hasattr(model, "num_pipes"):
        return model

    kdf_path = _sess.get_kdf_path()
    store = _load_refs()
    ref_id = (request.form.get("ref_id") or "").strip()
    if ref_id:
        store.delete(ref_id)
        store.save(kdf_path)

    return redirect(url_for("references_page"))


@app.route("/model/references/shortcuts", methods=["POST"])
def references_create_shortcuts() -> Any:
    """Create .url shortcut files in the reference/ folder and reload page.

    Returns:
        HTML response with shortcut creation results.
    """
    model = _require_model()
    if not hasattr(model, "num_pipes"):
        return model

    kdf_path = _sess.get_kdf_path()
    store = _load_refs()
    shortcut_result: dict[str, Any] = {}

    try:
        count, ref_dir = store.create_shortcuts(kdf_path)
        shortcut_result = {"count": count, "path": str(ref_dir)}
    except Exception as exc:
        shortcut_result = {"error": str(exc)}


    return render_template(
        "references.html",
        **_refs_context(kdf_path, store, shortcut_result=shortcut_result),
    )


# ---------------------------------------------------------------------------
# Path browser API
# ---------------------------------------------------------------------------

# File extensions surfaced per filter mode
_EXT_MAP: dict[str, set[str]] = {
    "kdf": {".kdf"},
    "excel": {".xlsx", ".xls"},
    "json": {".json"},
    "any": set(),  # empty = show all files
}


@app.route("/api/browse")
def api_browse():
    """Return directory listing for the path browser widget.

    Query params:
        path (str): Directory path to list. Defaults to the user's home directory.
        filter (str): One of ``kdf``, ``excel``, ``json``, ``any``. Controls which
            files are included. Directories are always shown.

    Returns:
        JSON ``{current, parent, drives, dirs, files}`` where *drives* is a
        non-empty list only on Windows.
    """
    import os

    raw = (request.args.get("path") or "").strip()
    fmode = (request.args.get("filter") or "any").lower()
    ext_filter = _EXT_MAP.get(fmode, set())

    # Resolve requested path, fall back to home
    if raw:
        target = Path(raw)
        if not target.is_dir():
            target = target.parent if target.parent.is_dir() else Path.home()
    else:
        target = Path.home()

    try:
        target = target.resolve()
        entries = list(target.iterdir())
    except PermissionError:
        target = Path.home()
        entries = list(target.iterdir())

    dirs: list[dict] = []
    files: list[dict] = []

    for entry in sorted(entries, key=lambda e: (not e.is_dir(), e.name.lower())):
        try:
            if entry.is_dir() and not entry.name.startswith("."):
                dirs.append({"name": entry.name, "path": str(entry)})
            elif entry.is_file():
                if not ext_filter or entry.suffix.lower() in ext_filter:
                    files.append({"name": entry.name, "path": str(entry)})
        except PermissionError:
            continue

    parent = str(target.parent) if target != target.parent else None

    # On Windows, enumerate drive letters
    drives: list[str] = []
    if os.name == "nt":
        import string

        drives = [
            f"{d}:\\"
            for d in string.ascii_uppercase
            if Path(f"{d}:\\").exists()
        ]

    return jsonify(
        {
            "current": str(target),
            "parent": parent,
            "drives": drives,
            "dirs": dirs,
            "files": files,
        }
    )


# ---------------------------------------------------------------------------
# Server launcher
# ---------------------------------------------------------------------------


def run_server(port: int = 8000) -> None:
    """Start the Flask development server and open the browser.

    Args:
        port: TCP port to listen on (default 8000).
    """
    url = f"http://localhost:{port}"
    print(f"\n  pyKorf Web UI → {url}\n  Press Ctrl+C to stop.\n")

    # Open browser after a short delay so the server is ready
    threading.Timer(0.8, webbrowser.open, args=[url]).start()

    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
