/**
 * Auto-generated TypeScript types mirroring FastAPI Pydantic schemas.
 *
 * KEY SESSION NUANCES:
 * - After every model save (POST /api/model/save, /api/model/project-info, etc.)
 *   the backend calls _sess.reload() which re-parses the KDF from disk.
 * - The frontend must call fetchSummary() after mutations to stay in sync.
 * - Stale detection: if KDF is modified externally (by KORF GUI),
 *   require_model() auto-reloads. The X-Model-Stale header signals this.
 * - The 409 status means "no model loaded" — frontend should redirect to /.
 * - PMS auto-apply on stale: apply_pms_if_stale() runs on GET /api/model/summary.
 */

// ─── Session ──────────────────────────────────────────────────────────────────

export interface SessionStatusResponse {
  model_loaded: boolean
  kdf_path: string | null
  kdf_mtime: string | null
  recent_files: string[]
  setup_ok: boolean
  sp_ok: boolean
  doc_register_ok: boolean
  skip_sp_override: boolean
  username: string
  update_available: boolean
}

export interface SessionOpenRequest {
  kdf_path: string
}

export interface SessionReloadResponse {
  message: string
}

export interface SessionCloseResponse {
  message: string
}

// ─── Model ────────────────────────────────────────────────────────────────────

export interface ModelSummary {
  num_pipes: number
  num_junctions: number
  num_pumps: number
  num_valves: number
  num_feeds: number
  num_products: number
}

export interface Prereqs {
  notes_ok: boolean
  pms_ok: boolean
  validation_ok: boolean
  sharepoint_ok: boolean
  issues: string[]
  pms_path: string
}

export interface ProjectInfo {
  company1: string
  company2: string
  project_name1: string
  project_name2: string
  item_name1: string
  item_name2: string
  prepared_by: string
  checked_by: string
  approved_by: string
  date: string
  project_no: string
  revision: string
}

export interface SmartDefaults extends ProjectInfo {}

export interface ModelFullResponse {
  kdf_path: string
  summary: ModelSummary
  prereqs: Prereqs
  project_info: ProjectInfo
  smart_defaults: SmartDefaults
}

export interface SaveProjectInfoRequest extends ProjectInfo {}

export interface SaveResponse {
  message: string
  logs: Array<{ type: string; message: string }>
}

// ─── Data ─────────────────────────────────────────────────────────────────────

export interface ApplyPmsRequest {
  pms_source: string
}

export interface ApplyHmbRequest {
  hmb_source: string
}

export interface ApplyDataResponse {
  success: boolean
  messages: Array<{ type: string; message: string }>
  errors: string[]
}

// ─── Settings ──────────────────────────────────────────────────────────────────

export interface GlobalSetting {
  id: string
  name: string
  description: string
}

export interface SettingsGetResponse {
  settings: GlobalSetting[]
  saved_selections: string[]
  saved_dp_margin: string
  saved_shutoff_margin: string
}

export interface ApplyGlobalSettingsRequest {
  setting_ids: string[]
  dp_margin: number
  shutoff_margin: number
}

export interface CenterLayoutResponse {
  message: string
}

export interface SnapOrthogonalRequest {
  threshold_deg: number
  grid_size: number
}

export interface SettingsApplyResponse {
  results: Record<string, string[]>
  errors: string[]
  message: string
}

// ─── Bulk Copy ────────────────────────────────────────────────────────────────

export interface BulkCopyRequest {
  ref_pipe: string
  target_pipes: string
  exclude: boolean
}

export interface BulkCopyResponse {
  success: boolean
  updated_pipes: string[]
  updated_count: number
  error: string | null
}

// ─── Report ───────────────────────────────────────────────────────────────────

export interface GenerateReportRequest {
  report_path?: string | null
}

export interface ExportRequest {
  file_path?: string | null
}

export interface ImportRequest {
  file_path?: string | null
}

export interface BatchReportRequest {
  batch_folder?: string | null
}

export interface ReportResponse {
  success: boolean
  messages: Array<{ type: string; message: string }>
  errors: string[]
}

// ─── Pipe Criteria ────────────────────────────────────────────────────────────

export interface PipeCriteriaEntry {
  state: string
  criteria: string
}

export interface SetPipeCriteriaRequest {
  criteria: Record<string, PipeCriteriaEntry>
}

export interface PredictCriteriaResponse {
  predicted: Record<string, PipeCriteriaEntry>
  filled_state: number
  filled_criteria: number
  errors: string[]
}

export interface CriteriaValuesInfo {
  max_dp: number | null
  max_vel: number | null
  min_vel: number
  rho_v2_min: number | null
  rho_v2_max: number | null
}

export interface PipeCalcInfo {
  dp_calc: number | null
  vel_calc: number | null
  rho_v2_calc: number | null
}

export interface PipeCriteriaResponse {
  kdf_path: string
  pipes: Array<[number, string]>
  existing: Record<string, Record<string, string>>
  codes: Record<string, string[][]>
  fluid_labels: Record<string, string>
  pipe_criteria_values: Record<string, Record<string, Record<string, unknown>>>
  pipe_calcs: Record<string, Record<string, unknown>>
  units_data: Record<string, unknown>
  set_result: Record<string, unknown> | null
  predict_result: Record<string, unknown> | null
}

export interface SetCriteriaResponse {
  applied: number
  skipped: string[]
}

// ─── References ──────────────────────────────────────────────────────────────

export interface Reference {
  id: string
  name: string
  link: string
  description: string
  category: string
}

export interface ReferencesStore {
  basis: string
  remarks: string
  hold: string
  references: Reference[]
}

export interface SaveAllReferencesRequest {
  basis: string
  remarks: string
  hold: string
}

export interface AddReferenceRequest {
  edit_id: string
  name: string
  link: string
  description: string
  category: string
}

export interface UpdateReferenceRequest {
  ref_id: string
  name: string
  link: string
  description: string
  category: string
}

export interface DeleteReferenceRequest {
  ref_id: string
}

export interface ShortcutsResponse {
  count: number
  path: string
  error: string | null
}

// ─── Preferences ─────────────────────────────────────────────────────────────

export interface PreferencesResponse {
  sp_overrides: Record<string, string>
  skip_sp_override: boolean
  license_key: string | null
  doc_register_excel_path: string | null
  doc_register_sp_site_url: string | null
  doc_register_db_last_imported: string | null
  sp_overrides_configured: boolean
  default_doc_register_url: string
}

export interface AddSpOverrideRequest {
  local_path: string
  sp_url: string
}

export interface EditSpOverrideRequest {
  original_local_path: string
  local_path: string
  sp_url: string
}

export interface DeleteSpOverrideRequest {
  local_path: string
}

export interface SetSkipSpRequest {
  skip: boolean
}

export interface SetLicenseKeyRequest {
  license_key: string
}

export interface SetDocRegisterConfigRequest {
  excel_path?: string | null
  sp_site_url?: string | null
}

export interface LicenseValidationResponse {
  valid: boolean
  expiry: string | null
  error: string
}

export interface DocRegisterRebuildResponse {
  success: boolean
  message: string
  stats: Record<string, unknown>
  error: string | null
}

// ─── Browse ──────────────────────────────────────────────────────────────────

export interface BrowseEntryDir {
  name: string
  path: string
  synced: boolean
}

export interface BrowseEntryFile {
  name: string
  path: string
  sharepoint_url: string | null
}

export interface BrowseResponse {
  current: string
  current_sp_url: string | null
  parent: string | null
  drives: string[]
  pinned_folders: string[]
  dirs: BrowseEntryDir[]
  files: BrowseEntryFile[]
}

// ─── Doc Register ────────────────────────────────────────────────────────────

export interface DocRegisterStatusResponse {
  excel_path: string | null
  sp_site_url: string | null
  db_exists: boolean
  is_stale: boolean
  db_stats: Record<string, unknown>
}

export interface EddrResult {
  document_no: string
  title: string
}

export interface QueryEntryResult {
  name: string
  modified: string | null
  modified_by: string | null
  path: string | null
  item_type: string | null
}

// ─── About ───────────────────────────────────────────────────────────────────

export interface AboutResponse {
  version: string
  release_date: string
}
