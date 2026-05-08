<script setup lang="ts">
import { watch } from "vue";
import { X } from "lucide-vue-next";

const props = defineProps<{
  open: boolean;
}>();

const emit = defineEmits<{
  "update:open": [value: boolean];
}>();

const selected = defineModel<string[]>({ required: true });

const PIPE_COLUMNS = [
  { key: "Line Number", label: "Line Number", defaultOn: true },
  { key: "Criteria Code", label: "Criteria Code", defaultOn: true },
  { key: "Volume [m³]", label: "Volume [m³]", defaultOn: false },
  { key: "ρV² min Criteria [Pa]", label: "ρV² min Criteria [Pa]", defaultOn: true },
  { key: "ρV² max Criteria [Pa]", label: "ρV² max Criteria [Pa]", defaultOn: true },
  { key: "ρV² calc [Pa]", label: "ρV² calc [Pa]", defaultOn: true },
];

const MANDATORY_KEYS = [
  "Pipe Name",
  "Line Size",
  "Line Length",
  "dP max Criteria",
  "v min Criteria",
  "v max Criteria",
  "DP/Length",
  "Velocity",
  "Criteria Check",
];

watch(
  () => props.open,
  (open) => {
    if (open && selected.value.length === 0) {
      selected.value = [
        ...MANDATORY_KEYS,
        ...PIPE_COLUMNS.filter((c) => c.defaultOn).map((c) => c.key),
      ];
    }
  },
);

function toggleColumn(key: string) {
  if (!selected.value) return;
  const idx = selected.value.indexOf(key);
  if (idx === -1) {
    selected.value = [...selected.value, key];
  } else {
    selected.value = selected.value.filter((_, i) => i !== idx);
  }
}

function close() {
  emit("update:open", false);
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="fixed inset-0 bg-black/40" @click="close" />
        <div
          class="relative z-10 w-full max-w-md rounded-lg bg-white p-6 shadow-xl"
          @click.stop
        >
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-800">Report Columns</h3>
            <button
              type="button"
              class="rounded p-1 text-gray-400 hover:text-gray-600"
              @click="close"
            >
              <X class="w-5 h-5" />
            </button>
          </div>

          <p class="text-xs text-gray-500 mb-3">
            Select optional columns to include in the Pipes section.
            Core columns (Pipe Name, Line Size, Length, Velocity, DP/Length, Criteria Check) are always included.
          </p>

          <div class="space-y-1 max-h-80 overflow-y-auto">
            <label
              v-for="col in PIPE_COLUMNS"
              :key="col.key"
              class="flex items-center gap-3 rounded px-3 py-1.5 hover:bg-gray-50 cursor-pointer"
            >
              <input
                type="checkbox"
                class="h-4 w-4 rounded border-gray-300 text-green-600 focus:ring-green-500"
                :checked="selected.includes(col.key)"
                @change="toggleColumn(col.key)"
              />
              <span class="text-sm text-gray-700">{{ col.label }}</span>
            </label>
          </div>

          <div class="mt-4 flex justify-end">
            <button
              type="button"
              class="rounded bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
              @click="close"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
