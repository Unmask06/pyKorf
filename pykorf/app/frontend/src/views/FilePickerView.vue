<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '../stores/session'
import { useToastStore } from '../composables/useToast'
import { useLoading } from '../composables/useLoading'
import { FolderOpen, ArrowRight, FileText, Clock, Lightbulb, Shield, ArrowUpCircle, StopCircle } from 'lucide-vue-next'
import PathBrowser from '../components/PathBrowser.vue'

const router = useRouter()
const session = useSessionStore()
const toast = useToastStore()

const kdfPath = ref('')
const showBrowser = ref(false)

const openLoading = useLoading(async (path: string) => {
  await session.openFile(path)
})

async function openFile() {
  const path = kdfPath.value.trim().replace(/^"|"$/g, '')
  if (!path) {
    toast.error('Please enter a file path.')
    return
  }
  try {
    await openLoading.execute(path)
    if (session.isLoaded) {
      toast.success('Model loaded successfully.')
      router.push('/model')
    }
  } catch (err: any) {
    toast.error(err.response?.data?.detail || err.message || 'Failed to load model.')
  }
}

function selectRecent(path: string) {
  kdfPath.value = path
  openFile()
}

onMounted(() => {
  session.fetchStatus()
  if (session.recentFiles.length > 0 && !kdfPath.value) {
    kdfPath.value = session.recentFiles[0]
  }
})
</script>

<template>
  <div class="flex justify-center mt-4">
    <div class="w-full" style="max-width: 720px;">

      <!-- Hero section -->
      <div class="text-center mb-4">
        <p class="text-gray-500 mb-1">Hello, <strong>{{ session.username }}</strong>!</p>
        <h1 class="text-2xl font-bold text-blue-600 flex items-center justify-center gap-2">
          <FolderOpen class="w-6 h-6" /> pyKorf
        </h1>
        <p class="pk-desc">Copilot for Hydraulic Network Modeling using KORF</p>
        <div v-if="session.updateAvailable" class="mt-2 flex items-center justify-center gap-2">
          <span class="pk-badge-update flex items-center gap-1">
            <ArrowUpCircle class="w-3.5 h-3.5" /> New Update Available
          </span>
          <button class="pk-btn-sm border border-red-200 text-red-600 hover:bg-red-50 flex items-center gap-1"
            title="Stop the pyKorf server now. Close this tab and restart from the terminal."
            @click="toast.warning('To update: close terminal and restart the application.')">
            <StopCircle class="w-3.5 h-3.5" /> Stop Server
          </button>
        </div>
      </div>

      <!-- Setup required alert -->
      <div v-if="!session.setupOk" class="pk-alert-warn p-3 mb-4">
        <div class="font-semibold mb-1 flex items-center gap-1">
          <Shield class="w-4 h-4" /> Setup Required Before Opening a Model
        </div>
        <ul class="text-sm mb-2 list-disc pl-5 space-y-0.5">
          <li v-if="!session.spOk && !session.skipSpOverride">SharePoint Override — not configured</li>
          <li v-if="!session.docRegisterOk && !session.skipSpOverride">Document Register Excel path — not set or file not found</li>
        </ul>
        <router-link to="/preferences"
          class="inline-flex items-center gap-1 bg-yellow-500 text-white px-3 py-1 rounded text-sm hover:bg-yellow-600">
          Go to Preferences
        </router-link>
      </div>

      <!-- Open file card -->
      <div class="pk-card">
        <div class="pk-card-body">
          <form @submit.prevent="openFile">
            <div class="mb-3">
              <label class="font-bold text-blue-600 block mb-2">{{ session.filename || 'Select file' }}</label>
              <label class="pk-label">File Path</label>
              <div class="flex">
                <span class="flex items-center justify-center px-3 py-1.5 text-sm bg-gray-100 border border-r-0 border-gray-300 rounded-l-md">
                  <FileText class="w-4 h-4 text-gray-500" />
                </span>
                <textarea v-model="kdfPath" class="pk-input-mono resize-none rounded-none"
                  rows="2" placeholder="C:/projects/model.kdf" />
                <button type="button" @click="showBrowser = true"
                  class="flex items-center justify-center px-3 py-1.5 text-sm border border-l-0 border-gray-300 rounded-r-md bg-gray-100 hover:bg-gray-200"
                  title="Browse for .kdf file">
                  <FolderOpen class="w-4 h-4" />
                </button>
              </div>
              <div class="pk-hint">Paste the absolute path or choose from recent files below.</div>
            </div>
            <button type="submit" class="w-full bg-blue-600 text-white rounded py-2 hover:bg-blue-700 flex items-center justify-center gap-1 disabled:opacity-50"
              :disabled="!session.setupOk || openLoading.isLoading.value">
              <span v-if="openLoading.isLoading.value" class="pk-spinner" />
              <ArrowRight class="w-4 h-4" /> Open Model
            </button>
          </form>
        </div>
      </div>

      <!-- Recent files -->
      <div v-if="session.recentFiles.length > 0" class="pk-card mt-3">
        <div class="pk-card-header flex items-center gap-1">
          <Clock class="w-4 h-4" /> Recent Files
        </div>
        <ul class="divide-y">
          <li v-for="f in session.recentFiles" :key="f" class="p-0">
            <a href="#"
              class="flex items-center gap-2 py-2 px-3 no-underline hover:bg-gray-50"
              :class="{ 'pointer-events-none text-gray-400': !session.setupOk }"
              @click.prevent="session.setupOk && selectRecent(f)"
              :title="!session.setupOk ? 'Complete setup in Preferences first' : f">
              <FileText class="w-4 h-4 text-gray-400 flex-shrink-0" />
              <span class="font-mono text-sm flex-grow truncate text-gray-800">{{ f.split(/[\/\\]/).pop() }}</span>
              <span class="text-gray-400 text-xs truncate" style="max-width: 45%;">{{ f }}</span>
              <ArrowRight class="w-3 h-3 text-blue-600 flex-shrink-0" />
            </a>
          </li>
        </ul>
      </div>

      <!-- How to Use -->
      <div class="pk-card mt-3">
        <div class="pk-card-header flex items-center gap-1">
          <Lightbulb class="w-4 h-4" /> How to Use
        </div>
        <div class="p-4 text-sm text-gray-500">
          <ol class="pl-4 space-y-1 mb-0">
            <li>Type or paste the full path to a <code class="bg-gray-100 rounded px-1">.kdf</code> file, or use the <FolderOpen class="w-3 h-3 inline" /> browse button.</li>
            <li>Click <strong>Open Model</strong> to load it.</li>
            <li>Recent files appear below for quick access.</li>
          </ol>
        </div>
      </div>

    </div>
  </div>

  <PathBrowser v-if="showBrowser" @close="showBrowser = false" @select="(p: string) => { kdfPath = p; showBrowser = false }" filter="kdf" />
</template>
