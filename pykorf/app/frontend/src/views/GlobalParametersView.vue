<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '../stores/session'
import { useModelStore } from '../stores/model'
import { useToastStore } from '../composables/useToast'
import { useLoading } from '../composables/useLoading'
import { api } from '../api/client'
import { Sliders, Move, Lightbulb, Terminal, XCircle, Magnet, CheckCircle, Grid3X3 } from 'lucide-vue-next'
import type { GlobalSetting, SettingsApplyResponse, SettingsGetResponse, CenterLayoutResponse } from '../types/api'

const router = useRouter()
const session = useSessionStore()
const model = useModelStore()
const toast = useToastStore()

const settings = ref<GlobalSetting[]>([])
const selectedIds = ref<string[]>([])
const dpMargin = ref(1.25)
const shutoffMargin = ref(1.20)
const applyResults = ref<SettingsApplyResponse | null>(null)

const thresholdDeg = ref(10.0)
const gridSize = ref(500.0)

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
    dpMargin.value = parseFloat(data.saved_dp_margin) || 1.25
    shutoffMargin.value = parseFloat(data.saved_shutoff_margin) || 1.20
  } catch (err: any) {
    toast.error(err.response?.data?.detail || err.message || 'Failed to load settings.')
  }
}

const applyLoading = useLoading(async () => {
  const { data } = await api.post<SettingsApplyResponse>('/api/settings/apply', {
    setting_ids: selectedIds.value,
    dp_margin: dpMargin.value,
    shutoff_margin: shutoffMargin.value,
  })
  applyResults.value = data
  await session.fetchStatus()
  await model.fetchSummary()
  return data
})

const centerLoading = useLoading(async () => {
  const { data } = await api.post<CenterLayoutResponse>('/api/settings/center-layout')
  await session.fetchStatus()
  toast.success(data.message)
})

const snapLoading = useLoading(async () => {
  const { data } = await api.post<CenterLayoutResponse>('/api/settings/snap-orthogonal', {
    threshold_deg: thresholdDeg.value,
    grid_size: gridSize.value,
  })
  await session.fetchStatus()
  toast.success(data.message)
})

async function apply() {
  if (!selectedIds.value.length) {
    toast.error('Select at least one setting to apply.')
    return
  }
  try {
    const result = await applyLoading.execute()
    if (result?.errors?.length) toast.error('Some settings had errors — see below.')
    else toast.success(result?.message || 'Settings applied.')
  } catch (err: any) {
    toast.error(err.response?.data?.detail || err.message || 'Failed to apply settings.')
  }
}

async function center() {
  try {
    await centerLoading.execute()
  } catch (err: any) {
    toast.error(err.response?.data?.detail || err.message || 'Failed to center layout.')
  }
}

async function snap() {
  try {
    await snapLoading.execute()
  } catch (err: any) {
    toast.error(err.response?.data?.detail || err.message || 'Failed to snap orthogonal.')
  }
}

function toggleAll() {
  if (allSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = settings.value.map(s => s.id)
  }
}

function resultLines(result: SettingsApplyResponse | null): Array<{ level: string; msg: string }> {
  if (!result) return []
  const lines: Array<{ level: string; msg: string }> = []
  if (result.errors) {
    for (const e of result.errors) lines.push({ level: 'error', msg: e })
  }
  if (result.results) {
    for (const [key, msgs] of Object.entries(result.results)) {
      for (const m of msgs) lines.push({ level: 'success', msg: `${key}: ${m}` })
    }
  }
  return lines
}

onMounted(() => {
  if (!session.isLoaded) router.push('/')
  fetchSettings()
})
</script>

<template>
  <div class="flex gap-4 flex-wrap lg:flex-nowrap">

    <!-- ── Left: Settings form ────────────────────────────────── -->
    <div class="w-full lg:w-2/3">
      <div class="pk-card">
        <div class="pk-card-header flex items-center gap-2">
          <Sliders class="w-4 h-4 text-yellow-500" /> Global Parameters
          <span class="ml-auto bg-gray-200 text-gray-600 text-xs px-2 py-0.5 rounded">Bulk model modifications</span>
        </div>
        <div class="pk-card-body">

          <!-- Layout Operations Section -->
          <div class="pk-card mb-4 border-blue-500 border-2">
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
                    :disabled="snapLoading.isLoading.value">
                    <Magnet class="w-4 h-4" /> Snap Orthogonal
                  </button>
                  <div class="pk-hint mt-1">Snap near-orthogonal connections and align to grid.</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Settings grid -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
            <div v-for="s in settings" :key="s.id" class="setting-card"
              :class="selectedIds.includes(s.id) ? 'setting-card-selected' : 'setting-card-unselected'">
              <div class="p-3">
                <div class="flex items-center gap-2 mb-1">
                  <input type="checkbox" :checked="selectedIds.includes(s.id)"
                    @change="selectedIds.includes(s.id) ? selectedIds = selectedIds.filter(id => id !== s.id) : selectedIds.push(s.id)"
                    class="form-check-input" />
                  <label class="font-semibold text-sm cursor-pointer"
                    @click="selectedIds.includes(s.id) ? selectedIds = selectedIds.filter(id => id !== s.id) : selectedIds.push(s.id)">
                    {{ s.name }}
                  </label>
                </div>
                <p class="text-xs text-gray-500 mt-1 mb-0">{{ s.description }}</p>

                <!-- dp_margin sub-form -->
                <div v-if="s.id === 'dp_margin'" class="mt-2">
                  <label class="text-xs font-semibold mb-1 block">Pressure Drop Margin</label>
                  <div class="flex">
                    <input v-model.number="dpMargin" type="number" step="0.01" min="1.0" max="3.0"
                      class="pk-input text-sm rounded-none" placeholder="1.25" />
                    <span class="flex items-center justify-center px-2 py-1 text-xs bg-gray-100 border border-l-0 border-gray-300 rounded-r-md">
                      {{ dpMarginPct }}% margin
                    </span>
                  </div>
                </div>

                <!-- pump_shutoff sub-form -->
                <div v-if="s.id === 'pump_shutoff'" class="mt-2">
                  <label class="text-xs font-semibold mb-1 block">Raise-Shutoff Margin</label>
                  <div class="flex">
                    <input v-model.number="shutoffMargin" type="number" step="0.01" min="1.0" max="3.0"
                      class="pk-input text-sm rounded-none" placeholder="1.20" />
                    <span class="flex items-center justify-center px-2 py-1 text-xs bg-gray-100 border border-l-0 border-gray-300 rounded-r-md">
                      {{ shutoffMarginPct }}% margin
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Action buttons -->
          <div class="flex gap-2">
            <button type="button" @click="toggleAll" class="pk-btn-secondary">
              <CheckCircle class="w-4 h-4" /> {{ allSelected ? 'Deselect All' : 'Select All' }}
            </button>
            <button type="button" @click="selectedIds = []" class="pk-btn-secondary">
              <XCircle class="w-4 h-4" /> Clear All
            </button>
            <button @click="apply" class="pk-btn-primary ml-auto" :disabled="applyLoading.isLoading.value">
              <span v-if="applyLoading.isLoading.value" class="pk-spinner" />
              Apply Selected
            </button>
          </div>

        </div>
      </div>
    </div>

    <!-- ── Right sidebar ──────────────────────────────────────── -->
    <div class="w-full lg:w-1/3 space-y-3">

      <!-- Results card -->
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

      <!-- Tips card -->
      <div class="pk-card">
        <div class="pk-card-header flex items-center gap-1">
          <Lightbulb class="w-4 h-4" /> Tips
        </div>
        <div class="p-4 text-sm text-gray-500">
          <ul class="list-disc pl-4 space-y-1 mb-0">
            <li>Toggle each setting card on or off with the switch.</li>
            <li>Clicking <em>Apply Selected</em> applies changes and <strong>saves</strong> the model immediately.</li>
            <li>Use <em>Select All</em> to enable every setting at once.</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
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
