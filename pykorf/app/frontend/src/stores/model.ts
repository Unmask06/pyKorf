import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getModelSummary as apiGetModelSummary,
  getPipes as apiGetPipes,
  saveModel as apiSaveModel,
  saveProjectInfo as apiSaveProjectInfo,
  bulkCopy as apiBulkCopy,
  setPipeCriteria as apiSetPipeCriteria,
  predictPipeCriteria as apiPredictPipeCriteria,
  getPipeCriteria as apiGetPipeCriteria,
} from '../api/generated/sdk.gen'
import type {
  ModelSummaryResponse,
  PrereqsResponse,
  ProjectInfoResponse,
  BulkCopyRequest,
  BulkCopyResponse,
  SaveProjectInfoRequest,
  SaveResponse,
  SetPipeCriteriaRequest,
  SetCriteriaResponse,
  PipeCriteriaEntry,
  PredictCriteriaResponse,
  PipeCriteriaResponse,
} from '../api/generated/types.gen'

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
  const summary = ref<ModelSummaryResponse | null>(null)
  const prereqs = ref<PrereqsResponse | null>(null)
  const projectInfo = ref<ProjectInfoResponse | null>(null)
  const smartDefaults = ref<ProjectInfoResponse | null>(null)
  const requiredFields = ref<string[]>([])
  const pipes = ref<string[]>([])

  async function _postReloadSession() {
    const session = (await import('./session')).useSessionStore()
    await session.fetchStatus()
  }

  async function fetchSummary() {
    try {
      const response = await apiGetModelSummary()
      if (!response.data) return
      summary.value = response.data.summary ?? null
      prereqs.value = response.data.prereqs ?? null
      projectInfo.value = response.data.project_info ?? null
      smartDefaults.value = response.data.smart_defaults ?? null
      requiredFields.value = response.data.required_fields ?? []
    } catch {
      // 409 = no model loaded, router guard handles redirect
    }
  }

  async function fetchPipes() {
    try {
      const response = await apiGetPipes()
      if (!response.data) {
        pipes.value = []
        return
      }
      pipes.value = response.data.pipes ?? []
    } catch {
      pipes.value = []
    }
  }

  async function save(): Promise<SaveResponse> {
    const response = await apiSaveModel({ body: {} })
    await _postReloadSession()
    await fetchSummary()
    return response.data!
  }

  async function saveProjectInfo(info: SaveProjectInfoRequest): Promise<SaveResponse> {
    const response = await apiSaveProjectInfo({ body: info })
    await _postReloadSession()
    await fetchSummary()
    return response.data!
  }

  async function bulkCopy(req: BulkCopyRequest): Promise<BulkCopyResponse> {
    const response = await apiBulkCopy({ body: req })
    await _postReloadSession()
    await fetchSummary()
    return response.data!
  }

  async function setPipeCriteria(criteria: Record<string, PipeCriteriaEntry>): Promise<SetCriteriaResponse> {
    const req: SetPipeCriteriaRequest = { criteria }
    const response = await apiSetPipeCriteria({ body: req })
    await _postReloadSession()
    await fetchSummary()
    return response.data!
  }

  async function predictCriteria(): Promise<PredictCriteriaResponse> {
    const response = await apiPredictPipeCriteria({ body: {} })
    return response.data!
  }

  async function fetchPipeCriteria(): Promise<PipeCriteriaResponse> {
    const response = await apiGetPipeCriteria()
    return response.data!
  }

  return {
    summary,
    prereqs,
    projectInfo,
    smartDefaults,
    requiredFields,
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
