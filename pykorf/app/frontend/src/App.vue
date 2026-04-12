<script setup lang="ts">
import { onMounted } from 'vue'
import { useSessionStore } from './stores/session'
import AppNavbar from './components/AppNavbar.vue'
import AppToast from './components/AppToast.vue'

const session = useSessionStore()

onMounted(() => {
  session.fetchStatus()
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
