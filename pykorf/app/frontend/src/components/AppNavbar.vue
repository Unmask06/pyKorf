<script setup lang="ts">
import {
  ArrowUpCircle,
  BookMarked,
  Clock,
  FileSpreadsheet,
  FileText,
  Grid3X3,
  Home,
  Info,
  Monitor,
  Settings,
} from "lucide-vue-next";
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useSessionStore } from "../stores/session";
import { useToastStore } from "../composables/useToast";
import { api } from "../api/client";
import { openModelInKorf } from "../api/generated/sdk.gen";

const session = useSessionStore();
const router = useRouter();
const toast = useToastStore();

const isLoaded = computed(() => session.isLoaded);

async function goHome() {
  router.push("/");
}

async function handleUpdateClick() {
  toast.warning("Server shutting down — restart to apply updates");
  try {
    await api.post("/api/session/shutdown");
  } catch (error) {
    toast.error("Failed to shutdown server. Please close manually.");
  }
}

async function openInKorf() {
  try {
    const res = await openModelInKorf();
    toast.success(res.data?.message || "Korf opened");
  } catch (error: any) {
    toast.error(error?.response?.data?.detail || "Failed to open in Korf");
  }
}
</script>

<template>
  <nav class="navbar">
    <!-- Brand -->
    <a href="/" class="navbar-brand" @click.prevent="goHome">
      <Grid3X3 class="w-4 h-4" />
      pyKorf
    </a>
    <span
      v-if="session.version"
      class="text-gray-400 ml-1"
      style="font-size: 0.72rem"
      >{{ session.version }}</span
    >

    <!-- KDF badge -->
    <span
      v-if="isLoaded && session.kdfPath"
      class="kdf-badge ml-3"
      :title="session.kdfPath"
    >
      <FileText class="w-3.5 h-3.5 opacity-70" style="font-size: 0.9rem" />
      {{ session.filename }}
    </span>

    <!-- Mtime -->
    <span
      v-if="session.kdfMtime"
      class="text-gray-400 ml-2"
      style="font-size: 0.72rem"
      title="KDF file last modified on disk"
    >
      <Clock class="w-3 h-3 inline" style="font-size: 0.7rem" />
      {{ session.kdfMtime }}
    </span>

    <!-- Open in Korf -->
    <button
      v-if="isLoaded"
      class="navbar-link ml-1"
      title="Open in Korf application"
      @click="openInKorf"
    >
      <Monitor class="w-4 h-4" /> Korf
    </button>

    <!-- Update badge -->
    <button
      v-if="session.updateAvailable"
      class="pk-badge-update ml-2 flex items-center gap-1 cursor-pointer hover:bg-green-50"
      title="Click for update instructions"
      @click="handleUpdateClick"
    >
      <ArrowUpCircle class="w-3 h-3" /> Update Available
    </button>

    <!-- Nav links -->
    <div class="ml-auto flex items-center gap-1">
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
  position: sticky;
  top: 0;
  z-index: 40;
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
