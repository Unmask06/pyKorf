"""Pydantic request/response schemas for the FastAPI endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


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


class PrereqsResponse(BaseModel):
    notes_ok: bool
    pms_ok: bool
    validation_ok: bool
    sharepoint_ok: bool
    issues: list[str] = []
    pms_path: str = ""


class ProjectInfoResponse(BaseModel):
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


class SmartDefaultsResponse(BaseModel):
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


class ModelFullResponse(BaseModel):
    kdf_path: str = ""
    summary: ModelSummaryResponse
    prereqs: PrereqsResponse
    project_info: ProjectInfoResponse
    smart_defaults: SmartDefaultsResponse


class SaveProjectInfoRequest(BaseModel):
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


class SaveResponse(BaseModel):
    message: str
    logs: list[dict[str, str]] = []


# --- Data ---


class ApplyPmsRequest(BaseModel):
    pms_source: str


class ApplyHmbRequest(BaseModel):
    hmb_source: str


class ApplyDataResponse(BaseModel):
    success: bool
    messages: list[dict[str, str]] = []
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


class CenterLayoutResponse(BaseModel):
    message: str


class SnapOrthogonalRequest(BaseModel):
    threshold_deg: float = 10.0
    grid_size: float = 500.0


class SettingsGetResponse(BaseModel):
    settings: list[GlobalSettingSchema] = []
    saved_selections: list[str] = []
    saved_dp_margin: str = "1.25"
    saved_shutoff_margin: str = "1.20"


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


class ExportRequest(BaseModel):
    file_path: str | None = None


class ImportRequest(BaseModel):
    file_path: str | None = None


class BatchReportRequest(BaseModel):
    batch_folder: str | None = None


class ReportResponse(BaseModel):
    success: bool
    messages: list[dict[str, str]] = []
    errors: list[str] = []


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


class PipeCriteriaResponse(BaseModel):
    kdf_path: str = ""
    pipes: list[tuple[int, str]] = []
    existing: dict[str, dict[str, str]] = {}
    codes: dict[str, list[list[str]]] = {}
    fluid_labels: dict[str, str] = {}
    pipe_criteria_values: dict[str, dict[str, dict]] = {}
    pipe_calcs: dict[str, dict] = {}
    units_data: dict[str, Any] = {}
    set_result: dict | None = None
    predict_result: dict | None = None


class SetCriteriaResponse(BaseModel):
    applied: int = 0
    skipped: list[str] = []


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


# --- Browse ---


class PinnedFoldersResponse(BaseModel):
    success: bool = True
    pinned_folders: list[str] = []
    error: str | None = None


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


# --- About ---


class AboutResponse(BaseModel):
    version: str
    release_date: str
