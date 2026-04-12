<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '../stores/session'
import { useModelStore } from '../stores/model'
import { useToastStore } from '../composables/useToast'
import { useLoading } from '../composables/useLoading'
import { api } from '../api/client'
import { FileSpreadsheet, FolderOpen, FileText, Folder, Clipboard, ArrowUpRight, ArrowDownRight, AlertTriangle, Layers } from 'lucide-vue-next'
import PathBrowser from '../components/PathBrowser.vue'

const router = useRouter()
const session = useSessionStore()
const model = useModelStore()
const toast = useToastStore()

const reportPath = ref('')
const exportPath = ref('')
const importPath = ref('')
const batchFolder = ref('')
const showReportBrowser = ref(false)
const showExportBrowser = ref(false)
const showImportBrowser = ref(false)
const showBatchBrowser = ref(false)

const genLoading = useLoading(async () => {
  await api.post('/api/report/generate', {
    report_path: reportPath.value || null,
  })
})

const exportLoading = useLoading(async () => {
  await api.post('/api/report/export', {
    file_path: exportPath.value || null,
  })
})

const importLoading = useLoading(async () => {
  await api.post('/api/report/import', {
    file_path: importPath.value || null,
  })
  await session.fetchStatus()
  await model.fetchSummary()
})

const batchLoading = useLoading(async () => {
  await api.post('/api/report/batch', {
    batch_folder: batchFolder.value || null,
  })
})

async function generate() {
  try {
    await genLoading.execute()
    toast.success('Report generated successfully.')
  } catch (err: any) {
    toast.error(err.response?.data?.detail || err.message || 'An unexpected error occurred.')
  }
}

async function doExport() {
  try {
    await exportLoading.execute()
    toast.success('Model exported to Excel.')
  } catch (err: any) {
    toast.error(err.response?.data?.detail || err.message || 'An unexpected error occurred.')
  }
}

async function doImport() {
  try {
    await importLoading.execute()
    toast.success('Parameters imported from Excel.')
  } catch (err: any) {
    toast.error(err.response?.data?.detail || err.message || 'An unexpected error occurred.')
  }
}

async function doBatch() {
  try {
    await batchLoading.execute()
    toast.success('Batch report generated.')
  } catch (err: any) {
    toast.error(err.response?.data?.detail || err.message || 'An unexpected error occurred.')
  }
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text)
  toast.info('Path copied to clipboard.')
}

onMounted(() => {
  if (!session.isLoaded) router.push('/')
})
</script>

<template>
  <div class="space-y-4">

    <!-- Top row: Generate Report + Batch Report -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">

      <!-- Generate Report -->
      <div class="pk-card h-full flex flex-col">
        <div class="pk-card-header flex items-center gap-1">
          <FileText class="w-4 h-4 text-green-600" /> Generate Report
        </div>
        <div class="p-4 flex flex-col flex-1">
          <div class="mb-3 flex-1">
            <label class="pk-label">Output File</label>
            <div class="flex">
              <span class="flex items-center justify-center px-3 py-1.5 text-sm bg-gray-100 border border-r-0 border-gray-300 rounded-l-md">
                <FileText class="w-4 h-4 text-gray-500" />
              </span>
              <textarea v-model="reportPath" class="pk-input-mono resize-none rounded-none" rows="3"
                style="font-size: 0.82rem;" readonly />
              <button type="button" @click="copyToClipboard(reportPath)"
                class="flex items-center justify-center px-3 py-1.5 text-sm border border-l-0 border-gray-300 rounded-r-md bg-gray-100 hover:bg-gray-50" title="Copy path">
                <Clipboard class="w-4 h-4" />
              </button>
            </div>
            <div class="pk-hint">Auto-derived from the open KDF file.</div>
          </div>
          <button @click="generate" class="w-full bg-green-600 text-white rounded py-1.5 text-sm hover:bg-green-700 flex items-center justify-center gap-1 disabled:opacity-50"
            :disabled="genLoading.isLoading.value">
            <span v-if="genLoading.isLoading.value" class="pk-spinner" />
            <ArrowDownRight class="w-4 h-4" /> Generate Report
          </button>
        </div>
      </div>

      <!-- Batch Report -->
      <div class="pk-card h-full flex flex-col">
        <div class="pk-card-header flex items-center gap-1">
          <Layers class="w-4 h-4 text-gray-500" /> Batch Report
        </div>
        <div class="p-4 flex flex-col flex-1">
          <div class="mb-3 flex-1">
            <label class="pk-label">KDF Folder</label>
            <div class="flex">
              <span class="flex items-center justify-center px-3 py-1.5 text-sm bg-gray-100 border border-r-0 border-gray-300 rounded-l-md">
                <Folder class="w-4 h-4 text-gray-500" />
              </span>
              <textarea v-model="batchFolder" class="pk-input-mono resize-none rounded-none" rows="3"
                placeholder="Folder containing .kdf files" style="font-size: 0.82rem;" />
              <button type="button" @click="showBatchBrowser = true"
                class="flex items-center justify-center px-3 py-1.5 text-sm border border-l-0 border-gray-300 rounded-r-md bg-gray-100 hover:bg-gray-50" title="Browse folder">
                <FolderOpen class="w-4 h-4" />
              </button>
            </div>
            <div class="pk-hint">
              All <code class="bg-gray-100 rounded px-1">.kdf</code> files in this folder will be processed into a combined report.
            </div>
          </div>
          <button @click="doBatch" class="w-full bg-gray-500 text-white rounded py-1.5 text-sm hover:bg-gray-600 flex items-center justify-center gap-1 disabled:opacity-50"
            :disabled="batchLoading.isLoading.value">
            <span v-if="batchLoading.isLoading.value" class="pk-spinner" />
            <Layers class="w-4 h-4" /> Generate Batch Report
          </button>
        </div>
      </div>
    </div>

    <!-- Bottom row: Export + Import -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">

      <!-- Export to Excel -->
      <div class="pk-card h-full flex flex-col">
        <div class="pk-card-header flex items-center gap-1">
          <ArrowUpRight class="w-4 h-4 text-blue-600" /> Export to Excel
        </div>
        <div class="p-4 flex flex-col flex-1">
          <div class="mb-3 flex-1">
            <label class="pk-label">Output Excel File</label>
            <div class="flex">
              <span class="flex items-center justify-center px-3 py-1.5 text-sm bg-gray-100 border border-r-0 border-gray-300 rounded-l-md">
                <FileSpreadsheet class="w-4 h-4 text-gray-500" />
              </span>
              <textarea v-model="exportPath" class="pk-input-mono resize-none rounded-none" rows="3"
                style="font-size: 0.82rem;" readonly />
              <button type="button" @click="copyToClipboard(exportPath)"
                class="flex items-center justify-center px-3 py-1.5 text-sm border border-l-0 border-gray-300 rounded-r-md bg-gray-100 hover:bg-gray-50" title="Copy path">
                <Clipboard class="w-4 h-4" />
              </button>
            </div>
            <div class="pk-hint">Auto-derived from the open KDF file.</div>
          </div>
          <button @click="doExport" class="w-full bg-blue-600 text-white rounded py-1.5 text-sm hover:bg-blue-700 flex items-center justify-center gap-1 disabled:opacity-50"
            :disabled="exportLoading.isLoading.value">
            <span v-if="exportLoading.isLoading.value" class="pk-spinner" />
            <ArrowDownRight class="w-4 h-4" /> Export to Excel
          </button>
        </div>
      </div>

      <!-- Import from Excel -->
      <div class="pk-card h-full flex flex-col">
        <div class="pk-card-header flex items-center gap-1">
          <ArrowDownRight class="w-4 h-4 text-yellow-500" /> Import from Excel
        </div>
        <div class="p-4 flex flex-col flex-1">
          <div class="mb-3 flex-1">
            <label class="pk-label">Source Excel File</label>
            <div class="flex">
              <span class="flex items-center justify-center px-3 py-1.5 text-sm bg-gray-100 border border-r-0 border-gray-300 rounded-l-md">
                <FileSpreadsheet class="w-4 h-4 text-gray-500" />
              </span>
              <textarea v-model="importPath" class="pk-input-mono resize-none rounded-none" rows="3"
                placeholder="Paste path to exported Excel file" style="font-size: 0.82rem;" />
              <button type="button" @click="showImportBrowser = true"
                class="flex items-center justify-center px-3 py-1.5 text-sm border border-l-0 border-gray-300 rounded-r-md bg-gray-100 hover:bg-gray-50" title="Browse">
                <FolderOpen class="w-4 h-4" />
              </button>
            </div>
            <div class="pk-hint">Export the model first, then paste or type the path here.</div>
          </div>
          <div class="bg-yellow-50 border border-yellow-200 rounded px-3 py-2 mb-3 flex items-center gap-2 text-xs text-yellow-700">
            <AlertTriangle class="w-4 h-4 flex-shrink-0" />
            Import overwrites the in-memory model. Save a backup first.
          </div>
          <div class="flex gap-2">
            <button @click="doImport" class="flex-1 bg-yellow-500 text-white rounded py-1.5 text-sm hover:bg-yellow-600 flex items-center justify-center gap-1 disabled:opacity-50"
              :disabled="importLoading.isLoading.value">
              <span v-if="importLoading.isLoading.value" class="pk-spinner" />
              <ArrowDownRight class="w-4 h-4" /> Import from Excel
            </button>
            <button @click="router.push('/model')" class="pk-btn-secondary">Cancel</button>
          </div>
        </div>
      </div>
    </div>

  </div>

  <PathBrowser v-if="showReportBrowser" filter="any"
    @close="showReportBrowser = false"
    @select="(p: string) => { reportPath = p; showReportBrowser = false }" />
  <PathBrowser v-if="showExportBrowser" filter="excel"
    @close="showExportBrowser = false"
    @select="(p: string) => { exportPath = p; showExportBrowser = false }" />
  <PathBrowser v-if="showImportBrowser" filter="excel"
    @close="showImportBrowser = false"
    @select="(p: string) => { importPath = p; showImportBrowser = false }" />
  <PathBrowser v-if="showBatchBrowser" filter="folder"
    @close="showBatchBrowser = false"
    @select="(p: string) => { batchFolder = p; showBatchBrowser = false }" />
</template>
