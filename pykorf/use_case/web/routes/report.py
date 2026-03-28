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

    # Default paths based on KDF file
    kdf_folder = str(kdf_path.parent) if kdf_path else ""
    kdf_stem = kdf_path.stem if kdf_path else "model"

    default_report_name = f"{kdf_stem}_report.xlsx"
    default_export_name = f"{kdf_stem}_export.xlsx"

    # Report folder (use last used or KDF folder)
    last_report = get_last_report_path()
    report_folder = str(Path(last_report).parent) if last_report else kdf_folder

    # Export path — only pre-fill if user has previously exported (no synthetic defaults)
    last_export = get_last_excel_export_path()
    export_path = str(last_export) if last_export else ""
    export_exists = Path(last_export).is_file() if last_export else False

    # Import path — follows the last export path
    last_import = get_last_excel_import_path()
    import_path = str(last_import) if last_import else export_path

    if request.method == "GET":
        return render_template(
            "report.html",
            kdf_path=str(kdf_path or ""),
            report_folder=report_folder,
            default_report_name=default_report_name,
            default_export_name=default_export_name,
            export_path=export_path,
            import_path=import_path,
            export_exists=export_exists,
            result=None,
        )

    action = (request.form.get("action") or "generate_report").strip()
    file_path_str = (request.form.get("file_path") or "").strip()

    result_lines: list[tuple[str, str]] = []
    errors: list[str] = []

    if action == "generate_report":
        # For report, file_path_str is the folder
        report_dir = Path(file_path_str) if file_path_str else Path(kdf_folder)
        if not report_dir.exists():
            errors.append(f"Output directory does not exist: {report_dir}")
        elif not report_dir.is_dir():
            errors.append(f"Output path is not a directory: {report_dir}")
        elif not os.access(report_dir, os.W_OK):
            errors.append(f"Output directory is not writable: {report_dir}")
        else:
            try:
                from pykorf.reports.exporter import ResultExporter

                report_file = report_dir / default_report_name
                exporter = ResultExporter(model)
                exporter.export_to_excel(str(report_file))
                set_last_report_path(str(report_file))
                result_lines.append(("success", f"Report saved to: {report_file}"))
            except Exception as exc:
                errors.append(f"Error generating report: {exc}")

    elif action == "export":
        file_path = Path(file_path_str) if file_path_str else Path(kdf_folder) / default_export_name
        try:
            model.io.to_excel(file_path)
            set_last_excel_export_path(str(file_path))
            export_path = str(file_path)
            export_exists = True
            result_lines.append(("success", f"Exported to: {file_path}"))
        except Exception as exc:
            errors.append(f"Error during export: {exc}")

    elif action == "import":
        file_path = Path(file_path_str) if file_path_str else Path(export_path)
        if not file_path.is_file():
            errors.append(f"File not found: {file_path}. Please export first before importing.")
        else:
            try:
                model.io.from_excel(file_path)
                set_last_excel_import_path(str(file_path))
                import_path = str(file_path)
                result_lines.append(("success", f"Imported from: {file_path}"))
            except Exception as exc:
                errors.append(f"Error during import: {exc}")

    else:
        errors.append(f"Unknown action: {action}")

    return render_template(
        "report.html",
        kdf_path=str(kdf_path or ""),
        report_folder=report_folder,
        default_report_name=default_report_name,
        default_export_name=default_export_name,
        export_path=export_path,
        import_path=import_path,
        export_exists=export_exists,
        result={"lines": result_lines, "errors": errors},
    )
