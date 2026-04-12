"""Report API: /api/report/*."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter

from pykorf.app.api import session_state as _sess
from pykorf.app.api.deps import require_model
from pykorf.app.api.schemas import (
    BatchReportRequest,
    ExportRequest,
    GenerateReportRequest,
    ImportRequest,
    ReportResponse,
)
from pykorf.core.log import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/generate", response_model=ReportResponse)
async def generate_report(req: GenerateReportRequest):
    """Generate a single-model Excel report."""
    model = await require_model()
    kdf_path = await _sess.get_kdf_path()
    kdf_folder = str(kdf_path.parent) if kdf_path else ""
    kdf_stem = kdf_path.stem if kdf_path else "model"
    default_name = f"{kdf_stem}_report.xlsx"

    from pykorf.app.operation.config.config import set_last_report_path

    report_file = Path(req.report_path) if req.report_path else Path(kdf_folder) / default_name

    messages = []
    errors = []

    if not report_file.parent.exists():
        errors.append(f"Output directory does not exist: {report_file.parent}")
    else:
        try:
            from pykorf.core.reports.exporter import ResultExporter
            from pykorf.app.operation.project.references import ReferencesStore

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

            def _do_export():
                exporter = ResultExporter(
                    model, basis=basis, remarks=remarks, hold=hold, references=references
                )
                exporter.export_to_excel(str(report_file))

            await asyncio.to_thread(_do_export)
            set_last_report_path(str(report_file))
            messages.append({"type": "success", "message": f"Report saved to: {report_file}"})
        except Exception as exc:
            errors.append(f"Error generating report: {exc}")

    return ReportResponse(success=len(errors) == 0, messages=messages, errors=errors)


@router.post("/export", response_model=ReportResponse)
async def export_excel(req: ExportRequest):
    """Export model to Excel file."""
    model = await require_model()
    kdf_path = await _sess.get_kdf_path()
    kdf_folder = str(kdf_path.parent) if kdf_path else ""
    kdf_stem = kdf_path.stem if kdf_path else "model"
    default_name = f"{kdf_stem}_export.xlsx"

    file_path = Path(req.file_path) if req.file_path else Path(kdf_folder) / default_name
    messages = []
    errors = []

    try:
        await asyncio.to_thread(model._io_service.to_excel, file_path)
        messages.append({"type": "success", "message": f"Exported to: {file_path}"})
    except Exception as exc:
        errors.append(f"Error during export: {exc}")

    return ReportResponse(success=len(errors) == 0, messages=messages, errors=errors)


@router.post("/import", response_model=ReportResponse)
async def import_excel(req: ImportRequest):
    """Import model parameters from Excel file."""
    model = await require_model()
    kdf_path = await _sess.get_kdf_path()
    kdf_folder = str(kdf_path.parent) if kdf_path else ""
    kdf_stem = kdf_path.stem if kdf_path else "model"
    default_name = f"{kdf_stem}_export.xlsx"

    file_path = Path(req.file_path) if req.file_path else Path(kdf_folder) / default_name
    messages = []
    errors = []

    if not file_path.is_file():
        errors.append(f"File not found: {file_path}. Export the model first.")
    else:
        try:
            await asyncio.to_thread(model._io_service.from_excel, file_path)
            messages.append({"type": "success", "message": f"Imported from: {file_path}"})
        except Exception as exc:
            errors.append(f"Error during import: {exc}")

    return ReportResponse(success=len(errors) == 0, messages=messages, errors=errors)


@router.post("/batch", response_model=ReportResponse)
async def batch_report(req: BatchReportRequest):
    """Generate batch report across multiple KDF files in a folder."""
    await require_model()
    kdf_path = await _sess.get_kdf_path()
    kdf_folder = str(kdf_path.parent) if kdf_path else ""

    from pykorf.app.operation.config.config import (
        set_last_batch_folder_path,
        set_last_report_path,
    )

    batch_folder = Path(req.batch_folder) if req.batch_folder else Path(kdf_folder)
    messages = []
    errors = []

    if not batch_folder.exists():
        errors.append(f"Batch folder not found: {batch_folder}")
    elif not batch_folder.is_dir():
        errors.append(f"Batch path is not a directory: {batch_folder}")
    else:
        try:
            from pykorf.app.operation.processor.batch_report import BatchReportGenerator

            def _do_batch():
                generator = BatchReportGenerator(batch_folder)
                output_path = generator.generate_report()
                return generator, output_path

            generator, output_path = await asyncio.to_thread(_do_batch)
            set_last_batch_folder_path(str(batch_folder))
            set_last_report_path(output_path)
            messages.append({"type": "success", "message": f"Batch report saved to: {output_path}"})
            for err in generator.errors:
                messages.append({"type": "warning", "message": err})
        except Exception as exc:
            errors.append(f"Error generating batch report: {exc}")

    return ReportResponse(success=len(errors) == 0, messages=messages, errors=errors)
