<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '../stores/session'
import { useModelStore } from '../stores/model'
import { useToastStore } from '../composables/useToast'
import { useLoading } from '../composables/useLoading'
import { api } from '../api/client'
import { FolderOpen, Upload, Wrench, Thermometer, Lightbulb, FileSpreadsheet, ArrowLeft } from 'lucide-vue-next'
import PathBrowser from '../components/PathBrowser.vue'

const router = useRouter()
const session = useSessionStore()
const model = useModelStore()
const toast = useToastStore()

const pmsSource = ref('')
const hmbSource = ref('')
const showPmsBrowser = ref(false)
const showHmbBrowser = ref(false)

const pmsLoading = useLoading(async () => {
  await api.post('/api/data/apply-pms', {
    pms_source: pmsSource.value,
  })
  await session.fetchStatus()
  await model.fetchSummary()
})

const hmbLoading = useLoading(async () => {
  await api.post('/api/data/apply-hmb', {
    hmb_source: hmbSource.value,
  })
  await session.fetchStatus()
  await model.fetchSummary()
})

async function applyPms() {
  if (!pmsSource.value.trim()) {
    toast.error('Please enter a PMS source file path.')
    return
  }
  try {
    await pmsLoading.execute()
    toast.success('PMS data applied successfully.')
  } catch (err: any) {
    toast.error(err.response?.data?.detail || err.message || 'Failed to apply PMS.')
  }
}

async function applyHmb() {
  if (!hmbSource.value.trim()) {
    toast.error('Please enter an HMB source file path.')
    return
  }
  try {
    await hmbLoading.execute()
    toast.success('HMB data applied successfully.')
  } catch (err: any) {
    toast.error(err.response?.data?.detail || err.message || 'Failed to apply HMB.')
  }
}

onMounted(() => {
  if (!session.isLoaded) router.push('/')
  if (model.prereqs?.pms_path) {
    pmsSource.value = model.prereqs.pms_path
  }
})
</script>

<template>
  <div class="flex gap-4 flex-wrap lg:flex-nowrap">

    <!-- ── Left: Form card ────────────────────────────────── -->
    <div class="w-full lg:w-2/3">
      <div class="pk-card">
        <div class="pk-card-header flex items-center gap-2">
          <Upload class="w-4 h-4 text-cyan-500" /> Apply PMS / HMB Data
        </div>
        <div class="pk-card-body">

          <!-- PMS Section -->
          <div class="mb-4 p-4 rounded-lg bg-gray-50">
            <div class="flex items-center gap-2 mb-3">
              <Wrench class="w-5 h-5 text-cyan-600" />
              <h4 class="font-semibold text-base text-gray-800">PMS Data</h4>
            </div>
            <div class="mb-3">
              <label class="pk-label">PMS Excel File</label>
              <div class="flex">
                <span class="flex items-center justify-center px-3 py-1.5 text-sm bg-gray-100 border border-r-0 border-gray-300 rounded-l-md">
                  <FileSpreadsheet class="w-4 h-4 text-gray-500" />
                </span>
                <textarea v-model="pmsSource" class="pk-input-mono resize-none rounded-none"
                  rows="2" placeholder="C:/config/pms_data.xlsx" />
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

          <!-- HMB Section -->
          <div class="p-4 rounded-lg bg-gray-50">
            <div class="flex items-center gap-2 mb-3">
              <Thermometer class="w-5 h-5 text-red-600" />
              <h4 class="font-semibold text-base text-gray-800">HMB Data</h4>
            </div>
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

          <!-- Cancel button -->
          <div class="mt-4 pt-3 border-t">
            <button @click="router.push('/model')" class="pk-btn-secondary flex items-center gap-1">
              <ArrowLeft class="w-4 h-4" /> Back to Menu
            </button>
          </div>

        </div>
      </div>
    </div>

    <!-- ── Right sidebar ────────────────────────────────────── -->
    <div class="w-full lg:w-1/3 space-y-3">

      <!-- About PMS -->
      <div class="pk-card">
        <div class="pk-card-header flex items-center gap-1">
          <Lightbulb class="w-4 h-4" /> About PMS
        </div>
        <div class="p-4 text-sm text-gray-500">
          <p class="mb-1">PMS applies pipe schedule, wall thickness, and material to all matching pipes.</p>
          <p class="mb-0">Pipe names are matched against the PMS lookup table from Excel.</p>
        </div>
      </div>

      <!-- About HMB -->
      <div class="pk-card">
        <div class="pk-card-header flex items-center gap-1">
          <Lightbulb class="w-4 h-4" /> About HMB
        </div>
        <div class="p-4 text-sm text-gray-500">
          <p class="mb-1">HMB applies fluid temperature and pressure from process stream tables to matching pipes.</p>
          <p class="mb-0">Stream numbers are extracted from each pipe's <code class="bg-gray-100 rounded px-1">NOTES</code> field and looked up in the HMB table.</p>
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
/* No page-specific styles — all pk-* classes defined in global style.css */
</style>


