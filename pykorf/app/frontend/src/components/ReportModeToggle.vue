<script setup lang="ts">
const model = defineModel<boolean>({ required: true });
</script>

<template>
  <div class="flex items-center justify-between py-2">
    <span class="text-sm text-gray-600">Report Mode</span>
    <div class="flex items-center gap-3">
      <span
        :class="model ? 'text-gray-400' : 'text-gray-700 font-medium'"
        class="text-sm"
        >Single Case</span
      >
      <button
        type="button"
        @click="model = !model"
        class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
        :class="model ? 'bg-green-600' : 'bg-gray-200'"
        role="switch"
        :aria-checked="model"
      >
        <span
          class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
          :class="model ? 'translate-x-6' : 'translate-x-1'"
        />
      </button>
      <span
        :class="model ? 'text-gray-700 font-medium' : 'text-gray-400'"
        class="text-sm"
        >Multi Case</span
      >
    </div>
  </div>
</template>
