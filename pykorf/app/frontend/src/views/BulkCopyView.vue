<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '../stores/session'
import { useModelStore } from '../stores/model'
import { useToastStore } from '../composables/useToast'
import { useLoading } from '../composables/useLoading'
import { Copy, FileText, Files, Lightbulb, ListChecks } from 'lucide-vue-next'
import { api } from '../api/client'
import type { BulkCopyResponse } from '../types/api'

const router = useRouter()
const session = useSessionStore()
const model = useModelStore()
const toast = useToastStore()

const refPipe = ref('')
const targetPipes = ref('')
const excludeMode = ref(false)
const pipeFilter = ref('')

const copyLoading = useLoading(async () => {
  const { data } = await api.post<BulkCopyResponse>('/api/model/bulk-copy', {
    ref_pipe: refPipe.value,
    target_pipes: targetPipes.value,
    exclude: excludeMode.value,
  })
  await session.fetchStatus()
  await model.fetchSummary()
  return data
})

async function doCopy() {
  if (!refPipe.value.trim()) {
    toast.error('Please enter a reference pipe name.')
    return
  }
  try {
    const res = await copyLoading.execute()
    if (res?.success) {
      toast.success(`Fluids copied to ${res.updated_count} pipe(s).`)
    } else {
      toast.error(res?.error || 'Bulk copy failed.')
    }
  } catch (err: any) {
    toast.error(err.response?.data?.detail || err.message)
  }
}

const filteredPipes = computed(() => {
  if (!pipeFilter.value) return model.pipes
  const q = pipeFilter.value.toLowerCase()
  return model.pipes.filter(p => p.toLowerCase().includes(q))
})

onMounted(() => {
  if (!session.isLoaded) router.push('/')
  model.fetchPipes()
})
</script>

<template>
  <div class="flex gap-4 flex-wrap lg:flex-nowrap">

    <!-- ── Left: Form card ───────────────────────────────────── -->
    <div class="w-full lg:w-2/3">
      <div class="pk-card">
        <div class="pk-card-header flex items-center gap-2">
          <Copy class="w-4 h-4 text-blue-600" /> Bulk Copy Fluids
        </div>
        <div class="pk-card-body">

          <!-- Reference pipe input -->
          <div class="mb-3">
            <label class="pk-label">Reference Pipe (copy FROM)</label>
            <div class="flex">
              <span class="flex items-center justify-center px-3 py-1.5 text-sm bg-gray-100 border border-r-0 border-gray-300 rounded-l-md">
                <FileText class="w-4 h-4 text-gray-500" />
              </span>
              <input v-model="refPipe" type="text" list="pipe-datalist"
                class="pk-input-mono rounded-none" placeholder="e.g. L1" autocomplete="off" />
              <datalist id="pipe-datalist">
                <option v-for="p in model.pipes" :key="p" :value="p" />
              </datalist>
            </div>
            <div class="pk-hint">The pipe whose fluid properties will be copied.</div>
          </div>

          <!-- Target pipes input -->
          <div class="mb-3">
            <label class="pk-label">Target Pipes (copy TO)</label>
            <div class="flex">
              <span class="flex items-center justify-center px-3 py-1.5 text-sm bg-gray-100 border border-r-0 border-gray-300 rounded-l-md">
                <Files class="w-4 h-4 text-gray-500" />
              </span>
              <input v-model="targetPipes" type="text"
                class="pk-input-mono rounded-none" placeholder="e.g. L2, L3, L4 (leave empty for ALL pipes)"
                autocomplete="off" />
              <button type="button" @click="targetPipes = ''"
                class="flex items-center justify-center px-2 py-1.5 text-sm border border-l-0 border-gray-300 rounded-r-md bg-gray-100 hover:bg-gray-200"
                title="Clear targets">
                ✕
              </button>
            </div>
            <div class="pk-hint">Comma-separated list. Leave empty to copy to ALL pipes (except reference).</div>
          </div>

          <!-- Exclude checkbox -->
          <div class="mb-3 flex items-center gap-2">
            <input type="checkbox" v-model="excludeMode" class="rounded" id="exclude-check" />
            <label for="exclude-check" class="text-sm cursor-pointer">
              <strong>Exclude mode</strong> — Copy to all pipes EXCEPT those listed
            </label>
          </div>

          <!-- Execute + Cancel -->
          <div class="flex gap-2">
            <button @click="doCopy" class="pk-btn-primary" :disabled="copyLoading.isLoading.value">
              <span v-if="copyLoading.isLoading.value" class="pk-spinner" />
              <Copy class="w-4 h-4" /> Execute Copy
            </button>
            <button @click="router.push('/model')" class="pk-btn-secondary">Cancel</button>
          </div>

        </div>
      </div>
    </div>

    <!-- ── Right sidebar ──────────────────────────────────────── -->
    <div class="w-full lg:w-1/3 space-y-3">

      <!-- Available Pipes -->
      <div class="pk-card">
        <div class="pk-card-header flex items-center gap-1">
          <ListChecks class="w-4 h-4" /> Available Pipes
          <span class="pk-badge-blue ml-2">{{ model.pipes.length }}</span>
        </div>
        <div class="p-0">
          <div class="p-2 border-b">
            <input v-model="pipeFilter" type="text" class="pk-input" placeholder="Filter pipes..." />
          </div>
          <div style="max-height: 400px; overflow-y: auto;">
            <div class="divide-y">
              <button v-for="p in filteredPipes" :key="p" type="button"
                @click="refPipe = p"
                class="w-full text-left px-3 py-1.5 flex items-center gap-2 hover:bg-gray-50 text-sm border-b last:border-b-0">
                <FileText class="w-3 h-3 text-gray-400 flex-shrink-0" /> {{ p }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- How to Use -->
      <div class="pk-card">
        <div class="pk-card-header flex items-center gap-1">
          <Lightbulb class="w-4 h-4" /> How to Use
        </div>
        <div class="p-4 text-sm text-gray-500">
          <ol class="pl-4 space-y-1 mb-0">
            <li>Select a <strong>Reference pipe</strong> (source of fluid properties)</li>
            <li>Select <strong>Target pipes</strong> or leave empty for ALL</li>
            <li>Check <strong>Exclude</strong> to copy to all EXCEPT listed pipes</li>
            <li>Click <strong>Execute Copy</strong></li>
          </ol>
        </div>
      </div>

      <!-- Examples -->
      <div class="pk-card">
        <div class="pk-card-header flex items-center gap-1">
          <Lightbulb class="w-4 h-4" /> Examples
        </div>
        <div class="p-4 text-sm text-gray-500">
          <p class="mb-1"><strong>Ref:</strong> L1, <strong>Targets:</strong> L2,L3</p>
          <p class="mb-2">→ Copy L1 fluid to L2,L3</p>
          <p class="mb-1"><strong>Ref:</strong> L1, <strong>Targets:</strong> (empty)</p>
          <p class="mb-2">→ Copy L1 fluid to ALL pipes</p>
          <p class="mb-1"><strong>Ref:</strong> L1, <strong>Targets:</strong> L2, <strong>Exclude:</strong> ✓</p>
          <p class="mb-0">→ Copy to all pipes EXCEPT L2</p>
        </div>
      </div>
    </div>
  </div>
</template>
