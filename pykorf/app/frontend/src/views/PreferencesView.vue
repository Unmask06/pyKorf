<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { usePreferencesStore } from '../stores/preferences'
import { useToastStore } from '../composables/useToast'
import { useLoading } from '../composables/useLoading'
import { Plus, Trash2, Loader, FolderOpen, Database, Key, CloudCheck, CloudOff, PenSquare, Info, Lock, Save, RotateCw, Clock, ExternalLink, AlertTriangle, FileSpreadsheet } from 'lucide-vue-next'
import PathBrowser from '../components/PathBrowser.vue'
import type { DocRegisterRebuildResponse } from '../types/api'

const prefs = usePreferencesStore()
const toast = useToastStore()

// SP Override form
const newLocalPath = ref('')
const newSpUrl = ref('')
const editOriginalPath = ref<string | null>(null)
const showOverrideBrowser = ref(false)
const spConfirmCheck = ref(false)

// Doc Register
const docExcelPath = ref('')
const docSpSiteUrl = ref('')
const showDocExcelBrowser = ref(false)
const rebuildResult = ref<DocRegisterRebuildResponse | null>(null)

// Show SP Open link when URL starts with http
const showSpOpenLink = computed(() => newSpUrl.value.trim().startsWith('http'))

function openSpUrl() {
  const url = newSpUrl.value.trim()
  if (url.startsWith('http')) {
    window.open(url, '_blank', 'noopener,noreferrer')
  }
}

// Can add override?
const canAddOverride = computed(() =>
  newLocalPath.value.trim() !== '' &&
  newSpUrl.value.trim() !== '' &&
  newSpUrl.value.trim().startsWith('http') &&
  spConfirmCheck.value
)

// Add/Edit SP override
async function addOverride() {
  if (!newLocalPath.value || !newSpUrl.value) {
    toast.error('Both local path and SharePoint URL are required.')
    return
  }
  const result = await prefs.addOverride(newLocalPath.value, newSpUrl.value) as any
  if (result.success) {
    newLocalPath.value = ''
    newSpUrl.value = ''
    spConfirmCheck.value = false
    editOriginalPath.value = null
    toast.success('Override added.')
  } else {
    toast.error(result.error || 'Failed to add override.')
  }
}

function editOverride(localPath: string, spUrl: string) {
  editOriginalPath.value = localPath
  newLocalPath.value = localPath
  newSpUrl.value = spUrl
}

async function saveOverride() {
  if (!editOriginalPath.value) return
  const result = await prefs.editOverride(editOriginalPath.value, newLocalPath.value, newSpUrl.value)
  if (result.success) {
    editOriginalPath.value = null
    newLocalPath.value = ''
    newSpUrl.value = ''
    spConfirmCheck.value = false
    toast.success('Override updated.')
  }
}

async function deleteOverride(localPath: string) {
  const result = await prefs.deleteOverride(localPath) as any
  if (result.success) toast.info('Override removed.')
  else toast.error(result.error || 'Failed to remove.')
}

function cancelEdit() {
  editOriginalPath.value = null
  newLocalPath.value = ''
  newSpUrl.value = ''
  spConfirmCheck.value = false
}

async function toggleSkipSp() {
  await prefs.setSkipSp(!prefs.skipSpOverride)
  toast.info(prefs.skipSpOverride ? 'SP override check skipped.' : 'SP override check enabled.')
}

// Doc Register config
const docConfigLoading = useLoading(async () => {
  await prefs.setDocRegisterConfig({
    excel_path: docExcelPath.value || null,
    sp_site_url: docSpSiteUrl.value || null,
  })
  toast.info('Document Register config saved.')
  rebuildResult.value = null
})

// Rebuild DB
const rebuildLoading = useLoading(async () => {
  const result = await prefs.rebuildDocRegisterDb()
  rebuildResult.value = result
  if (result.success) toast.success(result.message)
  else toast.error(result.error || result.message)
})

onMounted(() => {
  prefs.fetchAll().then(() => {
    docExcelPath.value = prefs.docRegisterExcelPath || ''
    docSpSiteUrl.value = prefs.docRegisterSpSiteUrl || ''
  })
})
</script>

<template>
  <div class="flex gap-4 flex-wrap lg:flex-nowrap">

    <!-- ── SharePoint Path Overrides ────────────────────────── -->
    <div class="w-full lg:w-2/3">
      <div class="pk-card">
        <div class="pk-card-header flex items-center gap-2">
          <CloudCheck class="w-4 h-4 text-blue-600" /> SharePoint Path Overrides
        </div>
        <div class="pk-card-body">

          <!-- Skip SP switch -->
          <div class="mb-3 flex items-center gap-3">
            <input type="checkbox" :checked="prefs.skipSpOverride" @change="toggleSkipSp"
              class="form-check-input" id="skip-sp-check" />
            <label for="skip-sp-check" class="text-sm cursor-pointer">
              Skip SharePoint Override Validation
            </label>
            <small class="text-gray-500 block mt-0.5" style="margin-left: 0;">
              <Info class="w-3 h-3 inline" /> When enabled, you can load models using local paths only. Reference search will be disabled.
            </small>
          </div>

          <!-- Edit mode warning -->
          <div v-if="editOriginalPath" class="pk-alert-warn p-2 mb-3 flex items-center gap-2">
            <PenSquare class="w-4 h-4" />
            <span>Editing existing override — make changes and click <strong>Save</strong>.</span>
            <button @click="cancelEdit" class="pk-btn-sm border ml-auto">Cancel</button>
          </div>

          <!-- Add/Edit form -->
          <form @submit.prevent="editOriginalPath ? saveOverride() : addOverride()" class="mb-4">
            <div class="mb-2">
              <label class="text-xs font-semibold mb-1 block">Local Folder Path</label>
              <div class="flex">
                <span class="flex items-center justify-center px-2 py-1 text-xs bg-gray-100 border border-r-0 border-gray-300 rounded-l-md">
                  <FolderOpen class="w-3.5 h-3.5 text-gray-500" />
                </span>
                <input v-model="newLocalPath" type="text" class="pk-input-mono text-sm rounded-none"
                  placeholder="C:\Users\UserName\OneDrive - CC7\25002 TAZIZ SALT PVC - ADNOC UAE - 2A-PROCESS"
                  required autocomplete="off" />
                <button type="button" @click="showOverrideBrowser = true"
                  class="flex items-center justify-center px-2 py-1 text-xs border border-l-0 border-gray-300 rounded-r-md bg-gray-100 hover:bg-gray-50"
                  title="Browse for local folder">
                  <FolderOpen class="w-3.5 h-3.5" />
                </button>
              </div>
              <div class="pk-hint">The OneDrive-synced local folder root (e.g. the folder shown in Explorer).</div>
            </div>
            <div class="mb-3">
              <label class="text-xs font-semibold mb-1 block">SharePoint URL</label>
              <div class="flex">
                <span class="flex items-center justify-center px-2 py-1 text-xs bg-gray-100 border border-r-0 border-gray-300 rounded-l-md">
                  <CloudCheck class="w-3.5 h-3.5 text-gray-500" />
                </span>
                <input v-model="newSpUrl" type="text" class="pk-input-mono text-sm rounded-none"
                  placeholder="https://cc7ges.sharepoint.com/sites/..."
                  required pattern="https?://.*" autocomplete="off" />
                <button v-if="showSpOpenLink" type="button" @click="openSpUrl"
                  class="flex items-center justify-center px-2 py-1 text-xs border border-l-0 border-blue-300 rounded-r-md bg-blue-50 text-blue-600 hover:bg-blue-100"
                  title="Open SharePoint URL in browser to verify">
                  <ExternalLink class="w-3.5 h-3.5" /> Open
                </button>
              </div>
              <div class="pk-hint">The corresponding SharePoint folder URL. See right for an example.</div>
            </div>

            <!-- Confirmation checkbox -->
            <div class="pk-alert-warn p-2 mb-3">
              <div class="flex items-start gap-2">
                <input type="checkbox" v-model="spConfirmCheck" class="mt-0.5 rounded" id="sp-confirm" />
                <label for="sp-confirm" class="text-xs">
                  <AlertTriangle class="w-3 h-3 inline text-yellow-500" />
                  <strong>I confirm this SharePoint URL works:</strong>
                  I clicked the link button (<ExternalLink class="w-3 h-3 inline" />) to open it in my browser and verified it opens correctly.
                </label>
              </div>
            </div>

            <button type="submit" :disabled="!canAddOverride"
              :class="editOriginalPath ? 'bg-yellow-500 hover:bg-yellow-600' : 'bg-green-600 hover:bg-green-700'"
              class="text-white rounded px-3 py-1 text-sm flex items-center gap-1 disabled:opacity-50">
              <Plus class="w-3.5 h-3.5" />
              {{ editOriginalPath ? 'Save Changes' : 'Add Override' }}
            </button>
          </form>

          <!-- Existing overrides table -->
          <template v-if="Object.keys(prefs.spOverrides).length">
            <div class="overflow-x-auto">
              <table class="pk-table">
                <thead class="bg-gray-800 text-white">
                  <tr>
                    <th class="px-3 py-2 text-left text-sm font-semibold">Local Folder</th>
                    <th class="px-3 py-2 text-left text-sm font-semibold">SharePoint URL</th>
                    <th class="px-3 py-2 text-left text-sm font-semibold" style="width: 6rem;"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(spUrl, localPath) in prefs.spOverrides" :key="localPath"
                    class="hover:bg-gray-50">
                    <td class="font-mono text-xs break-all">{{ localPath }}</td>
                    <td class="font-mono text-xs break-all">
                      <a v-if="spUrl" :href="spUrl as string" target="_blank" rel="noopener"
                        class="text-blue-600 hover:underline" :title="spUrl as string">
                        <ExternalLink class="w-3 h-3 inline mr-1" />{{ spUrl }}
                      </a>
                    </td>
                    <td>
                      <button @click="editOverride(localPath as string, spUrl as string)"
                        class="border border-gray-300 rounded px-1 py-0 mr-1 text-gray-500 hover:text-blue-600 hover:border-blue-300"
                        title="Edit">
                        <PenSquare class="w-3 h-3" />
                      </button>
                      <button @click="deleteOverride(localPath as string)"
                        class="border border-red-200 rounded px-1 py-0 text-red-400 hover:text-red-600 hover:border-red-400"
                        title="Delete">
                        <Trash2 class="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
          <template v-else>
            <div class="text-center text-gray-400 py-4">
              <CloudOff class="w-8 h-8 mx-auto mb-2" />
              No overrides configured. Add one above if SharePoint URLs are resolving incorrectly.
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- ── Right: Example card ───────────────────────────────── -->
    <div class="w-full lg:w-1/3">
      <div class="pk-card">
        <div class="pk-card-header flex items-center gap-1">
          <Lightbulb class="w-4 h-4" /> When to use this
        </div>
        <div class="p-4 text-sm text-gray-500">
          <p class="mb-2">
            OneDrive sometimes syncs a <strong>subfolder</strong> of a SharePoint library but only records the library root URL in Windows. This causes the Browse button to generate an incorrect SharePoint URL missing the intermediate folders.
          </p>
          <p class="mb-1 mt-2"><strong>Example:</strong></p>
          <p class="mb-1 text-gray-500" style="font-size: 0.78rem;">Local folder:</p>
          <code style="font-size: 0.72rem; word-break: break-all;">C:\Users\UserName\OneDrive - CC7\25002 TAZIZ SALT PVC - ADNOC UAE - 2A-PROCESS</code>
          <p class="mt-2 mb-1 text-gray-500" style="font-size: 0.78rem;">SharePoint URL:</p>
          <code style="font-size: 0.72rem; word-break: break-all;">https://cc7ges.sharepoint.com/sites/25002TAZIZSALT-ADNOCUAE/Shared Documents/2 EXECUTION/2. ENG/2A-PROCESS</code>
        </div>
      </div>
    </div>
  </div>

  <!-- ── Document Register (full width) ─────────────────────── -->
  <div class="mt-4">
    <div class="pk-card">
      <div class="pk-card-header flex items-center gap-2">
        <Database class="w-4 h-4 text-cyan-500" /> Document Register
        <span class="ml-auto text-xs px-2 py-0.5 rounded"
          :class="prefs.docRegisterExcelPath ? 'bg-gray-200 text-gray-600' : 'bg-red-100 text-red-600'">
          {{ prefs.docRegisterExcelPath ? 'Configured' : 'Not configured' }}
        </span>
      </div>
      <div class="pk-card-body">
        <div v-if="!prefs.spOverridesConfigured && !prefs.skipSpOverride"
          class="pk-alert-warn p-2 mb-3 flex items-center gap-2">
          <AlertTriangle class="w-4 h-4 flex-shrink-0" />
          <strong>SharePoint Path Overrides Required:</strong>
          You must configure at least one SharePoint path override above before saving Document Register config.
          This enables automatic conversion of SharePoint URLs to local paths.
        </div>

        <form @submit.prevent="docConfigLoading.execute()" class="flex flex-wrap gap-2 items-start">
          <div class="flex-1" style="min-width: 250px;">
            <label class="text-xs font-semibold mb-1 block">Excel File Path</label>
            <div class="flex">
              <span class="flex items-center justify-center px-2 py-1 text-xs bg-gray-100 border border-r-0 border-gray-300 rounded-l-md">
                <FileSpreadsheet class="w-3.5 h-3.5 text-gray-500" />
              </span>
              <input v-model="docExcelPath" type="text" class="pk-input-mono text-sm rounded-none"
                placeholder="C:\path\to\Document Register.xlsx" autocomplete="off" />
              <button type="button" @click="showDocExcelBrowser = true"
                class="flex items-center justify-center px-2 py-1 text-xs border border-l-0 border-gray-300 rounded-r-md bg-gray-100 hover:bg-gray-50"
                title="Browse for Excel file">
                <FolderOpen class="w-3.5 h-3.5" />
              </button>
            </div>
            <div class="pk-hint">
              <Info class="w-3 h-3 inline" /> Supports local paths or SharePoint URLs (auto-converted).
            </div>
          </div>
          <div style="min-width: 200px; flex: 0.6;">
            <label class="text-xs font-semibold mb-1 block">SharePoint Site URL</label>
            <div class="flex">
              <span class="flex items-center justify-center px-2 py-1 text-xs bg-gray-100 border border-r-0 border-gray-300 rounded-l-md">
                <CloudCheck class="w-3.5 h-3.5 text-gray-500" />
              </span>
              <input v-model="docSpSiteUrl" type="text" class="pk-input-mono text-sm rounded-none"
                placeholder="SharePoint site URL" autocomplete="off" />
            </div>
          </div>
          <div style="min-width: 100px; flex: 0.2;">
            <label class="text-xs font-semibold mb-1 block">&nbsp;</label>
            <button v-if="prefs.spOverridesConfigured || prefs.skipSpOverride"
              type="submit" class="pk-btn-primary w-full text-xs" :disabled="docConfigLoading.isLoading.value">
              <Loader v-if="docConfigLoading.isLoading.value" class="w-3 h-3 animate-spin" />
              <Save v-else class="w-3 h-3" /> Save Config
            </button>
            <button v-else type="button" class="pk-btn-secondary w-full text-xs" disabled
              title="Configure SharePoint Path Overrides above before saving Document Register config">
              <Lock class="w-3 h-3" /> Save Config
            </button>
          </div>
        </form>

        <div v-if="prefs.docRegisterExcelPath" class="mt-3 flex items-center gap-2">
          <button @click="rebuildLoading.execute()"
            class="border border-cyan-300 text-cyan-600 rounded px-3 py-1 text-xs hover:bg-cyan-50 flex items-center gap-1"
            :disabled="rebuildLoading.isLoading.value">
            <Loader v-if="rebuildLoading.isLoading.value" class="w-3 h-3 animate-spin" />
            <RotateCw v-else class="w-3 h-3" /> Rebuild Database
          </button>
          <span v-if="prefs.docRegisterDbLastImported" class="text-xs text-gray-500">
            <Clock class="w-3 h-3 inline" /> Last built: {{ prefs.docRegisterDbLastImported }}
          </span>
        </div>
        <div v-else class="mt-2 text-xs text-gray-500">
          <Info class="w-3 h-3 inline" /> Configure the Excel path above, then click Save to enable document search in References.
        </div>

        <div v-if="rebuildResult" class="mt-2 rounded px-3 py-1 text-xs"
          :class="rebuildResult.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'">
          {{ rebuildResult.message }}
          <div v-if="rebuildResult.error" class="mt-1">{{ rebuildResult.error }}</div>
        </div>
      </div>
    </div>
  </div>

  <!-- ── License Key (full width) ────────────────────────────── -->
  <div class="mt-4">
    <div class="pk-card">
      <div class="pk-card-header flex items-center gap-2">
        <Key class="w-4 h-4 text-yellow-500" /> License Key
        <span class="ml-auto bg-yellow-100 text-yellow-700 text-xs px-2 py-0.5 rounded">Coming Soon</span>
      </div>
      <div class="pk-card-body">
        <div class="pk-msg-info p-2 mb-3 flex items-center gap-2">
          <Info class="w-4 h-4" />
          <strong>License key activation is not yet implemented.</strong>
          Currently running in trial mode. This feature will be available in a future update.
        </div>
        <div class="text-center text-gray-400 py-4">
          <Key class="w-12 h-12 mx-auto mb-2" />
          <p class="text-sm">License management functionality coming soon...</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Path browsers -->
  <PathBrowser v-if="showOverrideBrowser" filter="folder"
    @close="showOverrideBrowser = false"
    @select="(p: string) => { newLocalPath = p; showOverrideBrowser = false }" />
  <PathBrowser v-if="showDocExcelBrowser" filter="excel"
    @close="showDocExcelBrowser = false"
    @select="(p: string) => { docExcelPath = p; showDocExcelBrowser = false }" />
</template>

<style scoped>
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
