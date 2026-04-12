import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'
import type {
  PreferencesResponse,
  AddSpOverrideRequest,
  EditSpOverrideRequest,
  DeleteSpOverrideRequest,
  SetSkipSpRequest,
  SetLicenseKeyRequest,
  SetDocRegisterConfigRequest,
  LicenseValidationResponse,
  DocRegisterRebuildResponse,
} from '../types/api'

export const usePreferencesStore = defineStore('preferences', () => {
  const spOverrides = ref<Record<string, string>>({})
  const skipSpOverride = ref(false)
  const licenseKey = ref<string | null>(null)
  const docRegisterExcelPath = ref<string | null>(null)
  const docRegisterSpSiteUrl = ref<string | null>(null)
  const docRegisterDbLastImported = ref<string | null>(null)
  const spOverridesConfigured = ref(false)
  const defaultDocRegisterUrl = ref('')

  function _apply(data: PreferencesResponse) {
    spOverrides.value = data.sp_overrides
    skipSpOverride.value = data.skip_sp_override
    licenseKey.value = data.license_key
    docRegisterExcelPath.value = data.doc_register_excel_path
    docRegisterSpSiteUrl.value = data.doc_register_sp_site_url
    docRegisterDbLastImported.value = data.doc_register_db_last_imported
    spOverridesConfigured.value = data.sp_overrides_configured
    defaultDocRegisterUrl.value = data.default_doc_register_url
  }

  async function fetchAll() {
    try {
      const { data } = await api.get<PreferencesResponse>('/api/preferences/')
      _apply(data)
    } catch {
      // ignore
    }
  }

  async function addOverride(localPath: string, spUrl: string) {
    const req: AddSpOverrideRequest = { local_path: localPath, sp_url: spUrl }
    const { data } = await api.post<{ success: boolean }>('/api/preferences/sp-overrides/add', req)
    if (data.success) await fetchAll()
    return data
  }

  async function editOverride(originalPath: string, localPath: string, spUrl: string) {
    const req: EditSpOverrideRequest = { original_local_path: originalPath, local_path: localPath, sp_url: spUrl }
    const { data } = await api.post<{ success: boolean }>('/api/preferences/sp-overrides/edit', req)
    if (data.success) await fetchAll()
    return data
  }

  async function deleteOverride(localPath: string) {
    const req: DeleteSpOverrideRequest = { local_path: localPath }
    const { data } = await api.post<{ success: boolean }>('/api/preferences/sp-overrides/delete', req)
    if (data.success) await fetchAll()
    return data
  }

  async function setSkipSp(skip: boolean) {
    const req: SetSkipSpRequest = { skip }
    await api.post('/api/preferences/skip-sp', req)
    skipSpOverride.value = skip
  }

  async function setLicenseKey(key: string) {
    const req: SetLicenseKeyRequest = { license_key: key }
    const { data } = await api.post<LicenseValidationResponse>('/api/preferences/license', req)
    return data
  }

  async function setDocRegisterConfig(req: SetDocRegisterConfigRequest) {
    const { data } = await api.post<DocRegisterRebuildResponse>('/api/preferences/doc-register', req)
    return data
  }

  async function rebuildDocRegisterDb(): Promise<DocRegisterRebuildResponse> {
    const { data } = await api.post<DocRegisterRebuildResponse>('/api/doc-register/rebuild-db')
    return data
  }

  return {
    spOverrides,
    skipSpOverride,
    licenseKey,
    docRegisterExcelPath,
    docRegisterSpSiteUrl,
    docRegisterDbLastImported,
    spOverridesConfigured,
    defaultDocRegisterUrl,
    fetchAll,
    addOverride,
    editOverride,
    deleteOverride,
    setSkipSp,
    setLicenseKey,
    setDocRegisterConfig,
    rebuildDocRegisterDb,
  }
})
