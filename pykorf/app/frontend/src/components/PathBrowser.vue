<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { api } from '../api/client'
import { Folder, File, ArrowUp, Cloud, FolderOpen, CloudCheck, Check, ArrowLeftRight, Pin, PinOff } from 'lucide-vue-next'

const props = defineProps<{
  filter?: string
}>()

const emit = defineEmits<{
  close: []
  select: [path: string]
}>()

interface DirEntry { name: string; path: string; synced: boolean }
interface FileEntry { name: string; path: string; sharepoint_url: string | null }

const currentPath = ref('')
const parentPath = ref<string | null>(null)
const drives = ref<string[]>([])
const pinnedFolders = ref<string[]>([])
const dirs = ref<DirEntry[]>([])
const files = ref<FileEntry[]>([])
const filterText = ref('')
const selectedPath = ref<string | null>(null)
const selectedSpUrl = ref<string | null>(null)
const currentSpUrl = ref<string | null>(null)
const useAsSp = ref(false)

async function browse(path?: string) {
  const filter = props.filter || 'any'
  const url = `/api/browse?filter=${encodeURIComponent(filter)}${path ? '&path=' + encodeURIComponent(path) : ''}`
  try {
    const { data } = await api.get(url)
    currentPath.value = data.current
    currentSpUrl.value = data.current_sp_url
    parentPath.value = data.parent
    drives.value = data.drives
    pinnedFolders.value = data.pinned_folders || []
    dirs.value = data.dirs
    files.value = data.files
    selectedPath.value = null
    selectedSpUrl.value = null
    useAsSp.value = false
  } catch { /* ignore */ }
}

function selectDir(d: DirEntry) {
  if (props.filter === 'folder') {
    selectedPath.value = d.path
    selectedSpUrl.value = null
  } else {
    browse(d.path)
  }
}

function selectFile(f: FileEntry) {
  selectedPath.value = f.path
  selectedSpUrl.value = f.sharepoint_url
  useAsSp.value = false
}

function confirm() {
  if (selectedPath.value) {
    if (useAsSp.value && selectedSpUrl.value) {
      emit('select', selectedSpUrl.value)
    } else {
      emit('select', selectedPath.value)
    }
  }
}

async function pinCurrentFolder() {
  if (!currentPath.value) return
  await api.post(`/api/browse/pin?folder=${encodeURIComponent(currentPath.value)}`)
  await browse(currentPath.value)
}

async function unpinFolder(folderPath: string) {
  await api.post(`/api/browse/unpin?folder=${encodeURIComponent(folderPath)}`)
  await browse(currentPath.value)
}

const isCurrentPinned = computed(() => pinnedFolders.value.includes(currentPath.value))

function displayNameForPinned(p: string): string {
  // Show just the folder name, not full path
  return p.replace(/[/\\]$/, '').split(/[/\\]/).pop() || p
}

const filteredDirs = computed(() => {
  if (!filterText.value) return dirs.value
  const q = filterText.value.toLowerCase()
  return dirs.value.filter(d => d.name.toLowerCase().includes(q))
})

const filteredFiles = computed(() => {
  if (!filterText.value) return files.value
  const q = filterText.value.toLowerCase()
  return files.value.filter(f => f.name.toLowerCase().includes(q))
})

onMounted(() => {
  browse()
})
</script>

<template>
  <div class="modal-backdrop">
    <div class="modal-lg">
      <!-- Header -->
      <div class="modal-header">
        <h6 class="font-semibold flex items-center gap-2 mb-0">
          <FolderOpen class="w-4 h-4 text-yellow-500" /> Browse Files
        </h6>
        <button @click="emit('close')" class="btn-close-icon" aria-label="Close">
          &times;
        </button>
      </div>

      <!-- Body -->
      <div class="modal-body p-3">

        <!-- SharePoint sync banner -->
        <div v-if="currentSpUrl" class="sp-banner mb-2 flex items-center gap-2">
          <CloudCheck class="w-4 h-4 text-blue-600" />
          <span class="text-blue-700 font-semibold text-xs">SharePoint synced folder</span>
        </div>

        <!-- Drives row -->
        <div v-if="drives.length || pinnedFolders.length" class="mb-2 flex items-center gap-2 flex-wrap">
          <template v-if="pinnedFolders.length">
            <span class="text-gray-500 text-xs mr-1 flex items-center gap-0.5">
              <Pin class="w-3 h-3" /> Pinned:
            </span>
            <span v-for="p in pinnedFolders" :key="p" @click="browse(p)"
              class="pinned-btn font-mono text-xs border border-yellow-300 bg-yellow-50 rounded px-1.5 py-0.5 hover:bg-yellow-100 inline-flex items-center gap-1 cursor-pointer"
              :title="p">
              <Folder class="w-3 h-3 text-yellow-600" /> {{ displayNameForPinned(p) }}
              <button @click.stop="unpinFolder(p)" class="unpin-x ml-0.5 text-gray-400 hover:text-red-500"
                title="Unpin" aria-label="Unpin">&times;</button>
            </span>
          </template>
          <template v-if="drives.length">
            <span class="text-gray-500 text-xs mr-1">Drives:</span>
            <button v-for="d in drives" :key="d" @click="browse(d)"
              class="drive-btn font-mono text-xs border rounded px-1.5 py-0.5 hover:bg-gray-50">{{ d }}</button>
          </template>
        </div>

        <!-- Current path + Up + Pin button -->
        <div class="flex items-center gap-2 mb-2">
          <button @click="parentPath && browse(parentPath)" :disabled="!parentPath"
            class="pk-btn-icon py-0.5 disabled:opacity-30 flex-shrink-0"
            title="Go up one level">
            <ArrowUp class="w-3 h-3" />
          </button>
          <div class="breadcrumb flex-1">{{ currentPath }}</div>
          <button
            @click="isCurrentPinned ? unpinFolder(currentPath) : pinCurrentFolder()"
            class="pk-btn-icon py-0.5 flex-shrink-0"
            :class="isCurrentPinned ? 'text-yellow-600' : 'text-gray-400 hover:text-yellow-600'"
            :title="isCurrentPinned ? 'Unpin this folder' : 'Pin this folder'">
            <PinOff v-if="isCurrentPinned" class="w-3.5 h-3.5" />
            <Pin v-else class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- Filter -->
        <input v-model="filterText" placeholder="Filter…"
          class="pk-input mb-2" autocomplete="off" />

        <!-- Directory + file listing -->
        <div class="list-container">
          <div v-for="d in filteredDirs" :key="d.path"
            @click="selectDir(d)" @dblclick="browse(d.path)"
            class="list-item"
            :class="{ 'list-item-selected': selectedPath === d.path }">
            <Folder class="w-4 h-4 text-yellow-500 flex-shrink-0" />
            <span class="flex-1 text-sm">{{ d.name }}</span>
            <span v-if="d.synced" class="pk-badge-sp">SP</span>
          </div>
          <div v-for="f in filteredFiles" :key="f.path"
            @click="selectFile(f)" @dblclick="selectFile(f); confirm()"
            class="list-item list-item-file"
            :class="{ 'list-item-selected': selectedPath === f.path }">
            <File class="w-4 h-4 flex-shrink-0" />
            <span class="flex-1 text-sm">{{ f.name }}</span>
            <span v-if="f.sharepoint_url" class="pk-badge-sp">SP</span>
          </div>
          <div v-if="!filteredDirs.length && !filteredFiles.length" class="text-center text-gray-400 py-3 text-sm">
            No matching files
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="modal-footer">
        <div class="flex flex-col gap-2 w-full">
          <!-- Selected path display -->
          <div class="flex items-center gap-2 w-full">
            <span class="text-gray-500 text-xs">{{ selectedPath || 'No file selected' }}</span>
          </div>

          <!-- SP/local toggle -->
          <div v-if="selectedSpUrl" class="flex items-center gap-2 w-full">
            <span class="text-gray-500 text-xs mr-1 flex items-center gap-0.5">
              <ArrowLeftRight class="w-3 h-3" /> Use as:
            </span>
            <div class="flex gap-1">
              <button @click="useAsSp = true"
                :class="useAsSp ? 'border-blue-500 text-blue-600 bg-blue-50' : 'border-gray-300 text-gray-600'"
                class="text-xs border rounded px-2 py-0.5 flex items-center gap-1">
                <Cloud class="w-3 h-3" /> SharePoint URL
              </button>
              <button @click="useAsSp = false"
                :class="!useAsSp ? 'border-blue-500 text-blue-600 bg-blue-50' : 'border-gray-300 text-gray-600'"
                class="text-xs border rounded px-2 py-0.5 flex items-center gap-1">
                <Folder class="w-3 h-3" /> Local Path
              </button>
            </div>
          </div>

          <!-- Action buttons -->
          <div class="flex gap-2 justify-end w-full">
            <button @click="emit('close')" class="pk-btn-secondary text-sm">Cancel</button>
            <button @click="confirm" :disabled="!selectedPath"
              class="pk-btn-primary text-sm flex items-center gap-1 disabled:opacity-30">
              <Check class="w-3 h-3" /> Select
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
}
.modal-lg {
  background: #fff;
  border-radius: 0.5rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  width: 100%;
  max-width: 48rem;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 1rem;
  border-bottom: 1px solid #dee2e6;
}
.btn-close-icon {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: #6c757d;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}
.btn-close-icon:hover {
  color: #343a40;
}
.modal-body {
  overflow: auto;
  flex: 1;
}
.modal-footer {
  padding: 0.5rem 1rem;
  border-top: 1px solid #dee2e6;
}
/* SharePoint sync banner */
.sp-banner {
  font-size: 0.78rem;
  background: rgba(13, 110, 253, 0.15);
  border: 1px solid rgba(13, 110, 253, 0.4);
  border-radius: 0.375rem;
  padding: 0.25rem 0.6rem;
}
/* Drive buttons */
.drive-btn {
  border-color: #dee2e6;
}
/* Pinned folder buttons */
.pinned-btn {
  position: relative;
}
.pinned-btn .unpin-x {
  background: none;
  border: none;
  font-size: 0.85rem;
  line-height: 1;
  cursor: pointer;
  padding: 0;
}
.pinned-btn .unpin-x:hover {
  color: #dc3545 !important;
}
/* Breadcrumb */
.breadcrumb {
  font-family: monospace;
  font-size: 0.82rem;
  word-break: break-all;
  background: #f8f9fa;
  border-radius: 0.375rem;
  padding: 0.4rem 0.75rem;
}
/* List container */
.list-container {
  max-height: 340px;
  overflow-y: auto;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
}
.list-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0.75rem;
  cursor: pointer;
  font-size: 0.9rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  transition: background 0.1s;
}
.list-item:last-child {
  border-bottom: none;
}
.list-item:hover {
  background: #f8f9fa;
}
.list-item-file {
  color: #0dcaf0;
}
.list-item-selected {
  background: #2563eb !important;
  color: #fff !important;
}
.list-item-selected .pk-badge-sp {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}
</style>
