import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api/client'
import type { SessionStatusResponse } from '../types/api'

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
  /** Set when backend auto-reloaded due to external KDF change */
  const modelWasStale = ref(false)

  const isLoaded = computed(() => modelLoaded.value)
  const filename = computed(() => {
    if (!kdfPath.value) return ''
    const parts = kdfPath.value.split(/[\/\\]/)
    return parts[parts.length - 1] || ''
  })

  function _applyStatus(data: SessionStatusResponse) {
    modelLoaded.value = data.model_loaded
    kdfPath.value = data.kdf_path
    kdfMtime.value = data.kdf_mtime
    recentFiles.value = data.recent_files
    setupOk.value = data.setup_ok
    spOk.value = data.sp_ok
    docRegisterOk.value = data.doc_register_ok
    skipSpOverride.value = data.skip_sp_override
    username.value = data.username
    updateAvailable.value = data.update_available
  }

  async function fetchStatus() {
    try {
      const { data } = await api.get<SessionStatusResponse>('/api/session/status')
      _applyStatus(data)
    } catch {
      modelLoaded.value = false
    }
  }

  async function openFile(path: string) {
    const { data } = await api.post<SessionStatusResponse>('/api/session/open', { kdf_path: path })
    _applyStatus(data)
  }

  async function reloadModel() {
    await api.post('/api/session/reload')
    await fetchStatus()
  }

  async function closeModel() {
    await api.post('/api/session/close')
    modelLoaded.value = false
    kdfPath.value = null
    kdfMtime.value = null
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
    modelWasStale,
    isLoaded,
    filename,
    fetchStatus,
    openFile,
    reloadModel,
    closeModel,
  }
})
