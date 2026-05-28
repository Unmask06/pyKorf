<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '../stores/session'
import { useModelStore } from '../stores/model'
import { useToastStore } from '../composables/useToast'
import { useLoading } from '../composables/useLoading'
import { Ruler, ArrowLeft, Wand2, XCircle, Zap, CheckCircle, AlertTriangle, MessageSquare, AlertCircle } from 'lucide-vue-next'
import type {
  CriteriaValuesInfo,
  CriteriaViolationsInfo,
  JustificationRequest,
  PipeCalcInfo,
  PipeCriteriaEntry,
  PipeCriteriaResponse,
  PredictCriteriaResponse,
  SetCriteriaResponse,
  UnitConversionInfo,
  ViolationSummary,
} from '../api/generated/types.gen'
import { savePipeJustification } from '../api/generated/sdk.gen'

const router = useRouter()
const session = useSessionStore()
const model = useModelStore()
const toast = useToastStore()

// Criteria table data
const pipes = ref<Array<[number, string]>>([])
const existing = ref<Record<string, PipeCriteriaEntry>>({})
const codes = ref<Record<string, string[][]>>({})
const criteriaValues = ref<Record<string, Record<string, CriteriaValuesInfo>>>({})
const criteriaViolations = ref<Record<string, Record<string, CriteriaViolationsInfo>>>({})
const pipeCalcs = ref<Record<string, PipeCalcInfo>>({})
const unitsData = ref<Record<string, Record<string, UnitConversionInfo>>>({})
const fluidLabels = ref<Record<string, string>>({})
const justifications = ref<Record<string, string>>({})
const orphanedJustifications = ref<Record<string, string>>({})
const violationSummary = ref<ViolationSummary | null>(null)

// Edited criteria entries
const pipeCriteria = ref<Record<string, PipeCriteriaEntry>>({})
const dirtyPipes = ref<Set<string>>(new Set())
const predictResult = ref<PredictCriteriaResponse | null>(null)

// UI state
const pipeFilter = ref('')
const unitSystem = ref('Engg_SI')
const selectAllChecked = ref(false)
const selectedRows = ref<Set<string>>(new Set())
const bulkState = ref('')
const bulkCriteria = ref('')
const setResult = ref<SetCriteriaResponse | null>(null)

// Justification modal state
const justificationModal = ref({
  open: false,
  pipeName: '',
  pipeIdx: 0,
  criteria: '',
  criteriaLabel: '',
  justification: '',
  violations: null as CriteriaViolationsInfo | null,
  calcInfo: null as PipeCalcInfo | null,
  criteriaValues: null as CriteriaValuesInfo | null,
})

// Computed unit labels based on selected unit system
const dpUnit = computed(() => {
  if (unitSystem.value === 'SI') return 'kPa/100m'
  const conv = unitsData.value.Engg_SI?.['kPa/100m']
  return conv?.target_unit || 'bar/100m'
})

const velocityUnit = computed(() => 'm/s')
const rhoV2Unit = computed(() => 'Pa')

function _applyResponse(data: PipeCriteriaResponse) {
  pipes.value = data.pipes ?? []
  existing.value = data.existing ?? {}
  codes.value = data.codes ?? {}
  criteriaValues.value = data.pipe_criteria_values ?? {}
  criteriaViolations.value = data.pipe_criteria_violations ?? {}
  pipeCalcs.value = data.pipe_calcs ?? {}
  unitsData.value = data.units_data ?? {}
  fluidLabels.value = data.fluid_labels ?? {}
  setResult.value = data.set_result ?? null
  predictResult.value = data.predict_result ?? null
  justifications.value = data.justifications ?? {}
  orphanedJustifications.value = data.orphaned_justifications ?? {}
  violationSummary.value = data.violation_summary ?? null

  const initial: Record<string, PipeCriteriaEntry> = {}
  for (const [name, vals] of Object.entries(data.existing ?? {})) {
    initial[name] = { state: vals.state || '', criteria: vals.criteria || '' }
  }
  pipeCriteria.value = initial
  dirtyPipes.value = new Set()
}

const criteriaLoading = useLoading(async () => {
  const data = await model.fetchPipeCriteria()
  _applyResponse(data)
})

const predictLoading = useLoading(async () => {
  const data = await model.predictCriteria()
  predictResult.value = data
  for (const [name, entry] of Object.entries(data.predicted ?? {})) {
    if (!pipeCriteria.value[name]?.state || !pipeCriteria.value[name]?.criteria) {
      pipeCriteria.value[name] = { state: entry.state || '', criteria: entry.criteria || '' }
      dirtyPipes.value.add(name)
    }
  }
  toast.info(`Predicted: ${data.filled_state ?? 0} states, ${data.filled_criteria ?? 0} criteria codes filled.`)
})

const saveLoading = useLoading(async () => {
  const result = await model.setPipeCriteria(pipeCriteria.value)
  await session.fetchStatus()
  toast.success(`Applied criteria to ${result.applied ?? 0} pipe(s).`)
  if (result.skipped?.length) {
    toast.warning(`Skipped: ${result.skipped.join(', ')}`)
  }
  await criteriaLoading.execute()
})

function updateEntry(name: string, field: 'state' | 'criteria', value: string) {
  if (!pipeCriteria.value[name]) {
    pipeCriteria.value[name] = { state: '', criteria: '' }
  }
  pipeCriteria.value[name][field] = value
  dirtyPipes.value.add(name)
}

function getAvailableCriteriaForState(state: string): Array<[string, string]> {
  if (!state || !codes.value[state]) return []
  return codes.value[state].map((c: string[]) => [c[0], c[1]])
}

function convertValue(field: string, siValue: number | null): string {
  if (siValue === null || siValue === undefined) return '—'
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
  const systemConversions = unitsData.value[unitSystem.value] || unitsData.value.Engg_SI || {}
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

// Clean up selections when filter changes
watch(filteredPipes, (newFiltered) => {
  const visibleNames = new Set(newFiltered.map(([, name]) => name))
  for (const name of selectedRows.value) {
    if (!visibleNames.has(name)) {
      selectedRows.value.delete(name)
    }
  }
  // Update select-all checkbox state
  selectAllChecked.value = newFiltered.length > 0 && newFiltered.every(([, name]) => selectedRows.value.has(name))
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
    selectAllChecked.value = false
  } else {
    selectedRows.value.add(name)
  }
}

// Auto-sync "Set rows" state dropdown based on selected rows
const selectedStates = computed(() => {
  const states = new Set<string>()
  for (const name of selectedRows.value) {
    const s = pipeCriteria.value[name]?.state || ''
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
watch(pipeCriteria, () => syncBulkStateFromSelection(), { deep: true })

// Computed: are any rows selected (that are also visible)?
const hasSelection = computed(() => {
  const visibleNames = new Set(filteredPipes.value.map(([, name]) => name))
  return [...selectedRows.value].some((n) => visibleNames.has(n))
})

function currentCriteriaInfo(name: string): CriteriaValuesInfo | undefined {
  const entry = pipeCriteria.value[name]
  if (!entry?.state || !entry.criteria) return undefined
  return criteriaValues.value[name]?.[`${entry.state}:${entry.criteria}`]
}

function criteriaKeyFor(name: string): string {
  const entry = pipeCriteria.value[name]
  return entry ? `${entry.state}:${entry.criteria}` : ''
}

function getViolations(name: string): CriteriaViolationsInfo | undefined {
  const key = criteriaKeyFor(name)
  return key ? criteriaViolations.value[name]?.[key] : undefined
}

function openJustificationModal(name: string, criteriaKey: string) {
  const entry = pipeCriteria.value[name]
  if (!entry?.state || !entry.criteria) return

  const violations = criteriaViolations.value[name]?.[criteriaKey]
  const isOrphaned = !!orphanedJustifications.value[name]

  if (!violations || violations.overall === 'PASS') {
    if (!isOrphaned) return
  }

  const critVals = criteriaValues.value[name]?.[criteriaKey]
  const calcInfo = pipeCalcs.value[name]

  const criteriaLabel = codes.value[entry.state]?.find(c => c[0] === entry.criteria)?.[1] || entry.criteria

  const pipeEntry = pipes.value.find(([, n]) => n === name)
  const pipeIdx = pipeEntry ? pipeEntry[0] : 0

  justificationModal.value = {
    open: true,
    pipeName: name,
    pipeIdx,
    criteria: criteriaKey,
    criteriaLabel,
    justification: justifications.value[name] || '',
    violations,
    calcInfo,
    criteriaValues: critVals,
  }
}

function closeJustificationModal() {
  justificationModal.value.open = false
}

const saveJustificationLoading = useLoading(async () => {
  const { pipeIdx, criteria, justification } = justificationModal.value
  try {
    const response = await savePipeJustification({
      body: {
        pipe_idx: pipeIdx,
        justification: justification,
      } as JustificationRequest,
    })
    justifications.value = response.data?.justifications || {}
    toast.success('Justification saved')
    closeJustificationModal()
    await criteriaLoading.execute()
  } catch (error: any) {
    toast.error(error?.response?.data?.detail || 'Failed to save justification')
  }
})

function applyBulk() {
  if (!bulkState.value && !bulkCriteria.value) {
    toast.warning('Select a state or criteria to apply.')
    return
  }
  const targets = hasSelection.value
    ? filteredPipes.value.filter(([, name]) => selectedRows.value.has(name))
    : filteredPipes.value
  for (const [, name] of targets) {
    if (bulkState.value) {
      updateEntry(name, 'state', bulkState.value)
    }
    if (bulkCriteria.value) {
      updateEntry(name, 'criteria', bulkCriteria.value)
    }
  }
  const label = hasSelection.value ? 'selected' : 'visible'
  toast.info(`Applied to ${targets.length} ${label} pipe(s).`)
}

function clearAll() {
  for (const [, name] of pipes.value) {
    pipeCriteria.value[name] = { state: '', criteria: '' }
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
      :class="(setResult.skipped ?? []).length ? 'bg-yellow-50 border border-yellow-200 text-yellow-700' : 'bg-green-50 border border-green-200 text-green-700'">
      <CheckCircle v-if="!(setResult.skipped ?? []).length" class="w-5 h-5 shrink-0 mt-0.5" />
      <AlertTriangle v-else class="w-5 h-5 shrink-0 mt-0.5" />
      <div>
        Applied Pipe Sizing criteria to <strong>{{ setResult.applied }}</strong> pipe(s) in model.
        <span v-if="(setResult.skipped ?? []).length" class="block mt-1 text-xs">
          Skipped (no criteria assigned): {{ (setResult.skipped ?? []).join(', ') }}
        </span>
      </div>
    </div>

    <!-- Predict result alert -->
    <div v-if="predictResult" class="flex items-start gap-2 p-3 rounded"
      :class="(predictResult.errors ?? []).length ? 'bg-yellow-50 border border-yellow-200 text-yellow-700' : 'bg-blue-50 border border-blue-200 text-blue-700'">
      <Wand2 class="w-5 h-5 shrink-0 mt-0.5" />
      <div>
        Predicted <strong>{{ predictResult.filled_state }}</strong> state(s) and
        <strong>{{ predictResult.filled_criteria }}</strong> criteria code(s).
        Review below, then click <strong>Set Criteria to Model</strong> to apply.
        <ul v-if="(predictResult.errors ?? []).length" class="mt-2 pl-4 text-xs list-disc">
          <li v-for="e in (predictResult.errors ?? [])" :key="e">{{ e }}</li>
        </ul>
      </div>
    </div>

    <!-- Orphaned justifications alert -->
    <div v-if="Object.keys(orphanedJustifications).length > 0" class="flex items-start gap-2 p-3 rounded bg-amber-50 border border-amber-200 text-amber-800">
      <AlertCircle class="w-5 h-5 shrink-0 mt-0.5" />
      <div>
        <strong>{{ Object.keys(orphanedJustifications).length }}</strong> pipe(s) have saved justifications but no current violations:
        {{ Object.keys(orphanedJustifications).join(', ') }}.
        <span class="text-xs">These will be preserved and applied when violations re-occur (e.g. in other cases).</span>
      </div>
    </div>

    <!-- Main card -->
    <div class="pk-card">
      <div class="pk-card-header flex items-center justify-between">
        <span class="flex items-center gap-1">
          <Ruler class="w-4 h-4 text-blue-600" /> Pipe Sizing Criteria
          <span class="pk-badge-blue ml-2">{{ pipes.length }} pipes</span>
          <span
            v-if="violationSummary?.violations_needing_justification && violationSummary.violations_needing_justification > 0"
            class="ml-2 px-2 py-0.5 text-xs rounded-full bg-yellow-100 text-yellow-700 border border-yellow-300 flex items-center gap-1"
            title="Violations needing justification"
          >
            <AlertCircle class="w-3 h-3" />
            {{ violationSummary.violations_needing_justification }} violations need justification
          </span>
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
            <button @click="applyBulk" class="pk-btn-secondary text-xs"
              :title="hasSelection ? 'Apply to selected rows' : 'Apply to all visible rows'">
              {{ hasSelection ? `Apply to selected (${selectedRows.size})` : 'Apply to visible' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Table -->
      <div style="max-height: 65vh; overflow-y: auto;">
        <div v-if="criteriaLoading.isLoading.value" class="flex items-center justify-center py-12">
          <div class="flex items-center gap-2 text-gray-500">
            <span class="pk-spinner" />
            <span>Loading pipe criteria...</span>
          </div>
        </div>
        <table v-else class="pk-table">
          <thead class="sticky top-0 z-10 bg-gray-50 border-b">
            <tr>
              <th style="width: 36px;" class="text-center">
                <input type="checkbox" v-model="selectAllChecked" @change="toggleSelectAll"
                  class="rounded" title="Select all visible" />
              </th>
              <th style="width: 60px;" class="pk-table-head-cell">#</th>
              <th style="width: 180px;" class="pk-table-head-cell">Pipe</th>
              <th style="width: 70px;" class="pk-table-head-cell-center">Size<br /><small class="font-normal text-gray-400">inch</small></th>
              <th style="width: 60px;" class="pk-table-head-cell-center">Length<br /><small class="font-normal text-gray-400">m</small></th>
              <th style="width: 130px;" class="pk-table-head-cell">State</th>
              <th style="min-width: 180px;" class="pk-table-head-cell">Criteria</th>
              <th style="width: 90px;" class="pk-table-head-cell-center">dP calc<br /><small class="font-normal text-gray-400">{{ dpUnit }}</small></th>
              <th style="width: 100px;" class="pk-table-head-cell-center crit-col">dP max<br /><small class="font-normal text-gray-400">{{ dpUnit }}</small></th>
              <th style="width: 80px;" class="pk-table-head-cell-center">vel calc<br /><small class="font-normal text-gray-400">{{ velocityUnit }}</small></th>
              <th style="width: 80px;" class="pk-table-head-cell-center crit-col">v min<br /><small class="font-normal text-gray-400">{{ velocityUnit }}</small></th>
              <th style="width: 80px;" class="pk-table-head-cell-center crit-col">v max<br /><small class="font-normal text-gray-400">{{ velocityUnit }}</small></th>
              <th style="width: 90px;" class="pk-table-head-cell-center">ρV² calc<br /><small class="font-normal text-gray-400">{{ rhoV2Unit }}</small></th>
              <th style="width: 80px;" class="pk-table-head-cell-center crit-col">ρV² max<br /><small class="font-normal text-gray-400">{{ rhoV2Unit }}</small></th>
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
              <td class="px-3 py-1.5 font-mono text-sm">{{ name }}</td>
              <td class="pk-text-center-mono-muted">
                {{ pipeCalcs[name]?.line_size || '—' }}
              </td>
              <td class="pk-text-center-mono-muted">
                {{ pipeCalcs[name]?.length_m !== null && pipeCalcs[name]?.length_m !== undefined ? Math.round(pipeCalcs[name]?.length_m) : '—' }}
              </td>
              <td class="px-3 py-1.5 text-center">
                <select :value="pipeCriteria[name]?.state || ''"
                  @change="updateEntry(name, 'state', ($event.target as HTMLSelectElement).value)"
                  class="pk-select">
                  <option value="">—</option>
                  <option v-for="(label, ft) in fluidLabels" :key="ft" :value="ft">{{ label }}</option>
                </select>
              </td>
              <td class="px-3 py-1.5">
                <select :value="pipeCriteria[name]?.criteria || ''"
                  @change="updateEntry(name, 'criteria', ($event.target as HTMLSelectElement).value)"
                  class="pk-select"
                  :disabled="!pipeCriteria[name]?.state">
                  <option value="">—</option>
                  <option v-for="[code, label] in getAvailableCriteriaForState(pipeCriteria[name]?.state || '')" :key="code" :value="code">
                    {{ label }}
                  </option>
                </select>
              </td>
              <td class="pk-text-center-mono" 
                  :class="{ 'viol-red': getViolations(name)?.dp_exceeds && !justifications[name], 'viol-justified': getViolations(name)?.dp_exceeds && justifications[name] && !orphanedJustifications[name], 'viol-orphaned': justifications[name] && !getViolations(name)?.dp_exceeds }"
                  @click="(getViolations(name)?.dp_exceeds || orphanedJustifications[name]) && openJustificationModal(name, criteriaKeyFor(name))"
                  :style="(getViolations(name)?.dp_exceeds || orphanedJustifications[name]) ? 'cursor: pointer;' : ''">
                <div class="flex items-center justify-center gap-1">
                  <MessageSquare v-if="justifications[name] && (getViolations(name)?.dp_exceeds || orphanedJustifications[name])" class="w-3 h-3 shrink-0" :class="orphanedJustifications[name] && !getViolations(name)?.dp_exceeds ? 'text-gray-400' : 'text-blue-500'" />
                  {{ convertValue('dp', pipeCalcs[name]?.dp_calc ?? null) }}
                </div>
              </td>
              <td class="pk-text-center-mono crit-col">
                <template v-if="pipeCriteria[name]?.state && pipeCriteria[name]?.criteria">
                  {{ convertValue('dp', currentCriteriaInfo(name)?.max_dp ?? null) }}
                </template>
                <template v-else>—</template>
              </td>
              <td class="pk-text-center-mono" 
                  :class="{ 'viol-red': (getViolations(name)?.vel_below_min || getViolations(name)?.vel_above_max) && !justifications[name], 'viol-justified': (getViolations(name)?.vel_below_min || getViolations(name)?.vel_above_max) && justifications[name] && !orphanedJustifications[name], 'viol-orphaned': justifications[name] && !(getViolations(name)?.vel_below_min || getViolations(name)?.vel_above_max) }"
                  @click="(getViolations(name)?.vel_below_min || getViolations(name)?.vel_above_max || orphanedJustifications[name]) && openJustificationModal(name, criteriaKeyFor(name))"
                  :style="(getViolations(name)?.vel_below_min || getViolations(name)?.vel_above_max || orphanedJustifications[name]) ? 'cursor: pointer;' : ''">
                <div class="flex items-center justify-center gap-1">
                  <MessageSquare v-if="justifications[name] && (getViolations(name)?.vel_below_min || getViolations(name)?.vel_above_max || orphanedJustifications[name])" class="w-3 h-3 shrink-0" :class="orphanedJustifications[name] && !(getViolations(name)?.vel_below_min || getViolations(name)?.vel_above_max) ? 'text-gray-400' : 'text-blue-500'" />
                  {{ convertValue('velocity', pipeCalcs[name]?.vel_calc ?? null) }}
                </div>
              </td>
              <td class="pk-text-center-mono crit-col">
                <template v-if="pipeCriteria[name]?.state && pipeCriteria[name]?.criteria">
                  {{ convertValue('velocity', currentCriteriaInfo(name)?.min_vel ?? null) }}
                </template>
                <template v-else>—</template>
              </td>
              <td class="pk-text-center-mono crit-col">
                <template v-if="pipeCriteria[name]?.state && pipeCriteria[name]?.criteria">
                  {{ convertValue('velocity', currentCriteriaInfo(name)?.max_vel ?? null) }}
                </template>
                <template v-else>—</template>
              </td>
              <td class="pk-text-center-mono" 
                  :class="{ 'viol-red': (getViolations(name)?.rho_v2_below_min || getViolations(name)?.rho_v2_above_max) && !justifications[name], 'viol-justified': (getViolations(name)?.rho_v2_below_min || getViolations(name)?.rho_v2_above_max) && justifications[name] && !orphanedJustifications[name], 'viol-orphaned': justifications[name] && !(getViolations(name)?.rho_v2_below_min || getViolations(name)?.rho_v2_above_max) }"
                  @click="(getViolations(name)?.rho_v2_below_min || getViolations(name)?.rho_v2_above_max || orphanedJustifications[name]) && openJustificationModal(name, criteriaKeyFor(name))"
                  :style="(getViolations(name)?.rho_v2_below_min || getViolations(name)?.rho_v2_above_max || orphanedJustifications[name]) ? 'cursor: pointer;' : ''">
                <div class="flex items-center justify-center gap-1">
                  <MessageSquare v-if="justifications[name] && (getViolations(name)?.rho_v2_below_min || getViolations(name)?.rho_v2_above_max || orphanedJustifications[name])" class="w-3 h-3 shrink-0" :class="orphanedJustifications[name] && !(getViolations(name)?.rho_v2_below_min || getViolations(name)?.rho_v2_above_max) ? 'text-gray-400' : 'text-blue-500'" />
                  {{ convertValue('rho_v2', pipeCalcs[name]?.rho_v2_calc ?? null) }}
                </div>
              </td>
              <td class="pk-text-center-mono crit-col">
                <template v-if="pipeCriteria[name]?.state && pipeCriteria[name]?.criteria">
                  {{ convertValue('rho_v2', currentCriteriaInfo(name)?.rho_v2_max ?? null) }}
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

    <!-- Justification Modal -->
    <div v-if="justificationModal.open" 
         class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
         @click.self="closeJustificationModal">
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div class="p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900">
              Justification for {{ justificationModal.pipeName }}
            </h3>
            <button @click="closeJustificationModal" class="text-gray-400 hover:text-gray-600">
              <XCircle class="w-5 h-5" />
            </button>
          </div>

          <div class="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
            <p class="text-sm text-blue-800">
              <strong>Criteria:</strong> {{ justificationModal.criteriaLabel }}
            </p>
          </div>

          <div v-if="orphanedJustifications[justificationModal.pipeName] && (!justificationModal.violations || justificationModal.violations.overall === 'PASS')" class="mb-4 p-3 bg-amber-50 border border-amber-200 rounded">
            <p class="text-sm text-amber-800">
              This pipe is not currently violating criteria. The justification below will be preserved for future cases where it may be needed.
            </p>
          </div>

          <div class="mb-4">
            <h4 class="text-sm font-medium text-gray-700 mb-2">Violation Details</h4>
            <div class="grid grid-cols-2 gap-2 text-sm">
              <div v-if="justificationModal.violations?.dp_exceeds" class="p-2 bg-red-50 border border-red-200 rounded">
                <span class="text-red-700">dP Exceeds:</span>
                <span class="ml-2 font-mono">{{ convertValue('dp', justificationModal.calcInfo?.dp_calc ?? null) }}</span>
                <span class="mx-1">></span>
                <span class="font-mono">{{ convertValue('dp', justificationModal.criteriaValues?.max_dp ?? null) }}</span>
              </div>
              <div v-if="justificationModal.violations?.vel_below_min" class="p-2 bg-red-50 border border-red-200 rounded">
                <span class="text-red-700">Velocity Below Min:</span>
                <span class="ml-2 font-mono">{{ convertValue('velocity', justificationModal.calcInfo?.vel_calc ?? null) }}</span>
                <span class="mx-1"><</span>
                <span class="font-mono">{{ convertValue('velocity', justificationModal.criteriaValues?.min_vel ?? null) }}</span>
              </div>
              <div v-if="justificationModal.violations?.vel_above_max" class="p-2 bg-red-50 border border-red-200 rounded">
                <span class="text-red-700">Velocity Above Max:</span>
                <span class="ml-2 font-mono">{{ convertValue('velocity', justificationModal.calcInfo?.vel_calc ?? null) }}</span>
                <span class="mx-1">></span>
                <span class="font-mono">{{ convertValue('velocity', justificationModal.criteriaValues?.max_vel ?? null) }}</span>
              </div>
              <div v-if="justificationModal.violations?.rho_v2_below_min" class="p-2 bg-red-50 border border-red-200 rounded">
                <span class="text-red-700">ρV² Below Min:</span>
                <span class="ml-2 font-mono">{{ convertValue('rho_v2', justificationModal.calcInfo?.rho_v2_calc ?? null) }}</span>
                <span class="mx-1"><</span>
                <span class="font-mono">{{ convertValue('rho_v2', justificationModal.criteriaValues?.rho_v2_min ?? null) }}</span>
              </div>
              <div v-if="justificationModal.violations?.rho_v2_above_max" class="p-2 bg-red-50 border border-red-200 rounded">
                <span class="text-red-700">ρV² Above Max:</span>
                <span class="ml-2 font-mono">{{ convertValue('rho_v2', justificationModal.calcInfo?.rho_v2_calc ?? null) }}</span>
                <span class="mx-1">></span>
                <span class="font-mono">{{ convertValue('rho_v2', justificationModal.criteriaValues?.rho_v2_max ?? null) }}</span>
              </div>
            </div>
          </div>

          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Justification <span class="text-gray-500">(optional, clears if empty)</span>
            </label>
            <textarea
              v-model="justificationModal.justification"
              rows="4"
              class="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter justification for this criteria violation (e.g., 'Temporary design exception approved by engineering lead')"
            ></textarea>
          </div>

          <div class="flex justify-end gap-2">
            <button
              @click="closeJustificationModal"
              class="px-4 py-2 text-sm border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              @click="saveJustificationLoading.execute()"
              :disabled="saveJustificationLoading.isLoading.value"
              class="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              <span v-if="saveJustificationLoading.isLoading.value" class="pk-spinner" />
              <CheckCircle class="w-4 h-4" />
              Save Justification
            </button>
          </div>
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

/* Center-align calculation columns */
.pk-text-center-mono,
.pk-text-center-mono-muted {
  text-align: center;
  font-family: monospace;
  font-size: 0.875rem;
}

.pk-text-center-mono-muted {
  color: #6c757d;
}

/* Violation highlighting — red background */
.viol-red {
  background-color: #fee2e2 !important;
  color: #dc2626;
}

/* Justified violation highlighting — blue background */
.viol-justified {
  background-color: #dbeafe !important;
  color: #1e40af;
}

/* Orphaned justification highlighting — grey background */
.viol-orphaned {
  background-color: #f3f4f6 !important;
  color: #6b7280;
}
</style>
