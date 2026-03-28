"""Generate Report route: /model/report."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Blueprint, render_template, request

from pykorf.use_case.web import session as _sess
from pykorf.use_case.web.helpers import is_redirect, require_model

bp = Blueprint("report", __name__)


@bp.route("/model/report", methods=["GET", "POST"])
def generate_report():
    """Render and handle the Reports page (Report, Export, Import)."""
    model = require_model()
    if is_redirect(model):
        return model

    from pykorf.use_case.config import (
        get_last_excel_export_path,
        get_last_excel_import_path,
        get_last_report_path,
        set_last_excel_export_path,
        set_last_excel_import_path,
        set_last_report_path,
    )

    kdf_path = _sess.get_kdf_path()
    last_report = get_last_report_path()
    default_report = last_report or (
        str(kdf_path.with_name(f"{kdf_path.stem}_report.xlsx")) if kdf_path else ""
    )

    if request.method == "GET":
        return render_template(
            "report.html",
            kdf_path=str(kdf_path or ""),
            last_report_path=default_report,
            last_export_path=str(get_last_excel_export_path() or ""),
            last_import_path=str(get_last_excel_import_path() or ""),
            active_tab="report",
            result=None,
        )

    action = (request.form.get("action") or "generate_report").strip()
    file_path_str = (request.form.get("file_path") or "").strip()

    result_lines: list[tuple[str, str]] = []
    errors: list[str] = []

    if not file_path_str:
        errors.append("File path is required.")
    else:
        file_path = Path(file_path_str)

        if action == "generate_report":
            report_dir = file_path.parent
            if not report_dir.exists():
                errors.append(f"Output directory does not exist: {report_dir}")
            elif not report_dir.is_dir():
                errors.append(f"Output path is not a directory: {report_dir}")
            elif not os.access(report_dir, os.W_OK):
                errors.append(f"Output directory is not writable: {report_dir}")
            else:
                try:
                    import pandas as pd

                    from pykorf.use_case.web.references import ReferencesStore

                    dfs = model.io.to_dataframes()

                    kdf_path_for_refs = _sess.get_kdf_path()
                    refs_store = (
                        ReferencesStore.load(kdf_path_for_refs)
                        if kdf_path_for_refs
                        else ReferencesStore()
                    )

                    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                        refs_df = refs_store.to_dataframe()
                        if not refs_df.empty:
                            refs_df.to_excel(writer, sheet_name="References", index=False)

                        if refs_store.basis.strip():
                            basis_df = pd.DataFrame({"Design Basis": [refs_store.basis]})
                            basis_df.to_excel(writer, sheet_name="Basis", index=False)

                        for sheet_name, df in dfs.items():
                            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)

                    set_last_report_path(str(file_path))
                    n_refs = len(refs_store.references)
                    ref_note = f" (+{n_refs} reference(s))" if n_refs else ""
                    result_lines.append(("success", f"Report saved to: {file_path}{ref_note}"))
                except Exception as exc:
                    errors.append(f"Error generating report: {exc}")

        elif action == "export":
            try:
                model.io.to_excel(file_path)
                set_last_excel_export_path(str(file_path))
                result_lines.append(("success", f"Exported to: {file_path}"))
            except Exception as exc:
                errors.append(f"Error during export: {exc}")

        elif action == "import":
            if not file_path.is_file():
                errors.append(f"File not found: {file_path}")
            else:
                try:
                    model.io.from_excel(file_path)
                    set_last_excel_import_path(str(file_path))
                    result_lines.append(("success", f"Imported from: {file_path}"))
                except Exception as exc:
                    errors.append(f"Error during import: {exc}")

        else:
            errors.append(f"Unknown action: {action}")

    active_tab = action if action in ("report", "export", "import") else "report"

    return render_template(
        "report.html",
        kdf_path=str(kdf_path or ""),
        last_report_path=default_report if action != "generate_report" else str(file_path or ""),
        last_export_path=str(get_last_excel_export_path() or ""),
        last_import_path=str(get_last_excel_import_path() or ""),
        active_tab=active_tab,
        result={"lines": result_lines, "errors": errors},
    )
