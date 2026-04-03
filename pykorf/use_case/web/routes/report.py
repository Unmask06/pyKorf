"""Generate Report route: /model/report."""

from __future__ import annotations

import os
from pathlib import Path

import structlog
from flask import Blueprint, render_template, request

from pykorf.use_case.web import session as _sess
from pykorf.use_case.web.helpers import is_redirect, require_model

logger = structlog.get_logger(__name__)
bp = Blueprint("report", __name__)


@bp.route("/model/report", methods=["GET", "POST"])
def generate_report():
    """Render and handle the Reports page (Report, Export, Import)."""
    model = require_model()
    if is_redirect(model):
        return model

    kdf_path = _sess.get_kdf_path()

    kdf_folder = str(kdf_path.parent) if kdf_path else ""
    kdf_stem = kdf_path.stem if kdf_path else "model"

    report_path = str(Path(kdf_folder) / f"{kdf_stem}_report.xlsx")
    export_path = str(Path(kdf_folder) / f"{kdf_stem}_export.xlsx")
    export_exists = Path(export_path).is_file()
    import_path = export_path if export_exists else ""
    import_exists = export_exists

    ctx = {
        "kdf_path": str(kdf_path or ""),
        "report_path": report_path,
        "export_path": export_path,
        "export_exists": export_exists,
        "import_path": import_path,
        "import_exists": import_exists,
        "batch_folder_path": kdf_folder,
    }

    if request.method == "GET":
        return render_template("report.html", **ctx, result=None)

    action = (request.form.get("action") or "generate_report").strip()
    file_path_str = (request.form.get("file_path") or "").strip()

    result_lines: list[tuple[str, str]] = []
    errors: list[str] = []

    if action == "generate_report":
        report_file = Path(report_path)
        report_dir = report_file.parent
        if not report_dir.exists():
            errors.append(f"Output directory does not exist: {report_dir}")
        elif not os.access(report_dir, os.W_OK):
            errors.append(f"Output directory is not writable: {report_dir}")
        else:
            try:
                from pykorf.reports.exporter import ResultExporter
                from pykorf.use_case.web.references import ReferencesStore

                ref_store = ReferencesStore.load(kdf_path) if kdf_path else None
                basis = ref_store.basis if ref_store else ""
                remarks = ref_store.remarks if ref_store else ""
                hold = ref_store.hold if ref_store else ""
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
                exporter = ResultExporter(
                    model, basis=basis, remarks=remarks, hold=hold, references=references
                )
                exporter.export_to_excel(str(report_file))
                result_lines.append(("success", f"Report saved to: {report_file}"))
            except Exception as exc:
                errors.append(f"Error generating report: {exc}")

    elif action == "export":
        try:
            model.io.to_excel(Path(export_path))
            export_exists = True
            import_path = export_path
            import_exists = True
            result_lines.append(("success", f"Exported to: {export_path}"))
        except Exception as exc:
            errors.append(f"Error during export: {exc}")

    elif action == "import":
        file_path = Path(file_path_str) if file_path_str else Path(import_path)
        if not file_path.is_file():
            errors.append(f"File not found: {file_path}. Export the model first before importing.")
        else:
            try:
                model.io.from_excel(file_path)
                import_path = str(file_path)
                import_exists = True
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
                result_lines.append(("success", f"Batch report saved to: {output_path}"))
                for err in generator.errors:
                    result_lines.append(("warning", err))
            except Exception as exc:
                errors.append(f"Error generating batch report: {exc}")

    else:
        errors.append(f"Unknown action: {action}")

    ctx.update(
        export_exists=export_exists,
        import_path=import_path,
        import_exists=import_exists,
    )
    return render_template("report.html", **ctx, result={"lines": result_lines, "errors": errors})
