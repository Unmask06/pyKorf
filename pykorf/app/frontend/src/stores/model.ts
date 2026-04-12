import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'
import type {
  ModelFullResponse,
  ModelSummary,
  Prereqs,
  ProjectInfo,
  BulkCopyRequest,
  BulkCopyResponse,
  SaveProjectInfoRequest,
  SaveResponse,
  SetPipeCriteriaRequest,
  SetCriteriaResponse,
  PipeCriteriaEntry,
  PredictCriteriaResponse,
  PipeCriteriaResponse,
} from '../types/api'

/**
 * Model store — caches current model data for the active page.
 *
 * SESSION RELOAD CONTRACT:
 * After every mutation POST (save, project-info, bulk-copy, set-criteria,
 * apply-pms, apply-hmb, center-layout, snap-orthogonal), the backend
 * calls _sess.reload() which re-parses the KDF from disk. The frontend
 * must then call fetchSummary() to resync.
 *
 * The model object itself lives only in the FastAPI process memory.
 * We never serialize it — only derived data comes over the API.
 */
export const useModelStore = defineStore('model', () => {
  const kdfPath = ref('')
  const summary = ref<ModelSummary | null>(null)
  const prereqs = ref<Prereqs | null>(null)
  const projectInfo = ref<ProjectInfo | null>(null)
  const smartDefaults = ref<ProjectInfo | null>(null)
  const pipes = ref<string[]>([])

  async function _postReloadSession() {
    const session = (await import('./session')).useSessionStore()
    await session.fetchStatus()
  }

  async function fetchSummary() {
    try {
      const { data } = await api.get<ModelFullResponse>('/api/model/summary')
      kdfPath.value = data.kdf_path
      summary.value = data.summary
      prereqs.value = data.prereqs
      projectInfo.value = data.project_info
      smartDefaults.value = data.smart_defaults
    } catch {
      // 409 = no model loaded, router guard handles redirect
    }
  }

  async function fetchPipes() {
    try {
      const { data } = await api.get<{ pipes: string[] }>('/api/model/pipes')
      pipes.value = data.pipes
    } catch {
      pipes.value = []
    }
  }

  async function save(): Promise<SaveResponse> {
    const { data } = await api.post<SaveResponse>('/api/model/save')
    await _postReloadSession()
    await fetchSummary()
    return data
  }

  async function saveProjectInfo(info: SaveProjectInfoRequest): Promise<SaveResponse> {
    const { data } = await api.post<SaveResponse>('/api/model/project-info', info)
    await _postReloadSession()
    await fetchSummary()
    return data
  }

  async function bulkCopy(req: BulkCopyRequest): Promise<BulkCopyResponse> {
    const { data } = await api.post<BulkCopyResponse>('/api/model/bulk-copy', req)
    await _postReloadSession()
    await fetchSummary()
    return data
  }

  async function setPipeCriteria(criteria: Record<string, PipeCriteriaEntry>): Promise<SetCriteriaResponse> {
    const req: SetPipeCriteriaRequest = { criteria }
    const { data } = await api.post<SetCriteriaResponse>('/api/model/pipe-criteria', req)
    await _postReloadSession()
    return data
  }

  async function predictCriteria(): Promise<PredictCriteriaResponse> {
    const { data } = await api.post<PredictCriteriaResponse>('/api/model/pipe-criteria/predict')
    return data
  }

  async function fetchPipeCriteria(): Promise<PipeCriteriaResponse> {
    const { data } = await api.get<PipeCriteriaResponse>('/api/model/pipe-criteria')
    return data
  }

  return {
    kdfPath,
    summary,
    prereqs,
    projectInfo,
    smartDefaults,
    pipes,
    fetchSummary,
    fetchPipes,
    save,
    saveProjectInfo,
    bulkCopy,
    setPipeCriteria,
    predictCriteria,
    fetchPipeCriteria,
  }
})
