import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getSessionStatus as apiGetSessionStatus,
  openFile as apiOpenFile,
  reloadModel as apiReloadModel,
  closeModel as apiCloseModel,
} from '../api/generated/sdk.gen'
import type {
  SessionOpenRequest,
  SessionStatusResponse,
} from '../api/generated/types.gen'

/**
 * Session store — mirrors the in-process model state held by FastAPI.
 *
 * KEY NUANCES:
 * 1. After every save/reload POST, call fetchStatus() to resync
 *    kdf_mtime (the backend re-parses the KDF from disk on reload).
 * 2. The backend auto-detects stale KDF (modified by KORF GUI) on
 *    every require_model() call. If stale, it reloads + sets
 *    X-Model-Stale: true header. The axios interceptor checks this.
 * 3. 409 status = no model loaded → redirect to file picker.
 * 4. PMS auto-apply happens server-side on GET /api/model/summary
 *    if the PMS Excel is newer than last import. Frontend doesn't
 *    need to trigger it explicitly.
 */
export const useSessionStore = defineStore('session', () => {
  const modelLoaded = ref(false)
  const kdfPath = ref<string | null>(null)
  const kdfMtime = ref<string | null>(null)
  const recentFiles = ref<string[]>([])
  const setupOk = ref(false)
  const spOk = ref(false)
  const docRegisterOk = ref(false)
  const skipSpOverride = ref(false)
  const username = ref('')
  const updateAvailable = ref(false)
  const version = ref('')
  /** Set when backend auto-reloaded due to external KDF change */
  const modelWasStale = ref(false)

  const isLoaded = computed(() => modelLoaded.value)
  const filename = computed(() => {
    if (!kdfPath.value) return ''
    const parts = kdfPath.value.split(/[\/\\]/)
    return parts[parts.length - 1] || ''
  })

  function _applyStatus(data: SessionStatusResponse) {
    modelLoaded.value = data.model_loaded ?? false
    kdfPath.value = data.kdf_path ?? null
    kdfMtime.value = data.kdf_mtime ?? null
    recentFiles.value = data.recent_files ?? []
    setupOk.value = data.setup_ok ?? false
    spOk.value = data.sp_ok ?? false
    docRegisterOk.value = data.doc_register_ok ?? false
    skipSpOverride.value = data.skip_sp_override ?? false
    username.value = data.username ?? ''
    updateAvailable.value = data.update_available ?? false
    version.value = data.version ?? ''
  }

  async function fetchStatus() {
    try {
      const response = await apiGetSessionStatus()
      if (!response.data) return
      _applyStatus(response.data)
    } catch {
      modelLoaded.value = false
    }
  }

  async function openFile(path: string) {
    const req: SessionOpenRequest = { kdf_path: path }
    const response = await apiOpenFile({ body: req })
    if (response.data) {
      _applyStatus(response.data)
    }
  }

  async function reloadModel() {
    await apiReloadModel({ body: {} })
    await fetchStatus()
  }

  async function closeModel() {
    await apiCloseModel({ body: {} })
    await fetchStatus()
  }

  return {
    modelLoaded,
    kdfPath,
    kdfMtime,
    recentFiles,
    setupOk,
    spOk,
    docRegisterOk,
    skipSpOverride,
    username,
    updateAvailable,
    version,
    modelWasStale,
    isLoaded,
    filename,
    fetchStatus,
    openFile,
    reloadModel,
    closeModel,
  }
})
