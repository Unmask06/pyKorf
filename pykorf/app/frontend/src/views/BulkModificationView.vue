<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '../stores/session'
import { useModelStore } from '../stores/model'
import { useToastStore } from '../composables/useToast'
import { useLoading } from '../composables/useLoading'
import { api, getErrorMessage } from '../api/client'
import { Sliders, Move, Terminal, XCircle, Magnet, CheckCircle, Grid3X3, FolderOpen, Upload, FileSpreadsheet } from 'lucide-vue-next'
import PathBrowser from '../components/PathBrowser.vue'
import type {
  ApplyDataResponse,
  ApplyGlobalSettingsRequest,
  ApplyHmbRequest,
  ApplyPmsRequest,
  CenterLayoutResponse,
  EmptyRequest,
  GlobalSetting,
  OkResponse,
  PreferencesResponse,
  SettingsApplyResponse,
  SettingsGetResponse,
  SnapOrthogonalRequest,
} from '../types/api'

const router = useRouter()
const session = useSessionStore()
const model = useModelStore()
const toast = useToastStore()

const settings = ref<GlobalSetting[]>([])
const selectedIds = ref<string[]>([])
const dpMargin = ref(0)
const shutoffMargin = ref(0)
const pumpElevation = ref(0)
const applyResults = ref<SettingsApplyResponse | ApplyDataResponse | null>(null)

const thresholdDeg = ref(10.0)
const gridSize = ref(500.0)

// PMS / HMB state
const pmsSource = ref('')
const hmbSource = ref('')
const showPmsBrowser = ref(false)
const showHmbBrowser = ref(false)

const pmsLoading = useLoading(async () => {
  const req: ApplyPmsRequest = {
    pms_source: pmsSource.value,
  }
  const { data } = await api.post<ApplyDataResponse>('/api/data/apply-pms', req)
  await session.fetchStatus()
  await model.fetchSummary()
  return data
})

const hmbLoading = useLoading(async () => {
  const req: ApplyHmbRequest = {
    hmb_source: hmbSource.value,
  }
  const { data } = await api.post<ApplyDataResponse>('/api/data/apply-hmb', req)
  await session.fetchStatus()
  await model.fetchSummary()
  return data
})

async function applyPms() {
  if (!pmsSource.value.trim()) {
    toast.error('Please enter a PMS source file path.')
    return
  }
  try {
    applyResults.value = null
    const result = await pmsLoading.execute()
    if (result) applyResults.value = result
    if (result?.errors?.length) {
      toast.error('PMS application had errors — see Results below.')
    } else {
      toast.success('PMS data applied successfully.')
    }
  } catch (err: unknown) {
    toast.error(getErrorMessage(err, 'Failed to apply PMS.'))
  }
}

async function applyHmb() {
  if (!hmbSource.value.trim()) {
    toast.error('Please enter an HMB source file path.')
    return
  }
  try {
    applyResults.value = null
    const result = await hmbLoading.execute()
    if (result) applyResults.value = result
    if (result?.errors?.length) {
      toast.error('HMB application had errors — see Results below.')
    } else {
      toast.success('HMB data applied successfully.')
    }
  } catch (err: unknown) {
    toast.error(getErrorMessage(err, 'Failed to apply HMB.'))
  }
}

const allSelected = computed(() =>
  settings.value.length > 0 && selectedIds.value.length === settings.value.length
)

const dpMarginPct = computed(() => Math.round((dpMargin.value - 1) * 100))
const shutoffMarginPct = computed(() => Math.round((shutoffMargin.value - 1) * 100))

async function fetchSettings() {
  try {
    const { data } = await api.get<SettingsGetResponse>('/api/settings/')
    settings.value = data.settings
    selectedIds.value = data.saved_selections
    dpMargin.value = parseFloat(data.saved_dp_margin)
    shutoffMargin.value = parseFloat(data.saved_shutoff_margin)
    pumpElevation.value = parseFloat(data.saved_min_pump_elev)
  } catch (err: unknown) {
    toast.error(getErrorMessage(err, 'Failed to load settings.'))
  }
}

const applyLoading = useLoading(async () => {
  const req: ApplyGlobalSettingsRequest = {
    setting_ids: selectedIds.value,
    dp_margin: dpMargin.value,
    shutoff_margin: shutoffMargin.value,
    min_pump_elevation: pumpElevation.value,
  }
  const { data } = await api.post<SettingsApplyResponse>('/api/settings/apply', req)
  applyResults.value = data
  await session.fetchStatus()
  await model.fetchSummary()
  return data
})

const centerLoading = useLoading(async () => {
  const req: EmptyRequest = {}
  const { data } = await api.post<CenterLayoutResponse>('/api/settings/center-layout', req)
  await session.fetchStatus()
  toast.success(data.message)
})

const snapLoading = useLoading(async () => {
  const req: SnapOrthogonalRequest = {
    threshold_deg: thresholdDeg.value,
    grid_size: gridSize.value,
  }
  const { data } = await api.post<CenterLayoutResponse>('/api/settings/snap-orthogonal', req)
  await session.fetchStatus()
  toast.success(data.message)
})

async function apply_global_params() {
  if (!selectedIds.value.length) {
    toast.error('Select at least one setting to apply.')
    return
  }
  try {
    applyResults.value = null
    const result = await applyLoading.execute()
    if (result) applyResults.value = result
    if (result?.errors?.length) toast.error('Some settings had errors — see below.')
    else toast.success(result?.message || 'Settings applied.')
  } catch (err: unknown) {
    toast.error(getErrorMessage(err, 'Failed to apply settings.'))
  }
}

async function center() {
  try {
    await centerLoading.execute()
  } catch (err: unknown) {
    toast.error(getErrorMessage(err, 'Failed to center layout.'))
  }
}

async function snap() {
  try {
    await snapLoading.execute()
  } catch (err: unknown) {
    toast.error(getErrorMessage(err, 'Failed to snap orthogonal.'))
  }
}

function toggleAll() {
  if (allSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = settings.value.map(s => s.id)
  }
}

function resultLines(result: SettingsApplyResponse | ApplyDataResponse | null): Array<{ level: string; msg: string }> {
  if (!result) return []
  const lines: Array<{ level: string; msg: string }> = []
  
  // Handle SettingsApplyResponse format
  if ('results' in result) {
    if (result.errors) {
      for (const e of result.errors) lines.push({ level: 'error', msg: e })
    }
    if (result.results) {
      for (const [key, msgs] of Object.entries(result.results)) {
        for (const m of msgs) lines.push({ level: 'success', msg: `${key}: ${m}` })
      }
    }
  }
  // Handle ApplyDataResponse format
  else if ('messages' in result) {
    if (result.messages) {
      for (const m of result.messages) {
        lines.push({ level: m.type === 'success' ? 'success' : 'info', msg: m.message })
      }
    }
    if (result.errors) {
      for (const e of result.errors) lines.push({ level: 'error', msg: e })
    }
  }
  return lines
}

// Resolve SharePoint URL to local path
async function resolvePmsSpUrl() {
  const url = pmsSource.value.trim()
  if (!url.startsWith('https://')) return

  try {
    const { data } = await api.post<OkResponse>('/api/sharepoint/resolve-url', { sp_url: url })
    if (data.success && data.message) {
      pmsSource.value = data.message
      toast.success('Converted to local path.')
    } else {
      toast.error(data.error || 'Could not resolve SharePoint URL.')
    }
  } catch (err: unknown) {
    toast.error(getErrorMessage(err, 'Failed to resolve SharePoint URL.'))
  }
}

onMounted(async () => {
  if (!session.isLoaded) router.push('/')
  fetchSettings()
  if (model.prereqs?.pms_path) {
    pmsSource.value = model.prereqs.pms_path
  } else {
    try {
      const { data } = await api.get<PreferencesResponse>('/api/preferences/')
      // default_pms_url already resolves: saved path → factory default on the backend
      if (data.default_pms_url) {
        pmsSource.value = data.default_pms_url
      }
    } catch {
      // ignore — prefill is best-effort
    }
  }
})
</script>

<template>
  <div class="space-y-4">

    <!-- ── Top row: data operations + results ────────────────── -->
    <div class="flex gap-4 flex-wrap lg:flex-nowrap">

      <div class="flex-1 space-y-4">

        <!-- Layout Operations -->
        <div class="pk-card border-blue-500 border-2">
          <div class="px-4 py-2 bg-blue-600 text-white font-semibold flex items-center gap-2 rounded-t">
            <Grid3X3 class="w-4 h-4" /> Layout Operations
          </div>
          <div class="p-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <button @click="center()"
                  class="w-full border border-blue-500 text-blue-600 rounded py-1.5 text-sm hover:bg-blue-50 flex items-center justify-center gap-2"
                  :disabled="centerLoading.isLoading.value">
                  <Move class="w-4 h-4" /> Center Layout
                </button>
                <div class="pk-hint mt-1">Center all elements on the page</div>
              </div>
              <div>
                <button @click="snap()"
                  class="w-full border border-blue-500 text-blue-600 rounded py-1.5 text-sm hover:bg-blue-50 flex items-center justify-center gap-2"
                  :disabled="true" style="pointer-events: none; opacity: 0.5; cursor: not-allowed;">
                  <Magnet class="w-4 h-4" /> Snap Orthogonal
                </button>
                <div class="pk-hint mt-1">Snap near-orthogonal connections and align to grid.</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Apply PMS / HMB Data -->
        <div class="pk-card border-cyan-500 border-2">
          <div class="px-4 py-2 bg-cyan-600 text-white font-semibold flex items-center gap-2 rounded-t">
            <Upload class="w-4 h-4" /> Apply PMS / HMB Data
          </div>
          <div class="p-4">
            <!-- PMS -->
            <div class="mb-4 p-4 rounded-lg bg-gray-50">
              <div class="mb-3">
                <label class="pk-label">PMS Excel File</label>
                <div class="flex">
                  <span class="flex items-center justify-center px-3 py-1.5 text-sm bg-gray-100 border border-r-0 border-gray-300 rounded-l-md">
                    <FileSpreadsheet class="w-4 h-4 text-gray-500" />
                  </span>
                  <textarea v-model="pmsSource" class="pk-input-mono resize-none rounded-none"
                    rows="2" placeholder="C:/config/pms_data.xlsx"
                    @click="resolvePmsSpUrl" />
                  <button type="button" @click="showPmsBrowser = true"
                    class="flex items-center justify-center px-3 py-1.5 text-sm border border-l-0 border-gray-300 rounded-r-md bg-gray-100 hover:bg-gray-200"
                    title="Browse for PMS Excel file">
                    <FolderOpen class="w-4 h-4" />
                  </button>
                </div>
                <div class="pk-hint">Path to the PMS Excel file. Supports local paths or SharePoint URLs (auto-converted using configured overrides).</div>
              </div>
              <button @click="applyPms" class="pk-btn-primary" :disabled="pmsLoading.isLoading.value">
                <span v-if="pmsLoading.isLoading.value" class="pk-spinner" />
                Apply PMS
              </button>
            </div>
            <!-- HMB -->
            <div class="p-4 rounded-lg bg-gray-50">
              <div class="mb-3">
                <label class="pk-label">HMB Excel File</label>
                <div class="flex">
                  <span class="flex items-center justify-center px-3 py-1.5 text-sm bg-gray-100 border border-r-0 border-gray-300 rounded-l-md">
                    <FileSpreadsheet class="w-4 h-4 text-gray-500" />
                  </span>
                  <textarea v-model="hmbSource" class="pk-input-mono resize-none rounded-none"
                    rows="2" placeholder="C:/config/stream_data.xlsx" />
                  <button type="button" @click="showHmbBrowser = true"
                    class="flex items-center justify-center px-3 py-1.5 text-sm border border-l-0 border-gray-300 rounded-r-md bg-gray-100 hover:bg-gray-200"
                    title="Browse for HMB Excel file">
                    <FolderOpen class="w-4 h-4" />
                  </button>
                </div>
                <div class="pk-hint">Path to the HMB/Stream Excel file.</div>
              </div>
              <button @click="applyHmb" class="pk-btn-primary" :disabled="hmbLoading.isLoading.value">
                <span v-if="hmbLoading.isLoading.value" class="pk-spinner" />
                Apply HMB
              </button>
            </div>
          </div>
        </div>

      </div>

      <!-- Results sidebar -->
      <div class="w-full lg:w-80">
        <div v-if="applyResults" class="pk-card">
          <div class="pk-card-header flex items-center gap-1">
            <Terminal class="w-4 h-4" /> Results
          </div>
          <div class="p-3 font-mono text-xs overflow-auto" style="max-height: 320px;">
            <template v-for="line in resultLines(applyResults)" :key="line.msg">
              <div :class="{
                'text-green-600': line.level === 'success',
                'text-red-600': line.level === 'error',
                'text-gray-500': line.level === 'info',
              }">
                <span v-if="line.level === 'success'">✓</span>
                <span v-else-if="line.level === 'error'">✗</span>
                <span v-else>›</span>
                {{ line.msg }}
              </div>
            </template>
          </div>
        </div>
      </div>

    </div>

    <!-- ── Bottom: Global Parameters — full width, 3-col grid ── -->
    <div class="pk-card border-gray-500 border-2">
      <div class="px-4 py-2 bg-gray-600 text-white font-semibold flex items-center gap-2 rounded-t">
        <Sliders class="w-4 h-4" /> Global Parameters
      </div>
      <div class="p-4">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-2 mb-4">
          <div v-for="s in settings" :key="s.id"
            class="flex items-start gap-3 px-3 py-2 rounded border cursor-pointer select-none transition-colors"
            :class="selectedIds.includes(s.id) ? 'border-blue-400 bg-blue-50' : 'border-gray-200 hover:border-gray-400'"
            @click="selectedIds.includes(s.id) ? selectedIds = selectedIds.filter(id => id !== s.id) : selectedIds.push(s.id)">
            <input type="checkbox" :checked="selectedIds.includes(s.id)"
              class="form-check-input mt-0.5 shrink-0"
              @click.stop
              @change="selectedIds.includes(s.id) ? selectedIds = selectedIds.filter(id => id !== s.id) : selectedIds.push(s.id)" />
            <div class="min-w-0 flex-1">
              <div class="text-sm font-medium leading-tight">{{ s.name }}</div>
              <div class="text-xs text-gray-400 mt-0.5 leading-snug">{{ s.description }}</div>

              <!-- dp_margin sub-form -->
              <div v-if="s.id === 'dp_margin'" class="mt-2 flex items-center gap-1" @click.stop>
                <input v-model.number="dpMargin" type="number" step="0.01" min="1.0" max="3.0"
                  class="pk-input text-xs w-20 rounded-none" />
                <span class="text-xs text-gray-500">{{ dpMarginPct }}% margin</span>
              </div>

              <!-- pump_shutoff sub-form -->
              <div v-if="s.id === 'pump_shutoff'" class="mt-2 flex items-center gap-1" @click.stop>
                <input v-model.number="shutoffMargin" type="number" step="0.01" min="1.0" max="3.0"
                  class="pk-input text-xs w-20 rounded-none" />
                <span class="text-xs text-gray-500">{{ shutoffMarginPct }}% margin</span>
              </div>

              <!-- min_pump_elevation sub-form -->
              <div v-if="s.id === 'min_pump_elevation'" class="mt-2 flex items-center gap-1" @click.stop>
                <input v-model.number="pumpElevation" type="number" step="0.1" min="0.0"
                  class="pk-input text-xs w-20 rounded-none" />
                <span class="text-xs text-gray-500">m</span>
              </div>
            </div>
          </div>
        </div>

        <div class="flex gap-2">
          <button type="button" @click="toggleAll" class="pk-btn-secondary">
            <CheckCircle class="w-4 h-4" /> {{ allSelected ? 'Deselect All' : 'Select All' }}
          </button>
          <button type="button" @click="selectedIds = []" class="pk-btn-secondary">
            <XCircle class="w-4 h-4" /> Clear All
          </button>
          <button @click="apply_global_params" class="pk-btn-primary ml-auto" :disabled="applyLoading.isLoading.value">
            <span v-if="applyLoading.isLoading.value" class="pk-spinner" />
            Apply Selected
          </button>
        </div>
      </div>
    </div>

  </div>

  <PathBrowser v-if="showPmsBrowser" filter="excel"
    @close="showPmsBrowser = false"
    @select="(p: string) => { pmsSource = p; showPmsBrowser = false }" />
  <PathBrowser v-if="showHmbBrowser" filter="excel"
    @close="showHmbBrowser = false"
    @select="(p: string) => { hmbSource = p; showHmbBrowser = false }" />
</template>

<style scoped>
/* Setting cards */
.setting-card {
  border: 2px solid #dee2e6;
  border-radius: 0.375rem;
  transition: border-color 0.15s ease;
}
.setting-card:hover {
  border-color: #3b82f6;
}
.setting-card-selected {
  border-color: #3b82f6;
}
.setting-card-unselected {
  border-color: #dee2e6;
}
/* Form toggle switch */
.form-check-input {
  width: 2em;
  height: 1em;
  border-radius: 1em;
  appearance: none;
  background: #adb5bd;
  cursor: pointer;
  position: relative;
  transition: background 0.15s;
  flex-shrink: 0;
}
.form-check-input:checked {
  background: #3b82f6;
}
.form-check-input::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: calc(1em - 4px);
  height: calc(1em - 4px);
  border-radius: 50%;
  background: white;
  transition: transform 0.15s;
}
.form-check-input:checked::after {
  transform: translateX(1em);
}
</style>
