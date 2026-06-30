<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { useSessionStore } from "./stores/session";
import { useToastStore } from "./composables/useToast";
import AppNavbar from "./components/AppNavbar.vue";
import AppToast from "./components/AppToast.vue";
import WhatsNewModal from "./components/WhatsNewModal.vue";
import {
  getWhatsNew,
  markWhatsNewSeen,
} from "./api/client";
import type {
  WhatsNewResponse,
  WhatsNewSection,
} from "./api/generated/types.gen";

const session = useSessionStore();
const toast = useToastStore();

function handleModelReload() {
  toast.info('Model reloaded from disk.')
  session.fetchStatus();
}

// "What's New" modal state — driven by an event bus so any view (e.g. About)
// can also request to open it.
const showWhatsNew = ref(false)
const whatsNewData = ref<{
  version: string
  date: string | null
  sections: WhatsNewSection[]
} | null>(null)

function openWhatsNew(data: WhatsNewResponse) {
  whatsNewData.value = {
    version: data.version ?? '',
    date: data.date ?? null,
    sections: data.sections ?? [],
  }
  showWhatsNew.value = true
}

async function dismissWhatsNew() {
  showWhatsNew.value = false
  try {
    await markWhatsNewSeen({ body: {} })
  } catch { /* best-effort */ }
}

async function checkWhatsNew() {
  try {
    const { data } = await getWhatsNew()
    if (!data) return
    if (data.has_unseen && (data.sections ?? []).length > 0) {
      openWhatsNew(data)
    }
  } catch { /* best-effort */ }
}

function onWhatsNewRequest(event: Event) {
  // Custom event from the About view — "show current What's New notes".
  const detail = (event as CustomEvent<WhatsNewResponse>).detail
  if (detail) openWhatsNew(detail)
}

onMounted(() => {
  session.fetchStatus()
  window.addEventListener('model-reloaded', handleModelReload)
  window.addEventListener('show-whats-new', onWhatsNewRequest)
  void checkWhatsNew()
})

onUnmounted(() => {
  window.removeEventListener('model-reloaded', handleModelReload)
  window.removeEventListener('show-whats-new', onWhatsNewRequest)
})
</script>

<template>
  <div class="min-h-screen bg-white">
    <AppNavbar />
    <AppToast />
    <main class="container-fluid mx-auto px-4 py-4">
      <router-view />
    </main>

    <WhatsNewModal
      v-if="showWhatsNew && whatsNewData"
      :version="whatsNewData.version"
      :date="whatsNewData.date"
      :sections="whatsNewData.sections"
      @close="dismissWhatsNew"
    />
  </div>
</template>
