<script setup lang="ts">
import { computed } from 'vue'
import { useSessionStore } from '../stores/session'
import { useRouter } from 'vue-router'
import { RotateCw, Home, Info, Settings, FileSpreadsheet, BookMarked, Grid3X3, ArrowUpCircle, FileText, Clock } from 'lucide-vue-next'

const session = useSessionStore()
const router = useRouter()

const isLoaded = computed(() => session.isLoaded)

async function goHome() {
  router.push('/')
}

async function reloadModel() {
  await session.reloadModel()
}
</script>

<template>
  <nav class="navbar">
    <!-- Brand -->
    <a href="/" class="navbar-brand" @click.prevent="goHome">
      <Grid3X3 class="w-4 h-4" />
      pyKorf
    </a>
    <span class="text-gray-400 ml-1" style="font-size: 0.72rem;"></span>

    <!-- KDF badge -->
    <span v-if="isLoaded && session.kdfPath"
      class="kdf-badge ml-3"
      :title="session.kdfPath">
      <FileText class="w-3.5 h-3.5 opacity-70" style="font-size: 0.9rem;" />
      {{ session.filename }}
    </span>

    <!-- Mtime -->
    <span v-if="session.kdfMtime" class="text-gray-400 ml-2" style="font-size: 0.72rem;"
      title="KDF file last modified on disk">
      <Clock class="w-3 h-3 inline" style="font-size: 0.7rem;" />
      {{ session.kdfMtime }}
    </span>

    <!-- Reload button -->
    <button v-if="isLoaded" @click="reloadModel"
      class="btn-reload ml-1" title="Reload model from disk">
      <RotateCw class="w-3.5 h-3.5" />
    </button>

    <!-- Update badge -->
    <span v-if="session.updateAvailable"
      class="pk-badge-update ml-2 flex items-center gap-1"
      title="Close terminal and restart the application to apply the update.">
      <ArrowUpCircle class="w-3 h-3" /> Update Available
    </span>

    <!-- Nav links -->
    <div class="ml-auto flex items-center gap-1">
      <template v-if="session.updateAvailable">
        <button class="btn-update-ready"
          title="Stop the pyKorf server now. Close this tab and restart from the terminal."
          @click="router.push('/')">
          <ArrowUpCircle class="w-3.5 h-3.5" /> Update Ready
        </button>
      </template>
      <router-link to="/about" class="navbar-link">
        <Info class="w-4 h-4" /> About
      </router-link>
      <router-link to="/preferences" class="navbar-link">
        <Settings class="w-4 h-4" /> Preferences
      </router-link>
      <router-link v-if="isLoaded" to="/model" class="navbar-link">
        <Grid3X3 class="w-4 h-4" /> Menu
      </router-link>
      <router-link v-if="isLoaded" to="/model/report" class="navbar-link">
        <FileSpreadsheet class="w-4 h-4" /> Report
      </router-link>
      <router-link v-if="isLoaded" to="/model/references" class="navbar-link">
        <BookMarked class="w-4 h-4" /> Refs
      </router-link>
      <router-link to="/" class="navbar-link text-blue-600" title="Home">
        <Home class="w-4 h-4" />
      </router-link>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  display: flex;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}
.navbar-brand {
  font-weight: 700;
  letter-spacing: 0.05em;
  color: #2563eb;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  text-decoration: none;
  font-size: 1rem;
}
.kdf-badge {
  font-family: monospace;
  font-size: 0.82rem;
  font-weight: 500;
  color: #212529;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 0.2rem 0.6rem;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  max-width: 40vw;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.btn-reload {
  background: none;
  border: 1px solid transparent;
  border-radius: 0.25rem;
  padding: 0.125rem 0.25rem;
  color: #6c757d;
  cursor: pointer;
}
.btn-reload:hover {
  border-color: #dee2e6;
  color: #495057;
}
.btn-update-ready {
  font-size: 0.78rem;
  border: 1px solid #22c55e;
  color: #22c55e;
  border-radius: 0.25rem;
  padding: 0.15rem 0.5rem;
  background: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
.btn-update-ready:hover {
  background: #f0fdf4;
}
.navbar-link {
  color: #6c757d;
  text-decoration: none;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
}
.navbar-link:hover {
  color: #495057;
  background: rgba(0, 0, 0, 0.04);
}
</style>
