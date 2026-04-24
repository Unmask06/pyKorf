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
    StatusMessage,
)
from pykorf.core.log import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _find_korf_excel(kdf_path: Path) -> Path | None:
    """Auto-detect KORF Excel file alongside a KDF file.

    Looks for ``{stem}.xlsx`` (exact stem match) in the same directory.
    Only returns it if the Excel file is newer than the KDF file,
    ensuring the report was generated from the current model state.
    """
    candidate = kdf_path.parent / f"{kdf_path.stem}.xlsx"
    if not candidate.is_file():
        return None
    try:
        kdf_mtime = kdf_path.stat().st_mtime
        xlsx_mtime = candidate.stat().st_mtime
        if xlsx_mtime >= kdf_mtime:
            return candidate
    except OSError:
        return None
    return None


@router.post("/generate", response_model=ReportResponse, operation_id="generateReport")
async def generate_report(req: GenerateReportRequest) -> ReportResponse:
    """Generate a single-model Excel report.

    When a KORF Excel file is found alongside the KDF (or explicitly provided
    via ``korf_excel_path``), uses KorfReporter to produce a multi-case report
    with per-case sheets and a worst-case summary envelope. Otherwise falls
    back to PykorfReporter (KDF-only, single-case).
    """
    model = await require_model()
    kdf_path = await _sess.get_kdf_path()
    kdf_folder = str(kdf_path.parent) if kdf_path else ""
    kdf_stem = kdf_path.stem if kdf_path else "model"
    default_name = f"{kdf_stem}_report.xlsx"

    from pykorf.app.operation.config.config import set_last_report_path

    report_file = Path(req.report_path) if req.report_path else Path(kdf_folder) / default_name

    messages: list[StatusMessage] = []
    errors = []

    if not report_file.parent.exists():
        errors.append(f"Output directory does not exist: {report_file.parent}")
    else:
        try:
            from pykorf.app.operation.project.references import ReferencesStore
            from pykorf.core.reports.exporter import ResultExporter

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

            korf_excel_path: Path | None = None
            if req.korf_excel_path:
                korf_excel_path = Path(req.korf_excel_path)
            elif kdf_path:
                korf_excel_path = _find_korf_excel(kdf_path)

            if korf_excel_path and korf_excel_path.is_file():
                from pykorf.core.reports.korf_reporter import KorfReporter

                def _do_export():
                    reporter = KorfReporter(
                        excel_path=korf_excel_path,
                        model=model,
                        basis=basis,
                        remarks=remarks,
                        hold=hold,
                        references=references,
                    )
                    exporter = ResultExporter(reporter=reporter)
                    exporter.export_to_excel(str(report_file))

                await asyncio.to_thread(_do_export)
                messages.append(
                    StatusMessage(
                        type="success",
                        message=f"KORF report saved to: {report_file} (source: {korf_excel_path.name})",
                    )
                )
            else:
                from pykorf.app.operation.project.pykorf_file import get_justifications

                def _do_export():
                    justifications = get_justifications(kdf_path) if kdf_path else {}
                    exporter = ResultExporter(
                        model=model,
                        basis=basis,
                        remarks=remarks,
                        hold=hold,
                        references=references,
                        justifications=justifications,
                    )
                    exporter.export_to_excel(str(report_file))

                await asyncio.to_thread(_do_export)
                messages.append(
                    StatusMessage(type="success", message=f"Report saved to: {report_file}")
                )

            set_last_report_path(str(report_file))
        except Exception as exc:
            errors.append(f"Error generating report: {exc}")

    return ReportResponse(success=len(errors) == 0, messages=messages, errors=errors)


@router.post("/export", response_model=ReportResponse, operation_id="exportReport")
async def export_excel(req: ExportRequest) -> ReportResponse:
    """Export model to Excel file."""
    model = await require_model()
    kdf_path = await _sess.get_kdf_path()
    kdf_folder = str(kdf_path.parent) if kdf_path else ""
    kdf_stem = kdf_path.stem if kdf_path else "model"
    default_name = f"{kdf_stem}_export.xlsx"

    file_path = Path(req.file_path) if req.file_path else Path(kdf_folder) / default_name
    messages: list[StatusMessage] = []
    errors = []

    try:
        await asyncio.to_thread(model._io_service.to_excel, file_path)
        messages.append(StatusMessage(type="success", message=f"Exported to: {file_path}"))
    except Exception as exc:
        errors.append(f"Error during export: {exc}")

    return ReportResponse(success=len(errors) == 0, messages=messages, errors=errors)


@router.post("/import", response_model=ReportResponse, operation_id="importReport")
async def import_excel(req: ImportRequest) -> ReportResponse:
    """Import model parameters from Excel file."""
    model = await require_model()
    kdf_path = await _sess.get_kdf_path()
    kdf_folder = str(kdf_path.parent) if kdf_path else ""
    kdf_stem = kdf_path.stem if kdf_path else "model"
    default_name = f"{kdf_stem}_export.xlsx"

    file_path = Path(req.file_path) if req.file_path else Path(kdf_folder) / default_name
    messages: list[StatusMessage] = []
    errors = []

    if not file_path.is_file():
        errors.append(f"File not found: {file_path}. Export the model first.")
    else:
        try:
            await asyncio.to_thread(model._io_service.from_excel, file_path)
            messages.append(StatusMessage(type="success", message=f"Imported from: {file_path}"))
        except Exception as exc:
            errors.append(f"Error during import: {exc}")

    return ReportResponse(success=len(errors) == 0, messages=messages, errors=errors)


@router.post("/batch", response_model=ReportResponse, operation_id="batchReport")
async def batch_report(req: BatchReportRequest) -> ReportResponse:
    """Generate batch report across multiple KDF files in a folder."""
    await require_model()
    kdf_path = await _sess.get_kdf_path()
    kdf_folder = str(kdf_path.parent) if kdf_path else ""

    from pykorf.app.operation.config.config import (
        set_last_batch_folder_path,
        set_last_report_path,
    )

    batch_folder = Path(req.batch_folder) if req.batch_folder else Path(kdf_folder)
    messages: list[StatusMessage] = []
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
                output_path = generator.generate_report(single_report=req.single_report)
                return generator, output_path

            generator, output_path = await asyncio.to_thread(_do_batch)
            set_last_batch_folder_path(str(batch_folder))
            set_last_report_path(output_path)
            messages.append(
                StatusMessage(type="success", message=f"Batch report saved to: {output_path}")
            )
            for err in generator.errors:
                messages.append(StatusMessage(type="warning", message=err))
        except Exception as exc:
            errors.append(f"Error generating batch report: {exc}")

    return ReportResponse(success=len(errors) == 0, messages=messages, errors=errors)
