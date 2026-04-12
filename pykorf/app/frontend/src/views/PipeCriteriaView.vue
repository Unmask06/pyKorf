<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '../stores/session'
import { useModelStore } from '../stores/model'
import { useToastStore } from '../composables/useToast'
import { useLoading } from '../composables/useLoading'
import { Ruler, ArrowLeft, Wand2, XCircle, Zap, CheckCircle, AlertTriangle } from 'lucide-vue-next'
import type { PipeCriteriaResponse, PipeCriteriaEntry, PredictCriteriaResponse } from '../types/api'

const router = useRouter()
const session = useSessionStore()
const model = useModelStore()
const toast = useToastStore()

// Criteria table data
const pipes = ref<Array<[number, string]>>([])
const existing = ref<Record<string, Record<string, string>>>({})
const codes = ref<Record<string, string[][]>>({})
const criteriaValues = ref<Record<string, Record<string, Record<string, unknown>>>>({})
const pipeCalcs = ref<Record<string, Record<string, unknown>>>({})
const unitsData = ref<Record<string, unknown>>({})
const fluidLabels = ref<Record<string, string>>({})

// Edited criteria entries
const editedCriteria = ref<Record<string, PipeCriteriaEntry>>({})
const dirtyPipes = ref<Set<string>>(new Set())
const predictResult = ref<PredictCriteriaResponse | null>(null)

// UI state
const pipeFilter = ref('')
const unitSystem = ref('Engg_SI')
const selectAllChecked = ref(false)
const selectedRows = ref<Set<string>>(new Set())
const bulkState = ref('')
const bulkCriteria = ref('')
const setResult = ref<Record<string, unknown> | null>(null)

// Computed unit labels based on selected unit system
const dpUnit = computed(() => {
  if (unitSystem.value === 'SI') return 'kPa/100m'
  const u = unitsData.value as any
  const conv = u?.['Engg_SI']?.['kPa/100m']
  return conv?.target_unit || 'bar/100m'
})

const velocityUnit = computed(() => 'm/s')
const rhoV2Unit = computed(() => 'Pa')

function _applyResponse(data: PipeCriteriaResponse) {
  pipes.value = data.pipes
  existing.value = data.existing
  codes.value = data.codes
  criteriaValues.value = data.pipe_criteria_values
  pipeCalcs.value = data.pipe_calcs
  unitsData.value = data.units_data
  fluidLabels.value = data.fluid_labels
  setResult.value = data.set_result
  predictResult.value = data.predict_result as PredictCriteriaResponse | null

  const initial: Record<string, PipeCriteriaEntry> = {}
  for (const [name, vals] of Object.entries(data.existing)) {
    initial[name] = { state: vals.state || '', criteria: vals.criteria || '' }
  }
  editedCriteria.value = initial
  dirtyPipes.value = new Set()
}

const criteriaLoading = useLoading(async () => {
  const data = await model.fetchPipeCriteria()
  _applyResponse(data)
})

const predictLoading = useLoading(async () => {
  const data = await model.predictCriteria()
  predictResult.value = data
  for (const [name, entry] of Object.entries(data.predicted)) {
    if (!editedCriteria.value[name]?.state || !editedCriteria.value[name]?.criteria) {
      editedCriteria.value[name] = { ...entry }
      dirtyPipes.value.add(name)
    }
  }
  toast.info(`Predicted: ${data.filled_state} states, ${data.filled_criteria} criteria codes filled.`)
})

const saveLoading = useLoading(async () => {
  const dirty: Record<string, PipeCriteriaEntry> = {}
  for (const name of dirtyPipes.value) {
    if (editedCriteria.value[name]) {
      dirty[name] = editedCriteria.value[name]
    }
  }
  if (Object.keys(dirty).length === 0) {
    toast.warning('No changes to save.')
    return
  }
  const result = await model.setPipeCriteria(dirty)
  await session.fetchStatus()
  toast.success(`Applied criteria to ${result.applied} pipe(s).`)
  if (result.skipped.length) {
    toast.warning(`Skipped: ${result.skipped.join(', ')}`)
  }
  await criteriaLoading.execute()
})

function updateEntry(name: string, field: 'state' | 'criteria', value: string) {
  if (!editedCriteria.value[name]) {
    editedCriteria.value[name] = { state: '', criteria: '' }
  }
  editedCriteria.value[name][field] = value
  dirtyPipes.value.add(name)
}

function getAvailableCriteriaForState(state: string): Array<[string, string]> {
  if (!state || !codes.value[state]) return []
  return codes.value[state].map((c: string[]) => [c[0], c[1]])
}

function convertValue(field: string, siValue: number | null): string {
  if (siValue === null || siValue === undefined) return '—'
  const u = unitsData.value as any
  // Map field name to the SI unit key used in units_data
  const unitKeyMap: Record<string, string> = {
    dp: 'kPa/100m',
    velocity: 'm/s',
    rho_v2: 'Pa',
  }
  const unitKey = unitKeyMap[field]
  if (!unitKey) return siValue.toFixed(2)

  // SI system: return as-is
  if (unitSystem.value === 'SI') return siValue.toFixed(2)

  // Engg_SI or other: look up conversion
  const systemConversions = u?.[unitSystem.value] || u?.['Engg_SI'] || {}
  const conv = systemConversions[unitKey]
  if (!conv) return siValue.toFixed(2)
  const factor = conv.multiplier ?? conv.factor ?? 1
  const offset = conv.offset ?? 0
  const converted = siValue * factor + offset
  return converted.toFixed(2)
}

const filteredPipes = computed(() => {
  if (!pipeFilter.value) return pipes.value
  const q = pipeFilter.value.toLowerCase()
  return pipes.value.filter(([, name]) => name.toLowerCase().includes(q))
})

function toggleSelectAll() {
  if (selectAllChecked.value) {
    selectedRows.value = new Set(filteredPipes.value.map(([, name]) => name))
  } else {
    selectedRows.value = new Set()
  }
}

function toggleRow(name: string) {
  if (selectedRows.value.has(name)) {
    selectedRows.value.delete(name)
  } else {
    selectedRows.value.add(name)
  }
}

// Auto-sync "Set rows" state dropdown based on selected rows
const selectedStates = computed(() => {
  const states = new Set<string>()
  for (const name of selectedRows.value) {
    const s = editedCriteria.value[name]?.state || ''
    if (s) states.add(s)
    else states.add('')
  }
  return states
})

// Watch selected rows' states and update bulkState if they share a common value
function syncBulkStateFromSelection() {
  const states = selectedStates.value
  if (states.size === 1) {
    bulkState.value = states.values().next().value as string
  } else {
    bulkState.value = ''
  }
}

watch(selectedRows, () => syncBulkStateFromSelection(), { deep: true })
watch(editedCriteria, () => syncBulkStateFromSelection(), { deep: true })

function applyBulkToVisible() {
  if (!bulkState.value && !bulkCriteria.value) {
    toast.warning('Select a state or criteria to apply.')
    return
  }
  for (const [, name] of filteredPipes.value) {
    if (bulkState.value) {
      updateEntry(name, 'state', bulkState.value)
    }
    if (bulkCriteria.value) {
      updateEntry(name, 'criteria', bulkCriteria.value)
    }
  }
  toast.info(`Applied to ${filteredPipes.value.length} visible pipe(s).`)
}

function clearAll() {
  for (const [, name] of pipes.value) {
    editedCriteria.value[name] = { state: '', criteria: '' }
    dirtyPipes.value.add(name)
  }
  toast.info('All criteria cleared.')
}

onMounted(() => {
  if (!session.isLoaded) router.push('/')
  criteriaLoading.execute()
})
</script>

<template>
  <div class="space-y-4">

    <!-- Set result alert -->
    <div v-if="setResult" class="flex items-start gap-2 p-3 rounded"
      :class="(setResult as any).skipped?.length ? 'bg-yellow-50 border border-yellow-200 text-yellow-700' : 'bg-green-50 border border-green-200 text-green-700'">
      <CheckCircle v-if="!(setResult as any).skipped?.length" class="w-5 h-5 flex-shrink-0 mt-0.5" />
      <AlertTriangle v-else class="w-5 h-5 flex-shrink-0 mt-0.5" />
      <div>
        Applied Pipe Sizing criteria to <strong>{{ (setResult as any).applied }}</strong> pipe(s) in model.
        <span v-if="(setResult as any).skipped?.length" class="block mt-1 text-xs">
          Skipped (no criteria assigned): {{ (setResult as any).skipped.join(', ') }}
        </span>
      </div>
    </div>

    <!-- Predict result alert -->
    <div v-if="predictResult" class="flex items-start gap-2 p-3 rounded"
      :class="predictResult.errors.length ? 'bg-yellow-50 border border-yellow-200 text-yellow-700' : 'bg-blue-50 border border-blue-200 text-blue-700'">
      <Wand2 class="w-5 h-5 flex-shrink-0 mt-0.5" />
      <div>
        Predicted <strong>{{ predictResult.filled_state }}</strong> state(s) and
        <strong>{{ predictResult.filled_criteria }}</strong> criteria code(s).
        Review below, then click <strong>Set Criteria to Model</strong> to apply.
        <ul v-if="predictResult.errors.length" class="mt-2 pl-4 text-xs list-disc">
          <li v-for="e in predictResult.errors" :key="e">{{ e }}</li>
        </ul>
      </div>
    </div>

    <!-- Main card -->
    <div class="pk-card">
      <div class="pk-card-header flex items-center justify-between">
        <span class="flex items-center gap-1">
          <Ruler class="w-4 h-4 text-blue-600" /> Pipe Sizing Criteria
          <span class="pk-badge-blue ml-2">{{ pipes.length }} pipes</span>
        </span>
        <router-link to="/model" class="pk-btn-secondary text-xs">
          <ArrowLeft class="w-3 h-3" /> Back
        </router-link>
      </div>

      <!-- Toolbar -->
      <div class="px-4 pt-3 pb-0">
        <div class="flex flex-wrap gap-2 items-end mb-3">
          <div>
            <input v-model="pipeFilter" type="text" class="pk-input" placeholder="Filter pipes…"
              style="width: 180px;" />
          </div>
          <div>
            <select v-model="unitSystem" class="pk-select" style="width: 130px;" title="Unit system for displayed values">
              <option value="SI">SI</option>
              <option value="Engg_SI">Engg SI</option>
            </select>
          </div>
          <div>
            <button @click="predictLoading.execute()"
              class="border border-cyan-400 text-cyan-600 rounded px-3 py-1 text-xs hover:bg-cyan-50 flex items-center gap-1"
              :disabled="predictLoading.isLoading.value"
              title="Auto-fill state from liquid fraction (LF) and predict criteria where possible">
              <span v-if="predictLoading.isLoading.value" class="pk-spinner" />
              <Wand2 class="w-3 h-3" /> Auto-predict
            </button>
          </div>
          <div class="ml-auto flex items-center gap-2">
            <span class="text-xs text-gray-500">Set rows:</span>
            <select v-model="bulkState" class="pk-select" style="width: 140px;">
              <option value="">— State —</option>
              <option v-for="(label, ft) in fluidLabels" :key="ft" :value="ft">{{ label }}</option>
            </select>
            <select v-model="bulkCriteria" class="pk-select" style="width: 220px;"
              :disabled="!bulkState">
              <option value="">— Criteria —</option>
              <option v-for="[code, label] in getAvailableCriteriaForState(bulkState)" :key="code" :value="code">{{ label }}</option>
            </select>
            <button @click="applyBulkToVisible" class="pk-btn-secondary text-xs">
              Apply to visible
            </button>
          </div>
        </div>
      </div>

      <!-- Table -->
      <div style="max-height: 65vh; overflow-y: auto;">
        <table class="pk-table">
          <thead class="sticky top-0 z-10 bg-gray-50 border-b">
            <tr>
              <th style="width: 36px;" class="text-center">
                <input type="checkbox" v-model="selectAllChecked" @change="toggleSelectAll"
                  class="rounded" title="Select all visible" />
              </th>
              <th style="width: 60px;" class="pk-table-head-cell">#</th>
              <th style="width: 130px;" class="pk-table-head-cell">Pipe</th>
              <th style="width: 160px;" class="pk-table-head-cell">State</th>
              <th style="min-width: 180px;" class="pk-table-head-cell">Criteria</th>
              <th style="width: 90px;" class="pk-table-head-cell text-center">dP calc<br /><small class="font-normal text-gray-400">{{ dpUnit }}</small></th>
              <th style="width: 100px;" class="pk-table-head-cell text-center crit-col">dP max<br /><small class="font-normal text-gray-400">{{ dpUnit }}</small></th>
              <th style="width: 80px;" class="pk-table-head-cell text-center">vel calc<br /><small class="font-normal text-gray-400">{{ velocityUnit }}</small></th>
              <th style="width: 80px;" class="pk-table-head-cell text-center crit-col">v min<br /><small class="font-normal text-gray-400">{{ velocityUnit }}</small></th>
              <th style="width: 80px;" class="pk-table-head-cell text-center crit-col">v max<br /><small class="font-normal text-gray-400">{{ velocityUnit }}</small></th>
              <th style="width: 90px;" class="pk-table-head-cell text-center">ρV² calc<br /><small class="font-normal text-gray-400">{{ rhoV2Unit }}</small></th>
              <th style="width: 120px;" class="pk-table-head-cell text-center crit-col">ρV² range<br /><small class="font-normal text-gray-400">{{ rhoV2Unit }}</small></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="[idx, name] in filteredPipes" :key="name"
              class="border-b hover:bg-gray-50"
              :class="{ 'bg-yellow-50': dirtyPipes.has(name) }">
              <td class="text-center">
                <input type="checkbox" :checked="selectedRows.has(name)"
                  @change="toggleRow(name)" class="rounded" />
              </td>
              <td class="px-3 py-1.5 text-gray-400 font-mono text-xs">{{ idx }}</td>
              <td class="px-3 py-1.5 font-mono font-semibold text-sm">{{ name }}</td>
              <td class="px-3 py-1.5">
                <select :value="editedCriteria[name]?.state || ''"
                  @change="updateEntry(name, 'state', ($event.target as HTMLSelectElement).value)"
                  class="pk-select">
                  <option value="">—</option>
                  <option v-for="(label, ft) in fluidLabels" :key="ft" :value="ft">{{ label }}</option>
                </select>
              </td>
              <td class="px-3 py-1.5">
                <select :value="editedCriteria[name]?.criteria || ''"
                  @change="updateEntry(name, 'criteria', ($event.target as HTMLSelectElement).value)"
                  class="pk-select"
                  :disabled="!editedCriteria[name]?.state">
                  <option value="">—</option>
                  <option v-for="[code, label] in getAvailableCriteriaForState(editedCriteria[name]?.state || '')" :key="code" :value="code">
                    {{ label }}
                  </option>
                </select>
              </td>
              <td class="pk-text-right-mono">
                {{ convertValue('dp', (pipeCalcs[name] as any)?.dp_calc as number | null) }}
              </td>
              <td class="pk-text-right-mono-muted crit-col">
                <template v-if="editedCriteria[name]?.state && editedCriteria[name]?.criteria">
                  {{ convertValue('dp', (criteriaValues[name]?.[`${editedCriteria[name].state}:${editedCriteria[name].criteria}`] as any)?.max_dp as number | null) }}
                </template>
                <template v-else>—</template>
              </td>
              <td class="pk-text-right-mono">
                {{ convertValue('velocity', (pipeCalcs[name] as any)?.vel_calc as number | null) }}
              </td>
              <td class="pk-text-right-mono-muted crit-col">
                <template v-if="editedCriteria[name]?.state && editedCriteria[name]?.criteria">
                  {{ convertValue('velocity', (criteriaValues[name]?.[`${editedCriteria[name].state}:${editedCriteria[name].criteria}`] as any)?.min_vel as number | null) }}
                </template>
                <template v-else>—</template>
              </td>
              <td class="pk-text-right-mono-muted crit-col">
                <template v-if="editedCriteria[name]?.state && editedCriteria[name]?.criteria">
                  {{ convertValue('velocity', (criteriaValues[name]?.[`${editedCriteria[name].state}:${editedCriteria[name].criteria}`] as any)?.max_vel as number | null) }}
                </template>
                <template v-else>—</template>
              </td>
              <td class="pk-text-right-mono">
                {{ convertValue('rho_v2', (pipeCalcs[name] as any)?.rho_v2_calc as number | null) }}
              </td>
              <td class="pk-text-right-mono-muted crit-col">
                <template v-if="editedCriteria[name]?.state && editedCriteria[name]?.criteria">
                  {{ convertValue('rho_v2', (criteriaValues[name]?.[`${editedCriteria[name].state}:${editedCriteria[name].criteria}`] as any)?.rho_v2_min as number | null) }}
                  –
                  {{ convertValue('rho_v2', (criteriaValues[name]?.[`${editedCriteria[name].state}:${editedCriteria[name].criteria}`] as any)?.rho_v2_max as number | null) }}
                </template>
                <template v-else>—</template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Footer -->
      <div class="px-4 py-2 border-t flex items-center justify-between">
        <div class="flex gap-2">
          <button @click="clearAll" class="border border-red-200 text-red-600 rounded px-3 py-1 text-xs hover:bg-red-50 flex items-center gap-1">
            <XCircle class="w-3 h-3" /> Clear All
          </button>
          <button @click="saveLoading.execute()" class="bg-green-600 text-white rounded px-3 py-1 text-xs hover:bg-green-700 flex items-center gap-1"
            :disabled="saveLoading.isLoading.value">
            <span v-if="saveLoading.isLoading.value" class="pk-spinner" />
            <Zap class="w-3 h-3" /> Set Criteria to Model
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Criteria limit columns — grey background */
.crit-col {
  background-color: #f1f3f5 !important;
  color: #6c757d;
}
</style>
