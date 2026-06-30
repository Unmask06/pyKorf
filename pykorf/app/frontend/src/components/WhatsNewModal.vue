<script setup lang="ts">
import { computed } from "vue";
import { Sparkles, X } from "lucide-vue-next";
import type { WhatsNewSection } from "../api/generated/types.gen";

const props = defineProps<{
  version: string;
  date?: string | null;
  sections: WhatsNewSection[];
}>();

const emit = defineEmits<{
  close: [];
}>();

// Color the section header based on its category — What's New is the hero
// (brand color), Improved is positive (blue), Fixed is corrective (green).
function sectionClass(title: string): string {
  const t = title.toLowerCase();
  if (t.includes("fix")) return "wn-section wn-section-fixed";
  if (t.includes("improve") || t.includes("changed") || t.includes("update"))
    return "wn-section wn-section-improved";
  return "wn-section wn-section-new";
}

function sectionIcon(title: string): string {
  const t = title.toLowerCase();
  if (t.includes("fix")) return "🐛";
  if (t.includes("improve") || t.includes("changed") || t.includes("update"))
    return "✨";
  return "🆕";
}

const hasContent = computed(() => props.sections.length > 0);
</script>

<template>
  <div class="pk-modal-backdrop">
    <div class="pk-modal whats-new-modal">
      <!-- Header -->
      <div
        class="pk-modal-header flex items-center justify-between pb-3 border-b"
      >
        <div class="flex items-center gap-2">
          <Sparkles class="w-5 h-5 text-amber-500" />
          <h6 class="font-semibold text-lg">What's New in pyKorf</h6>
          <span class="wn-version-badge">{{ version }}</span>
          <span v-if="date" class="wn-date">{{ date }}</span>
        </div>
        <button
          @click="emit('close')"
          class="text-gray-400 hover:text-gray-600 p-1 rounded hover:bg-gray-100"
          title="Close"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Body -->
      <div class="whats-new-body">
        <template v-if="hasContent">
          <div
            v-for="(section, sIdx) in sections"
            :key="sIdx"
            :class="sectionClass(section.title || '')"
          >
            <div class="wn-section-header">
              <span class="wn-section-icon">{{ sectionIcon(section.title || '') }}</span>
              <h4 class="wn-section-title">{{ section.title }}</h4>
            </div>
            <ul v-if="section.items?.length" class="wn-section-list">
              <li
                v-for="(item, iIdx) in section.items"
                :key="iIdx"
                class="wn-section-item"
              >
                {{ item }}
              </li>
            </ul>
          </div>
        </template>
        <template v-else>
          <div class="whats-new-empty">
            <Sparkles class="w-8 h-8 mx-auto mb-2 text-amber-400" />
            <p>No release notes for this version.</p>
          </div>
        </template>
      </div>

      <!-- Footer -->
      <div
        class="px-4 py-2.5 border-t bg-gray-50 flex items-center justify-end rounded-b-lg"
      >
        <button
          @click="emit('close')"
          class="pk-btn-primary px-4 py-1.5 text-sm rounded shrink-0"
        >
          Got it
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── Modal shell ─────────────────────────────────────────────────────────── */
.whats-new-modal {
  width: 640px !important;
  max-width: 92vw !important;
  max-height: 85vh !important;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: wn-pop-in 0.18s ease-out;
}

@keyframes wn-pop-in {
  from { opacity: 0; transform: scale(0.96) translateY(6px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}

/* ── Header badges ───────────────────────────────────────────────────────── */
.wn-version-badge {
  display: inline-flex;
  align-items: center;
  background: #2563eb;
  color: #fff;
  padding: 0.1rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.7rem;
  font-weight: 700;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.wn-date {
  font-size: 0.7rem;
  color: #6b7280;
  font-weight: 500;
}

/* ── Body (scrollable) ───────────────────────────────────────────────────── */
.whats-new-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 0.85rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

/* ── Sections ────────────────────────────────────────────────────────────── */
.wn-section {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 0.6rem 0.85rem;
  background: #fafafa;
}

.wn-section-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.35rem;
}

.wn-section-icon {
  font-size: 0.95rem;
  line-height: 1;
}

.wn-section-title {
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin: 0;
}

/* What's New — hero (amber) */
.wn-section-new {
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
  border-color: #fcd34d;
}
.wn-section-new .wn-section-title {
  color: #b45309;
}

/* Improved — blue */
.wn-section-improved {
  background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%);
  border-color: #93c5fd;
}
.wn-section-improved .wn-section-title {
  color: #1d4ed8;
}

/* Fixed — green */
.wn-section-fixed {
  background: linear-gradient(180deg, #f0fdf4 0%, #dcfce7 100%);
  border-color: #86efac;
}
.wn-section-fixed .wn-section-title {
  color: #15803d;
}

.wn-section-list {
  list-style: none;
  margin: 0;
  padding: 0 0 0 0.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.wn-section-item {
  font-size: 0.83rem;
  line-height: 1.45;
  color: #1f2937;
  padding-left: 0.9rem;
  position: relative;
}

.wn-section-item::before {
  content: "•";
  position: absolute;
  left: 0.15rem;
  color: #6b7280;
  font-weight: 700;
}

/* ── Empty state ─────────────────────────────────────────────────────────── */
.whats-new-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  font-size: 0.85rem;
  padding: 2rem 0;
}
</style>
