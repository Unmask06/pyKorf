"""Pydantic request/response schemas for the FastAPI endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class EmptyRequest(BaseModel):
    """Explicit empty request payload for body-less POST endpoints."""


class StatusMessage(BaseModel):
    type: str
    message: str


# --- Session ---


class SessionOpenRequest(BaseModel):
    kdf_path: str


class SessionStatusResponse(BaseModel):
    model_loaded: bool
    kdf_path: str | None = None
    kdf_mtime: str | None = None
    recent_files: list[str] = []
    setup_ok: bool = False
    sp_ok: bool = False
    doc_register_ok: bool = False
    skip_sp_override: bool = False
    username: str = ""
    update_available: bool = False
    version: str = ""


class SessionReloadResponse(BaseModel):
    message: str


class SessionCloseResponse(BaseModel):
    message: str


# --- Model ---


class ModelSummaryResponse(BaseModel):
    num_pipes: int = 0
    num_junctions: int = 0
    num_pumps: int = 0
    num_valves: int = 0
    num_feeds: int = 0
    num_products: int = 0


class ValidationIssue(BaseModel):
    """Categorized validation issue."""

    message: str
    category: str


class PrereqsResponse(BaseModel):
    notes_ok: bool
    pms_ok: bool
    validation_ok: bool
    sharepoint_ok: bool
    issues: list[ValidationIssue] = []
    pms_path: str = ""


class ProjectInfoBase(BaseModel):
    """Shared project info fields for request/response contexts."""

    company1: str = ""
    company2: str = ""
    project_name1: str = ""
    project_name2: str = ""
    item_name1: str = ""
    item_name2: str = ""
    prepared_by: str = ""
    checked_by: str = ""
    approved_by: str = ""
    date: str = ""
    project_no: str = ""
    revision: str = ""


class ProjectInfoResponse(ProjectInfoBase):
    """Project info fetched from KDF."""


class SmartDefaultsResponse(ProjectInfoBase):
    """User's saved preferences for project info."""


class ModelFullResponse(BaseModel):
    kdf_path: str = ""
    summary: ModelSummaryResponse
    prereqs: PrereqsResponse
    project_info: ProjectInfoResponse
    smart_defaults: SmartDefaultsResponse


class SaveProjectInfoRequest(ProjectInfoBase):
    """Request to save project info to KDF."""


class SaveResponse(BaseModel):
    message: str
    logs: list[StatusMessage] = []


# --- Data ---


class ApplyPmsRequest(BaseModel):
    pms_source: str


class ApplyHmbRequest(BaseModel):
    hmb_source: str


class ApplyDataResponse(BaseModel):
    success: bool
    messages: list[StatusMessage] = []
    errors: list[str] = []


# --- Generic ---


class OkResponse(BaseModel):
    """Generic success/failure response for simple write operations."""

    success: bool
    message: str = ""
    error: str | None = None


# --- Settings ---


class GlobalSettingSchema(BaseModel):
    id: str
    name: str
    description: str


class ApplyGlobalSettingsRequest(BaseModel):
    setting_ids: list[str]
    dp_margin: float = 1.25
    shutoff_margin: float = 1.20
    min_pump_elevation: float = 0.5


class CenterLayoutResponse(BaseModel):
    message: str


class SnapOrthogonalRequest(BaseModel):
    threshold_deg: float = 10.0
    grid_size: float = 500.0


class SettingsGetResponse(BaseModel):
    settings: list[GlobalSettingSchema] = []
    saved_selections: list[str] = []
    saved_dp_margin: str = str(ApplyGlobalSettingsRequest.model_fields["dp_margin"].default)
    saved_shutoff_margin: str = str(
        ApplyGlobalSettingsRequest.model_fields["shutoff_margin"].default
    )
    saved_min_pump_elev: str = str(
        ApplyGlobalSettingsRequest.model_fields["min_pump_elevation"].default
    )


class SettingsApplyResponse(BaseModel):
    results: dict[str, list[str]] = {}
    errors: list[str] = []
    message: str = ""


# --- Bulk Copy ---


class BulkCopyRequest(BaseModel):
    ref_pipe: str
    target_pipes: str = ""
    exclude: bool = False


class BulkCopyResponse(BaseModel):
    success: bool
    updated_pipes: list[str] = []
    updated_count: int = 0
    error: str | None = None


# --- Report ---


class GenerateReportRequest(BaseModel):
    report_path: str | None = None
    mode: str = "single"  # "single" | "multi"
    pipe_columns: list[str] | None = None  # Optional subset of pipe columns to include


class ExportRequest(BaseModel):
    file_path: str | None = None


class ImportRequest(BaseModel):
    file_path: str | None = None


class BatchReportRequest(BaseModel):
    batch_folder: str | None = None
    single_report: bool = False
    mode: str = "single"  # "single" | "multi"
    validate_only: bool = False  # If True, only validate multi-case readiness
    pipe_columns: list[str] | None = None  # Optional subset of pipe columns to include


class ReportResponse(BaseModel):
    success: bool
    messages: list[StatusMessage] = []
    errors: list[str] = []


class KorfExcelStatusResponse(BaseModel):
    """KORF Excel source status for the report generator."""

    korf_excel_path: str | None = None
    is_stale: bool = False


# --- Pipe Criteria ---


class PipeCriteriaEntry(BaseModel):
    state: str = ""
    criteria: str = ""


class SetPipeCriteriaRequest(BaseModel):
    criteria: dict[str, PipeCriteriaEntry]


class PredictCriteriaRequest(BaseModel):
    """Empty — predicts for all pipes in current model."""


class PredictCriteriaResponse(BaseModel):
    predicted: dict[str, PipeCriteriaEntry]
    filled_state: int = 0
    filled_criteria: int = 0
    errors: list[str] = []


class CriteriaCodeInfo(BaseModel):
    code: str
    label: str


class CriteriaValuesInfo(BaseModel):
    max_dp: float | None = None
    max_vel: float | None = None
    min_vel: float = 0.0
    rho_v2_min: float | None = None
    rho_v2_max: float | None = None


class PipeCalcInfo(BaseModel):
    dp_calc: float | None = None
    vel_calc: float | None = None
    rho_v2_calc: float | None = None
    length_m: float | None = None
    line_size: str | None = None


class CriteriaViolationsInfo(BaseModel):
    dp_exceeds: bool = False
    vel_below_min: bool = False
    vel_above_max: bool = False
    rho_v2_below_min: bool = False
    rho_v2_above_max: bool = False
    overall: str = "PASS"


class UnitConversionInfo(BaseModel):
    target_unit: str
    multiplier: float = 1.0
    offset: float = 0.0
    factor: float | None = None


class ModelPipesResponse(BaseModel):
    pipes: list[str] = []


class ViolationSummary(BaseModel):
    total_pipes_with_violations: int = 0
    total_violations: int = 0
    justified_pipes: int = 0
    justified_violations: int = 0
    pipes_needing_justification: int = 0
    violations_needing_justification: int = 0


class PipeCriteriaResponse(BaseModel):
    kdf_path: str = ""
    pipes: list[tuple[int, str]] = []
    existing: dict[str, PipeCriteriaEntry] = {}
    codes: dict[str, list[tuple[str, str]]] = {}
    fluid_labels: dict[str, str] = {}
    pipe_criteria_values: dict[str, dict[str, CriteriaValuesInfo]] = {}
    pipe_calcs: dict[str, PipeCalcInfo] = {}
    pipe_criteria_violations: dict[str, dict[str, CriteriaViolationsInfo]] = {}
    units_data: dict[str, dict[str, UnitConversionInfo]] = {}
    set_result: SetCriteriaResponse | None = None
    predict_result: PredictCriteriaResponse | None = None
    justifications: dict[str, str] = {}
    violation_summary: ViolationSummary = ViolationSummary()


class SetCriteriaResponse(BaseModel):
    applied: int = 0
    skipped: list[str] = []


class JustificationRequest(BaseModel):
    pipe_name: str
    justification: str


class JustificationSaveResponse(BaseModel):
    justifications: dict[str, str] = {}
    saved: bool = True


# --- References ---


class ReferenceSchema(BaseModel):
    id: str
    name: str
    link: str
    description: str = ""
    category: str = "Other"


class ReferencesStoreSchema(BaseModel):
    basis: str = ""
    remarks: str = ""
    hold: str = ""
    references: list[ReferenceSchema] = []


class SaveAllReferencesRequest(BaseModel):
    basis: str = ""
    remarks: str = ""
    hold: str = ""


class AddReferenceRequest(BaseModel):
    edit_id: str = ""
    name: str
    link: str
    description: str = ""
    category: str = "Other"


class UpdateReferenceRequest(BaseModel):
    ref_id: str
    name: str = ""
    link: str = ""
    description: str = ""
    category: str = "Other"


class DeleteReferenceRequest(BaseModel):
    ref_id: str


class ShortcutsResponse(BaseModel):
    count: int = 0
    path: str = ""
    error: str | None = None


# --- Preferences ---


class SpOverrideEntry(BaseModel):
    local: str
    sp_url: str


class PreferencesResponse(BaseModel):
    sp_overrides: dict[str, str] = {}
    skip_sp_override: bool = False
    license_key: str | None = None
    doc_register_excel_path: str | None = None
    doc_register_sp_site_url: str | None = None
    doc_register_db_last_imported: str | None = None
    sp_overrides_configured: bool = False
    default_doc_register_url: str = ""
    default_pms_url: str = ""
    default_sp_site_url: str = ""
    last_batch_folder_path: str | None = None


class AddSpOverrideRequest(BaseModel):
    local_path: str
    sp_url: str


class EditSpOverrideRequest(BaseModel):
    original_local_path: str
    local_path: str
    sp_url: str


class DeleteSpOverrideRequest(BaseModel):
    local_path: str


class SetSkipSpRequest(BaseModel):
    skip: bool


class SetLicenseKeyRequest(BaseModel):
    license_key: str


class SetDocRegisterConfigRequest(BaseModel):
    excel_path: str | None = None
    sp_site_url: str | None = None


class LicenseValidationResponse(BaseModel):
    valid: bool
    expiry: str | None = None
    error: str = ""


class DocRegisterRebuildResponse(BaseModel):
    success: bool = False
    message: str = ""
    stats: dict[str, Any] = {}
    error: str | None = None


class ResolveSpUrlRequest(BaseModel):
    sp_url: str


# --- Browse ---


class PinnedFoldersResponse(BaseModel):
    success: bool = True
    pinned_folders: list[str] = []
    error: str | None = None


class BrowseRequest(BaseModel):
    path: str = ""
    filter: str = "any"


class PinnedFolderRequest(BaseModel):
    folder: str


class BrowseEntryDir(BaseModel):
    name: str
    path: str
    synced: bool = False


class BrowseEntryFile(BaseModel):
    name: str
    path: str
    sharepoint_url: str | None = None


class BrowseResponse(BaseModel):
    current: str
    current_sp_url: str | None = None
    parent: str | None = None
    drives: list[str] = []
    pinned_folders: list[str] = []
    dirs: list[BrowseEntryDir] = []
    files: list[BrowseEntryFile] = []


# --- Doc Register ---


class DocRegisterSearchEddrRequest(BaseModel):
    q: str = ""


class DocRegisterSearchQueryRequest(BaseModel):
    doc_no: str = ""


class DocRegisterSearchFilesRequest(BaseModel):
    q: str = ""


class DocRegisterStatusResponse(BaseModel):
    excel_path: str | None = None
    sp_site_url: str | None = None
    db_exists: bool = False
    is_stale: bool = False
    db_stats: dict[str, Any] = {}


class EddrResult(BaseModel):
    document_no: str
    title: str


class QueryEntryResult(BaseModel):
    name: str
    modified: str | None = None
    modified_by: str | None = None
    path: str | None = None
    item_type: str | None = None


class DocRegisterSearchEddrResponse(BaseModel):
    results: list[EddrResult] = []


class DocRegisterSearchQueryResponse(BaseModel):
    results: list[QueryEntryResult] = []


class DocRegisterSearchFilesResponse(BaseModel):
    results: list[QueryEntryResult] = []


class DocRegisterConfigResponse(BaseModel):
    excel_path: str | None = None
    sp_site_url: str | None = None


# --- About ---


class AboutResponse(BaseModel):
    version: str
    release_date: str


class ShutdownResponse(BaseModel):
    status: str
