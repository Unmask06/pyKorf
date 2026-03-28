"""Generate Report route: /model/report."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Blueprint, redirect, render_template, request

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
        get_last_batch_folder_path,
        get_last_excel_export_path,
        get_last_excel_import_path,
        get_last_report_path,
        set_last_batch_folder_path,
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

    # Report folder and last generated file
    last_report = get_last_report_path()
    report_folder = str(Path(last_report).parent) if last_report else kdf_folder
    last_report_file = str(last_report) if last_report and Path(last_report).is_file() else ""

    # Batch report folder
    last_batch = get_last_batch_folder_path()
    batch_folder_path = str(last_batch) if last_batch else kdf_folder

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
            last_report_file=last_report_file,
            batch_folder_path=batch_folder_path,
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
                from pykorf.use_case.web.references import ReferencesStore

                ref_store = ReferencesStore.load(kdf_path) if kdf_path else None
                basis = ref_store.basis if ref_store else ""
                references = (
                    [
                        {
                            "name": r.name,
                            "category": r.category,
                            "link": r.link,
                            "description": r.description,
                        }
                        for r in ref_store.references
                    ]
                    if ref_store
                    else []
                )
                report_file = report_dir / default_report_name
                exporter = ResultExporter(model, basis=basis, references=references)
                exporter.export_to_excel(str(report_file))
                set_last_report_path(str(report_file))
                last_report_file = str(report_file)
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

    elif action == "batch_report":
        batch_folder_str = (request.form.get("batch_folder") or "").strip()
        batch_folder = Path(batch_folder_str) if batch_folder_str else Path(kdf_folder)
        if not batch_folder.exists():
            errors.append(f"Batch folder not found: {batch_folder}")
        elif not batch_folder.is_dir():
            errors.append(f"Batch path is not a directory: {batch_folder}")
        else:
            try:
                from pykorf.use_case.batch_report import BatchReportGenerator

                generator = BatchReportGenerator(batch_folder)
                output_path = generator.generate_report()
                set_last_batch_folder_path(str(batch_folder))
                batch_folder_path = str(batch_folder)
                set_last_report_path(output_path)
                last_report_file = output_path
                result_lines.append(("success", f"Batch report saved to: {output_path}"))
                for err in generator.errors:
                    result_lines.append(("warning", err))
            except Exception as exc:
                errors.append(f"Error generating batch report: {exc}")

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
        last_report_file=last_report_file,
        batch_folder_path=batch_folder_path,
        result={"lines": result_lines, "errors": errors},
    )


@bp.route("/model/report/open-file", methods=["POST"])
def open_report_file():
    """Open the last generated report Excel file with the system default application."""
    file_path = (request.form.get("file_path") or "").strip()
    if file_path and Path(file_path).is_file():
        os.startfile(file_path)
    return redirect("/model/report")
