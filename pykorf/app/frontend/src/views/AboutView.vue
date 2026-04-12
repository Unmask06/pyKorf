<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../api/client'
import { Info, CheckCircle, Home } from 'lucide-vue-next'

const version = ref('')
const releaseDate = ref('')

onMounted(async () => {
  try {
    const { data } = await api.get('/api/about/')
    version.value = data.version
    releaseDate.value = data.release_date
  } catch { /* ignore */ }
})
</script>

<template>
  <div class="flex justify-center">
    <div class="w-full" style="max-width: 720px;">
      <div class="pk-card">
        <div class="pk-card-header flex items-center gap-2">
          <Info class="w-4 h-4 text-blue-600" /> About pyKorf
        </div>
        <div class="p-4">
          <div class="flex items-center gap-2 mb-3">
            <span class="bg-blue-600 text-white px-2.5 py-1 rounded text-lg">{{ version }}</span>
            <span class="text-gray-500 text-sm">Released {{ releaseDate }}</span>
          </div>

          <p class="text-base mb-2">
            <strong>pyKorf</strong> is a lightweight toolkit for engineers working with
            <a href="https://korf.ca/hydraulics.php" target="_blank" rel="noopener" class="text-blue-600 no-underline">KORF</a>
            hydraulic model files (<code class="bg-gray-100 rounded px-1 text-sm">.kdf</code>).
          </p>

          <p class="text-gray-500 mb-4">
            KORF is powerful but its native interface offers limited bulk-editing and reporting
            capabilities. pyKorf bridges that gap — load a model, apply consistent pipe sizing
            criteria, import PMS / HMB data from Excel, and export a clean summary report, all
            from a browser.
          </p>

          <hr class="my-3" />

          <h6 class="text-xs font-semibold text-gray-400 uppercase mb-3 mt-3">Key Features</h6>
          <ul class="list-none space-y-1 mb-4">
            <li class="flex items-start gap-2">
              <CheckCircle class="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              Read and write <code class="bg-gray-100 rounded px-1">.kdf</code> model files without opening KORF
            </li>
            <li class="flex items-start gap-2">
              <CheckCircle class="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              Assign pipe sizing criteria (dP, velocity) from a built-in lookup table
            </li>
            <li class="flex items-start gap-2">
              <CheckCircle class="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              Bulk-import fluid data from PMS and HMB spreadsheets
            </li>
            <li class="flex items-start gap-2">
              <CheckCircle class="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              Export a pipe summary report to Excel
            </li>
            <li class="flex items-start gap-2">
              <CheckCircle class="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              Apply project level parameters to entire model in one click
            </li>
          </ul>

          <hr class="my-3" />

          <h6 class="text-xs font-semibold text-gray-400 uppercase mb-3 mt-3">Author</h6>
          <div class="flex items-center gap-3">
            <div class="rounded-full bg-blue-600 flex items-center justify-center text-white font-bold"
              style="width: 48px; height: 48px; font-size: 1.1rem; flex-shrink: 0;">
              PP
            </div>
            <div>
              <div class="font-semibold">Prasanna Palanivel</div>
              <div class="text-gray-500 text-sm">Process Engineer</div>
            </div>
          </div>
        </div>
        <div class="border-t px-4 py-3 text-gray-500 text-sm flex justify-between items-center">
          <span>pyKorf — Built for the Process Engineers by the Process Engineer</span>
          <router-link to="/" class="pk-btn-secondary text-xs flex items-center gap-1">
            <Home class="w-3 h-3" /> Home
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.no-underline {
  text-decoration: none;
}
</style>
