<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useSessionStore } from './stores/session'
import { useToastStore } from './composables/useToast'
import AppNavbar from './components/AppNavbar.vue'
import AppToast from './components/AppToast.vue'

const session = useSessionStore()
const toast = useToastStore()

function handleModelReload() {
  toast.info('Model reloaded from disk.')
  session.fetchStatus()
}

onMounted(() => {
  session.fetchStatus()
  window.addEventListener('model-reloaded', handleModelReload)
})

onUnmounted(() => {
  window.removeEventListener('model-reloaded', handleModelReload)
})
</script>

<template>
  <div class="min-h-screen bg-white">
    <AppNavbar />
    <AppToast />
    <main class="container-fluid mx-auto px-4 py-4">
      <router-view />
    </main>
  </div>
</template>
