"""Report API: /api/report/*."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter

from pykorf.app.api import session_state as _sess
from pykorf.app.api.deps import require_model
from pykorf.app.api.schemas import (
    BatchFileStatus,
    BatchReportRequest,
    ExportRequest,
    GenerateReportRequest,
    ImportRequest,
    KorfExcelStatusResponse,
    ReportResponse,
    StatusMessage,
)
from pykorf.core.log import get_logger

logger = get_logger(__name__)
router = APIRouter()

MAX_STALENESS_OVERRIDE_SECONDS = 60.0


def get_staleness_seconds(kdf_path: Path, korf_excel_path: Path) -> float | None:
    """Return seconds between KDF and KORF Excel modification times.

    Positive value means KORF Excel is stale (KDF modified after Excel).
    Returns None if either file doesn't exist or stats can't be read.
    """
    try:
        kdf_mtime = kdf_path.stat().st_mtime
        korf_mtime = korf_excel_path.stat().st_mtime
        return max(0.0, kdf_mtime - korf_mtime)
    except OSError:
        return None


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


def _korf_excel_status(kdf_path: Path) -> KorfExcelStatusResponse:
    """Return KORF Excel presence and staleness status.

    Returns the xlsx path if it exists (regardless of staleness), and
    ``is_stale=True`` when the xlsx is older than the kdf.

    Also returns:
    - staleness_seconds: How many seconds stale (0 if not stale)
    - can_override: True if stale but within 60s threshold
    """
    candidate = kdf_path.parent / f"{kdf_path.stem}.xlsx"
    if not candidate.is_file():
        return KorfExcelStatusResponse(
            korf_excel_path=None,
            is_stale=False,
            staleness_seconds=None,
            can_override=False,
        )

    staleness_seconds = get_staleness_seconds(kdf_path, candidate)
    if staleness_seconds is None:
        return KorfExcelStatusResponse(
            korf_excel_path=None,
            is_stale=False,
            staleness_seconds=None,
            can_override=False,
        )

    is_stale = staleness_seconds > 0
    can_override = is_stale and staleness_seconds <= MAX_STALENESS_OVERRIDE_SECONDS

    return KorfExcelStatusResponse(
        korf_excel_path=str(candidate),
        is_stale=is_stale,
        staleness_seconds=staleness_seconds,
        can_override=can_override,
    )


@router.get("/korf-status", response_model=KorfExcelStatusResponse, operation_id="korfExcelStatus")
async def korf_excel_status() -> KorfExcelStatusResponse:
    """Check KORF Excel source status (presence + staleness).

    Returns the detected KORF Excel path and whether it is stale
    (i.e., the KDF has been modified since the Excel was generated).
    """
    kdf_path = await _sess.get_kdf_path()
    if not kdf_path:
        return KorfExcelStatusResponse(korf_excel_path=None, is_stale=False)
    return _korf_excel_status(kdf_path)


@router.post(
    "/generate",
    response_model=ReportResponse,
    operation_id="generateReport",
)
async def generate_report(
    req: GenerateReportRequest,
) -> ReportResponse:
    """Generate a single-model Excel report.

    Uses ``mode`` to select the reporter:
    - ``"single"`` (default): PykorfReporter via KDF data only.
    - ``"multi"``: KorfReporter via auto-detected KORF Excel alongside the KDF.
      Requires the KORF Excel file to exist and be up-to-date.
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

            is_multi = req.mode == "multi"

            if is_multi:
                # Check for KORF Excel (even if stale)
                korf_excel_path = kdf_path.parent / f"{kdf_path.stem}.xlsx" if kdf_path else None

                if not korf_excel_path or not korf_excel_path.is_file():
                    errors.append(
                        "Multi-case mode requires a KORF Excel report alongside the KDF "
                        f"(expected: {kdf_path.stem}.xlsx in the same folder). "
                        "Generate it from KORF first."
                    )
                else:
                    # Load justifications from .pykorf sidecar
                    from pykorf.app.operation.project.pykorf_file import get_justifications

                    justifications = get_justifications(kdf_path) if kdf_path else {}

                    # Check staleness with threshold
                    staleness_seconds = get_staleness_seconds(kdf_path, korf_excel_path)

                    if staleness_seconds and staleness_seconds > MAX_STALENESS_OVERRIDE_SECONDS:
                        # Hard block - exceeds 60s threshold
                        errors.append(
                            f"KORF Excel is {int(staleness_seconds)}s stale (exceeds "
                            f"{int(MAX_STALENESS_OVERRIDE_SECONDS)}s threshold). "
                            "Regenerate from KORF first."
                        )
                    elif staleness_seconds and staleness_seconds > 0:
                        # Soft block - within 60s threshold, need override
                        if not req.skip_stale_check:
                            errors.append(
                                f"KORF Excel is {int(staleness_seconds)}s stale. "
                                f"Check 'Proceed with stale data' to override "
                                f"(max {int(MAX_STALENESS_OVERRIDE_SECONDS)}s)."
                            )
                        else:
                            # User requested override - proceed with warning
                            messages.append(
                                StatusMessage(
                                    type="warning",
                                    message=f"Proceeding with {int(staleness_seconds)}s stale KORF Excel.",
                                )
                            )
                            from pykorf.core.reports.korf_reporter import KorfReporter

                            def _do_export():
                                reporter = KorfReporter(
                                    excel_path=korf_excel_path,
                                    model=model,
                                    basis=basis,
                                    remarks=remarks,
                                    hold=hold,
                                    references=references,
                                    justifications=justifications,
                                )
                                exporter = ResultExporter(reporter=reporter)
                                exporter.export_to_excel(
                                    str(report_file), pipe_columns=req.pipe_columns
                                )

                            await asyncio.to_thread(_do_export)
                            messages.append(
                                StatusMessage(
                                    type="success",
                                    message=(
                                        f"Multi-case report saved to: {report_file} "
                                        f"(source: {korf_excel_path.name})"
                                    ),
                                )
                            )
                    else:
                        # Not stale - proceed normally
                        from pykorf.core.reports.korf_reporter import KorfReporter

                        def _do_export():
                            reporter = KorfReporter(
                                excel_path=korf_excel_path,
                                model=model,
                                basis=basis,
                                remarks=remarks,
                                hold=hold,
                                references=references,
                                justifications=justifications,
                            )
                            exporter = ResultExporter(reporter=reporter)
                            exporter.export_to_excel(
                                str(report_file), pipe_columns=req.pipe_columns
                            )

                        await asyncio.to_thread(_do_export)
                        messages.append(
                            StatusMessage(
                                type="success",
                                message=(
                                    f"Multi-case report saved to: {report_file} "
                                    f"(source: {korf_excel_path.name})"
                                ),
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
                    exporter.export_to_excel(str(report_file), pipe_columns=req.pipe_columns)

                await asyncio.to_thread(_do_export)
                messages.append(
                    StatusMessage(type="success", message=f"Report saved to: {report_file}")
                )

            if not errors:
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
    """Generate batch report across multiple KDF files in a folder.

    Uses ``mode`` to select the reporter:
    - ``"single"`` (default): PykorfReporter per KDF.
    - ``"multi"``: KorfReporter per KDF (auto-detects KORF Excel alongside each KDF).

    When ``validate_only=True`` and ``mode="multi"``, scans for KORF Excel
    files and returns which KDFs are missing/stale without generating.
    """
    await require_model()
    kdf_path = await _sess.get_kdf_path()
    kdf_folder = str(kdf_path.parent) if kdf_path else ""

    from pykorf.app.operation.config.config import (
        set_last_batch_folder_path,
        set_last_report_path,
    )

    batch_folder = Path(req.batch_folder) if req.batch_folder else Path(kdf_folder)
    messages: list[StatusMessage] = []
    file_results: list[BatchFileStatus] = []
    errors = []

    if not batch_folder.exists():
        errors.append(f"Batch folder not found: {batch_folder}")
    elif not batch_folder.is_dir():
        errors.append(f"Batch path is not a directory: {batch_folder}")
    elif req.validate_only and req.mode == "multi":
        kdf_files = sorted(batch_folder.rglob("*.kdf"))
        if req.path_keyword_filter:
            keyword = req.path_keyword_filter.strip().lower()
            if keyword:
                kdf_files = [p for p in kdf_files if keyword in str(p).lower()]
        valid_count = 0
        for kf in kdf_files:
            status = _korf_excel_status(kf)
            if status.korf_excel_path and not status.is_stale:
                valid_count += 1
                file_results.append(
                    BatchFileStatus(filename=kf.name, ok=True)
                )
            elif status.korf_excel_path and status.is_stale:
                messages.append(
                    StatusMessage(
                        type="warning",
                        message=f"{kf.name}: KORF Excel stale",
                    )
                )
                file_results.append(
                    BatchFileStatus(filename=kf.name, ok=False, issue="KORF Excel stale")
                )
            else:
                messages.append(
                    StatusMessage(
                        type="warning",
                        message=f"{kf.name}: KORF Excel missing",
                    )
                )
                file_results.append(
                    BatchFileStatus(filename=kf.name, ok=False, issue="KORF Excel missing")
                )
        messages.insert(
            0,
            StatusMessage(
                type="info",
                message=f"{valid_count} of {len(kdf_files)} KDF files have valid KORF Excel",
            ),
        )
    else:
        try:
            from pykorf.app.operation.processor.batch_report import BatchReportGenerator

            is_multi = req.mode == "multi"

            def _do_batch():
                generator = BatchReportGenerator(batch_folder)
                output_path = generator.generate_report(
                    single_report=req.single_report,
                    multi_case=is_multi,
                    pipe_columns=req.pipe_columns,
                    path_keyword_filter=req.path_keyword_filter,
                )
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

    return ReportResponse(success=len(errors) == 0, messages=messages, errors=errors, file_results=file_results)
