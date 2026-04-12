<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '../stores/session'
import { useModelStore } from '../stores/model'
import { useToastStore } from '../composables/useToast'
import { useLoading } from '../composables/useLoading'
import {
  Sliders, ClipboardCopy, FileSpreadsheet, Ruler, BookMarked,
  CheckCircle, XCircle, AlertCircle, FolderOpen, Lightbulb,
  BarChart3, Grid3X3, PenSquare, X, Upload,
} from 'lucide-vue-next'
import type { ProjectInfo } from '../types/api'

const router = useRouter()
const session = useSessionStore()
const model = useModelStore()
const toast = useToastStore()

const showProjectModal = ref(false)
const editInfo = ref<ProjectInfo>({
  company1: '', company2: '',
  project_name1: '', project_name2: '',
  item_name1: '', item_name2: '',
  prepared_by: '', checked_by: '', approved_by: '',
  date: '', project_no: '', revision: '',
})

function openProjectModal() {
  if (model.projectInfo) {
    editInfo.value = { ...model.projectInfo }
  }
  showProjectModal.value = true
}

const saveProjectLoading = useLoading(async () => {
  await model.saveProjectInfo(editInfo.value)
  showProjectModal.value = false
  toast.success('Project info saved.')
})

// Summary items with icons and labels
const summaryItems = [
  { key: 'num_pipes', label: 'Pipes', icon: 'pipe' },
  { key: 'num_junctions', label: 'Junctions', icon: 'node' },
  { key: 'num_pumps', label: 'Pumps', icon: 'gear' },
  { key: 'num_valves', label: 'Valves', icon: 'funnel' },
  { key: 'num_feeds', label: 'Feeds', icon: 'down' },
  { key: 'num_products', label: 'Products', icon: 'up' },
]

function getSummaryValue(key: string): number {
  return (model.summary as any)?.[key] ?? 0
}

// Category badge helper for validation issues
function issueBadge(issue: string): { label: string; cls: string } {
  if (issue.includes('NOTES') || issue.toLowerCase().includes('line number'))
    return { label: 'NOTES', cls: 'bg-yellow-100 text-yellow-700' }
  if (issue.includes('NAME'))
    return { label: 'NAME', cls: 'bg-gray-200 text-gray-700' }
  if (issue.includes('CONN'))
    return { label: 'CONN', cls: 'bg-blue-100 text-blue-700' }
  if (issue.includes('VALUE'))
    return { label: 'VALUE', cls: 'bg-gray-200 text-gray-700' }
  if (issue.includes('LAYOUT'))
    return { label: 'LAYOUT', cls: 'bg-gray-200 text-gray-700' }
  if (issue.includes('REQUIRED'))
    return { label: 'REQUIRED', cls: 'bg-red-100 text-red-700' }
  return { label: 'INFO', cls: 'bg-gray-200 text-gray-700' }
}

onMounted(async () => {
  if (!session.isLoaded) {
    router.push('/')
    return
  }
  await model.fetchSummary()
})
</script>

<template>
  <div v-if="model.summary" class="flex gap-4 flex-wrap lg:flex-nowrap">

    <!-- ── Left sidebar ────────────────────────────────────────── -->
    <div class="w-full lg:w-1/4 space-y-3">

      <!-- Project Info Card -->
      <div class="pk-card">
        <div class="px-3 py-2 border-b flex justify-between items-center" style="background: transparent;">
          <span class="font-semibold text-xs flex items-center gap-1 text-blue-600">
            <FolderOpen class="w-3.5 h-3.5" /> Project Info
          </span>
          <button type="button" @click="openProjectModal"
            class="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-0.5">
            <PenSquare class="w-3 h-3" /> Edit
          </button>
        </div>
        <table v-if="model.projectInfo" class="w-full text-xs border-0 mb-0">
          <tbody>
            <tr>
              <td class="text-gray-500 pl-3 py-1" style="width: 40%; white-space: nowrap;">Company</td>
              <td class="font-medium pr-3 py-1">
                {{ model.projectInfo.company1 }}
                <span v-if="model.projectInfo.company2" class="text-gray-400">/</span>
                <span v-if="model.projectInfo.company2">{{ model.projectInfo.company2 }}</span>
              </td>
            </tr>
            <tr>
              <td class="text-gray-500 pl-3 py-1">Project</td>
              <td class="font-medium pr-3 py-1">{{ model.projectInfo.project_name1 }}</td>
            </tr>
            <tr>
              <td class="text-gray-500 pl-3 py-1">Document No</td>
              <td class="font-medium pr-3 py-1">{{ model.projectInfo.item_name1 }}</td>
            </tr>
            <tr>
              <td class="text-gray-500 pl-3 py-1">Item / Tag</td>
              <td class="font-medium pr-3 py-1">{{ model.projectInfo.item_name2 }}</td>
            </tr>
            <tr>
              <td class="text-gray-500 pl-3 py-1">Prepared By</td>
              <td class="font-medium pr-3 py-1">{{ model.projectInfo.prepared_by }}</td>
            </tr>
            <tr>
              <td class="text-gray-500 pl-3 py-1">Date</td>
              <td class="font-medium pr-3 py-1">{{ model.projectInfo.date }}</td>
            </tr>
            <tr>
              <td class="text-gray-500 pl-3 py-1">Revision</td>
              <td class="font-medium pr-3 py-1">{{ model.projectInfo.revision }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Project Info Edit Modal -->
      <div v-if="showProjectModal" class="pk-modal-backdrop">
        <div class="pk-modal">
          <div class="pk-modal-header">
            <h6 class="font-semibold flex items-center gap-1 text-blue-600">
              <FolderOpen class="w-4 h-4" /> Edit Project Info
            </h6>
            <button @click="showProjectModal = false" class="text-gray-400 hover:text-gray-600">
              <X class="w-4 h-4" />
            </button>
          </div>
          <div class="p-4 space-y-2 overflow-auto">
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="pk-label-sm">Company</label>
                <input v-model="editInfo.company1" type="text" class="pk-input"
                  :placeholder="model.smartDefaults?.company1 || ''" />
              </div>
              <div>
                <label class="pk-label-sm">Company 2</label>
                <input v-model="editInfo.company2" type="text" class="pk-input"
                  :placeholder="model.smartDefaults?.company2 || ''" />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="pk-label-sm">Project Name</label>
                <input v-model="editInfo.project_name1" type="text" class="pk-input"
                  :placeholder="model.smartDefaults?.project_name1 || ''" />
              </div>
              <div>
                <label class="pk-label-sm">Project Name 2</label>
                <input v-model="editInfo.project_name2" type="text" class="pk-input"
                  :placeholder="model.smartDefaults?.project_name2 || ''" />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="pk-label-sm">Document No</label>
                <input v-model="editInfo.item_name1" type="text" class="pk-input"
                  :placeholder="model.smartDefaults?.item_name1 || ''" />
              </div>
              <div>
                <label class="pk-label-sm">Item / Tag</label>
                <input v-model="editInfo.item_name2" type="text" class="pk-input"
                  :placeholder="model.smartDefaults?.item_name2 || ''" />
              </div>
            </div>
            <div class="grid grid-cols-3 gap-2">
              <div>
                <label class="pk-label-sm">Prepared</label>
                <input v-model="editInfo.prepared_by" type="text" class="pk-input"
                  :placeholder="model.smartDefaults?.prepared_by || ''" />
              </div>
              <div>
                <label class="pk-label-sm">Checked</label>
                <input v-model="editInfo.checked_by" type="text" class="pk-input"
                  :placeholder="model.smartDefaults?.checked_by || ''" />
              </div>
              <div>
                <label class="pk-label-sm">Approved</label>
                <input v-model="editInfo.approved_by" type="text" class="pk-input"
                  :placeholder="model.smartDefaults?.approved_by || ''" />
              </div>
            </div>
            <div class="grid grid-cols-3 gap-2">
              <div>
                <label class="pk-label-sm">Date</label>
                <input v-model="editInfo.date" type="text" class="pk-input"
                  :placeholder="model.smartDefaults?.date || ''" />
              </div>
              <div>
                <label class="pk-label-sm">Project No</label>
                <input v-model="editInfo.project_no" type="text" class="pk-input"
                  :placeholder="model.smartDefaults?.project_no || ''" />
              </div>
              <div>
                <label class="pk-label-sm">Rev</label>
                <input v-model="editInfo.revision" type="text" class="pk-input"
                  :placeholder="model.smartDefaults?.revision || ''" />
              </div>
            </div>
          </div>
          <div class="px-4 py-2 border-t flex justify-end gap-2">
            <button @click="showProjectModal = false" class="pk-btn-secondary">Cancel</button>
            <button @click="saveProjectLoading.execute()"
              class="pk-btn-primary" :disabled="saveProjectLoading.isLoading.value">
              <span v-if="saveProjectLoading.isLoading.value" class="pk-spinner" />
              Save
            </button>
          </div>
        </div>
      </div>

      <!-- Model Summary Card -->
      <div class="pk-card">
        <div class="pk-card-header flex items-center gap-1">
          <BarChart3 class="w-4 h-4 text-blue-600" /> Model Summary
        </div>
        <ul class="divide-y">
          <li v-for="item in summaryItems" :key="item.key"
            class="flex justify-between items-center px-3 py-1.5">
            <span class="text-sm text-gray-600">{{ item.label }}</span>
            <span class="pk-badge-blue">{{ getSummaryValue(item.key) }}</span>
          </li>
        </ul>
      </div>

      <!-- How to Use -->
      <div class="pk-card">
        <div class="pk-card-header flex items-center gap-1">
          <Lightbulb class="w-4 h-4" /> How to Use
        </div>
        <div class="p-4 text-sm text-gray-500">
          <ol class="pl-4 space-y-1 mb-0">
            <li>Apply <strong>Data</strong> (PMS / HMB) to populate pipe specs and fluid data.</li>
            <li>Use <strong>Global Parameters</strong> to set sizing criteria and dummy pipes.</li>
            <li>Generate a <strong>Report</strong> or export to Excel for review.</li>
          </ol>
        </div>
      </div>
    </div>

    <!-- ── Right column ─────────────────────────────────────────── -->
    <div class="flex-1 space-y-4">
      <h2 class="text-lg font-bold flex items-center gap-1">
        <Grid3X3 class="w-5 h-5 text-blue-600" /> Operations
      </h2>

      <!-- Operations grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
        <router-link to="/model/settings" class="no-underline">
          <div class="pk-card border-2 border-gray-200 hover:border-blue-400 p-3 h-full setting-card">
            <div class="card-body">
              <h5 class="font-semibold flex items-center gap-2"><Sliders class="w-4 h-4 text-yellow-500" /> Global Parameters</h5>
              <p class="text-xs text-gray-500 mt-1">Apply bulk modifications to KORF model based Project Criteria.</p>
            </div>
          </div>
        </router-link>
        <router-link to="/model/data" class="no-underline">
          <div class="pk-card border-2 border-gray-200 hover:border-blue-400 p-3 h-full setting-card">
            <h5 class="font-semibold flex items-center gap-2"><Upload class="w-4 h-4 text-cyan-500" /> Apply Data</h5>
            <p class="text-xs text-gray-500 mt-1">Apply PMS (pipe specs) and HMB (stream data) from Excel files.</p>
          </div>
        </router-link>
        <router-link to="/model/bulk-copy" class="no-underline">
          <div class="pk-card border-2 border-gray-200 hover:border-blue-400 p-3 h-full setting-card">
            <h5 class="font-semibold flex items-center gap-2"><ClipboardCopy class="w-4 h-4 text-blue-600" /> Bulk Copy Fluids</h5>
            <p class="text-xs text-gray-500 mt-1">Copy fluid properties from one pipe to multiple others. Supports include/exclude modes.</p>
          </div>
        </router-link>
        <router-link to="/model/report" class="no-underline">
          <div class="pk-card border-2 border-gray-200 hover:border-blue-400 p-3 h-full setting-card">
            <h5 class="font-semibold flex items-center gap-2"><FileSpreadsheet class="w-4 h-4 text-green-600" /> Reports</h5>
            <p class="text-xs text-gray-500 mt-1">Generate reports, export to Excel, or import edited parameters back.</p>
          </div>
        </router-link>
        <router-link to="/model/pipe-criteria" class="no-underline">
          <div class="pk-card border-2 border-gray-200 hover:border-blue-400 p-3 h-full setting-card">
            <h5 class="font-semibold flex items-center gap-2"><Ruler class="w-4 h-4 text-blue-600" /> Pipe Sizing Criteria</h5>
            <p class="text-xs text-gray-500 mt-1">Assign fluid state and sizing criteria code to each pipe.</p>
          </div>
        </router-link>
        <router-link to="/model/references" class="no-underline">
          <div class="pk-card border-2 border-gray-200 hover:border-blue-400 p-3 h-full setting-card">
            <h5 class="font-semibold flex items-center gap-2"><BookMarked class="w-4 h-4 text-blue-600" /> References</h5>
            <p class="text-xs text-gray-500 mt-1">Design basis notes, SharePoint links and reference documents. Shortcuts auto-created next to the KDF.</p>
          </div>
        </router-link>
      </div>

      <!-- Prerequisites & Validation -->
      <div v-if="model.prereqs" class="grid grid-cols-1 md:grid-cols-2 gap-3 mt-2">

        <!-- Pre-requisites -->
        <div class="pk-card h-full">
          <div class="pk-card-header flex items-center gap-1">
            <CheckCircle class="w-4 h-4 text-blue-600" /> Pre-requisites
          </div>
          <ul class="divide-y">
            <li class="flex items-start gap-3 py-3 px-3">
              <CheckCircle v-if="model.prereqs.notes_ok" class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
              <XCircle v-else class="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
              <div class="min-w-0">
                <div class="font-semibold text-sm">Line number in Notes</div>
                <div class="text-xs text-gray-500">Every pipe must have a valid line number in its <strong>NOTES</strong> field in KORF.</div>
              </div>
            </li>
            <li class="flex items-start gap-3 py-3 px-3">
              <CheckCircle v-if="model.prereqs.pms_ok" class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
              <XCircle v-else class="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
              <div class="min-w-0">
                <div class="font-semibold text-sm">
                  PMS Excel file configured
                  <router-link to="/model/data" class="text-blue-600 text-xs ml-1">(Data tab)</router-link>
                </div>
                <div v-if="model.prereqs.pms_path" class="font-mono text-xs text-gray-400 truncate" :title="model.prereqs.pms_path">
                  {{ model.prereqs.pms_path.split(/[\/\\]/).pop() }}
                </div>
                <div v-else class="text-xs text-gray-500">No PMS file set — go to <router-link to="/model/data" class="text-blue-600">Data</router-link> tab.</div>
              </div>
            </li>
            <li class="flex items-start gap-3 py-3 px-3">
              <CheckCircle v-if="model.prereqs.validation_ok" class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
              <XCircle v-else class="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
              <div>
                <div class="font-semibold text-sm">No validation errors</div>
                <div class="text-xs text-gray-500">
                  {{ model.prereqs.validation_ok ? 'All checks passed.' : `${model.prereqs.issues.length} issue(s) found — see validation panel.` }}
                </div>
              </div>
            </li>
            <li class="flex items-start gap-3 py-3 px-3">
              <CheckCircle v-if="model.prereqs.sharepoint_ok" class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
              <AlertCircle v-else class="w-5 h-5 text-yellow-500 mt-0.5 flex-shrink-0" />
              <div>
                <div class="font-semibold text-sm">
                  Local &amp; SharePoint path configured
                  <router-link to="/preferences" class="text-blue-600 text-xs ml-1">(Preferences)</router-link>
                </div>
                <div class="text-xs text-gray-500">
                  {{ model.prereqs.sharepoint_ok ? 'Override mapping is set.' : 'Optional — recommended for shared OneDrive paths.' }}
                </div>
              </div>
            </li>
          </ul>
        </div>

        <!-- Validation Results -->
        <div class="pk-card h-full flex flex-col">
          <div class="pk-card-header flex items-center gap-1">
            <CheckCircle v-if="model.prereqs.validation_ok" class="w-4 h-4 text-green-500" />
            <XCircle v-else class="w-4 h-4 text-red-500" />
            Validation Results
            <span v-if="model.prereqs.validation_ok" class="ml-auto bg-green-500 text-white text-xs px-2 py-0.5 rounded">PASSED</span>
            <span v-else class="ml-auto bg-red-500 text-white text-xs px-2 py-0.5 rounded">{{ model.prereqs.issues.length }} issue(s)</span>
          </div>
          <div class="flex-1">
            <div v-if="model.prereqs.validation_ok" class="text-center text-green-500 py-4 flex flex-col items-center justify-center h-full">
              <CheckCircle class="w-10 h-10" />
              <div class="mt-2 font-semibold">All validations passed</div>
            </div>
            <template v-else>
              <ul class="divide-y overflow-auto" style="max-height: 280px;">
                <li v-for="issue in model.prereqs.issues" :key="issue" class="px-3 py-2 text-xs">
                  <span class="text-xs px-1.5 py-0.5 rounded mr-1" :class="issueBadge(issue).cls">{{ issueBadge(issue).label }}</span>
                  {{ issue }}
                </li>
              </ul>
            </template>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* Setting card hover */
.setting-card {
  transition: border-color 0.15s ease;
}
.no-underline {
  text-decoration: none;
  color: inherit;
}
</style>
