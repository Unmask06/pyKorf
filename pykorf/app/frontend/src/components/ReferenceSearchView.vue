<script setup lang="ts">
import { ref, computed, onBeforeUnmount, watch } from "vue";
import {
  Search,
  ExternalLink,
  FolderOpen,
  RotateCw,
  Info as InfoCircle,
  FileText,
  Folder,
} from "lucide-vue-next";
import { useLoading } from "../composables/useLoading";
import { api } from "../api/client";
import type {
  DocRegisterSearchEddrRequest,
  DocRegisterSearchEddrResponse,
  DocRegisterSearchQueryRequest,
  DocRegisterSearchQueryResponse,
  EddrResult,
  QueryEntryResult,
} from "../types/api";

const emit = defineEmits<{
  close: [];
  select: [name: string, link: string, description: string];
}>();

const docSearchQuery = ref("");
const docSearchResults = ref<EddrResult[]>([]);
const queryResults = ref<QueryEntryResult[]>([]);
const selectedEddrItem = ref<EddrResult | null>(null);
const docSearchMode = ref<"eddr" | "query">("eddr");
const queryFilter = ref("");

function docResultKey(item: EddrResult): string {
  return item.document_no;
}

function queryResultKey(item: QueryEntryResult): string {
  return `${item.name}:${item.path || ""}`;
}

function formatSharePointUrl(path: string): string {
  if (!path) return "#";
  if (path.startsWith("http")) return path;
  if (path.startsWith("sites/")) {
    return `https://cc7ges.sharepoint.com/${path.replace(/\\/g, "/")}`;
  }
  return path;
}

function itemUrl(item: QueryEntryResult): string {
  if (!item.path) return "#";
  const folder = item.path.replace(/\/+$/, "").replace(/\\+$/, "");
  const full = `${folder}/${item.name}`;
  return formatSharePointUrl(full);
}

const filteredQueryResults = computed(() => {
  if (!queryFilter.value) return queryResults.value;
  const q = queryFilter.value.toLowerCase();
  return queryResults.value.filter(
    (item) =>
      item.name.toLowerCase().includes(q) ||
      (item.path || "").toLowerCase().includes(q) ||
      (item.modified_by || "").toLowerCase().includes(q),
  );
});

const docSearchLoading = useLoading(async () => {
  if (docSearchMode.value === "eddr") {
    if (!docSearchQuery.value.trim()) {
      docSearchResults.value = [];
      return;
    }
    const req: DocRegisterSearchEddrRequest = { q: docSearchQuery.value };
    const { data } = await api.get<DocRegisterSearchEddrResponse>(
      "/api/doc-register/search-eddr",
      { params: req },
    );
    docSearchResults.value = data.results;
  } else {
    const docNo =
      selectedEddrItem.value?.document_no ||
      (!selectedEddrItem.value && queryFilter.value.trim()
        ? queryFilter.value.trim()
        : "");
    if (!docNo) {
      queryResults.value = [];
      return;
    }
    const req: DocRegisterSearchQueryRequest = { doc_no: docNo };
    const { data } = await api.get<DocRegisterSearchQueryResponse>(
      "/api/doc-register/search-query",
      { params: req },
    );
    queryResults.value = data.results;
  }
});

let docSearchTimer: ReturnType<typeof setTimeout> | null = null;
let filterSearchTimer: ReturnType<typeof setTimeout> | null = null;

function clearDocSearchTimer() {
  if (docSearchTimer !== null) {
    clearTimeout(docSearchTimer);
    docSearchTimer = null;
  }
}

function clearFilterSearchTimer() {
  if (filterSearchTimer !== null) {
    clearTimeout(filterSearchTimer);
    filterSearchTimer = null;
  }
}

async function selectEddrItem(item: EddrResult) {
  selectedEddrItem.value = item;
  queryResults.value = [];
  queryFilter.value = "";
  docSearchMode.value = "query";
  await docSearchLoading.execute();
}

function selectFileResult(item: QueryEntryResult) {
  const docNo =
    selectedEddrItem.value?.document_no ?? queryFilter.value.trim();
  const title = selectedEddrItem.value?.title ?? queryFilter.value.trim();
  emit("select", docNo, item.path || "", title);
  emit("close");
}

watch(docSearchQuery, (query) => {
  clearDocSearchTimer();
  selectedEddrItem.value = null;
  queryResults.value = [];
  queryFilter.value = "";
  if (!query.trim()) {
    docSearchResults.value = [];
    return;
  }
  docSearchMode.value = "eddr";
  docSearchTimer = setTimeout(() => {
    void docSearchLoading.execute();
  }, 250);
});

// Step 2 direct search by document number
watch(queryFilter, (val) => {
  clearFilterSearchTimer();
  if (queryResults.value.length > 0) return; // already loaded — just filter client-side
  if (!selectedEddrItem.value && val.trim().length >= 3) {
    filterSearchTimer = setTimeout(() => {
      docSearchMode.value = "query";
      void docSearchLoading.execute();
    }, 400);
  }
});

onBeforeUnmount(() => {
  clearDocSearchTimer();
  clearFilterSearchTimer();
});
</script>

<template>
  <div class="pk-modal-backdrop">
    <div class="pk-modal doc-search-modal modal-xl">
      <!-- Header -->
      <div class="pk-modal-header flex items-center justify-between pb-3 border-b">
        <div class="flex items-center gap-2">
          <h6 class="font-semibold text-lg flex items-center gap-2">
            <Search class="w-5 h-5 text-cyan-500" /> Search Document Register
          </h6>
          <span class="badge-up-to-date">Up to date</span>
        </div>
        <div class="flex items-center gap-1">
          <button
            @click="docSearchLoading.execute()"
            class="pk-btn-ghost text-sm flex items-center gap-1 px-2 py-1 rounded hover:bg-gray-100"
            title="Refresh database"
          >
            <RotateCw class="w-3.5 h-3.5" /> Refresh DB
          </button>
          <button
            @click="emit('close')"
            class="text-gray-400 hover:text-gray-600 p-1 rounded hover:bg-gray-100"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Body: flex column, no outer scroll — each step section scrolls internally -->
      <div class="doc-search-modal-body">
        <!-- Step 1 -->
        <div class="step-section step-section-1">
          <label class="step-label">
            <span class="step-badge step-badge-blue">Step 1</span>
            Search Document by Title in EDDR
          </label>
          <input
            v-model="docSearchQuery"
            @keyup.enter="docSearchMode = 'eddr'; docSearchLoading.execute();"
            type="text"
            class="pk-input w-full step-input"
            placeholder="Search by document title (e.g. 'Quench Column', 'Data sheet', 'P&ID')..."
            autocomplete="off"
          />
          <div class="step-results-area">
            <div v-if="docSearchResults.length" class="results-table-wrap">
              <table class="results-table">
                <thead>
                  <tr>
                    <th style="width: 22%">Document No</th>
                    <th>Title</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="item in docSearchResults"
                    :key="docResultKey(item)"
                    @click="selectEddrItem(item)"
                    class="results-row"
                    :class="{ 'row-selected': selectedEddrItem?.document_no === item.document_no }"
                  >
                    <td class="font-mono font-semibold text-gray-800 px-3 py-1" style="font-size:0.7rem">
                      {{ item.document_no }}
                    </td>
                    <td class="px-3 py-1 text-gray-700" style="font-size:0.73rem">{{ item.title }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="empty-state">
              <Search class="w-6 h-6 mx-auto mb-1 opacity-40" />
              <p>Type to search documents by title…</p>
            </div>
          </div>
        </div>

        <!-- Step 2 -->
        <div class="step-section step-section-2">
          <label class="step-label">
            <span class="step-badge step-badge-green">Step 2</span>
            Select File or Folder from SharePoint
          </label>
          <input
            v-model="queryFilter"
            type="text"
            class="pk-input w-full step-input"
            placeholder="Filter files/folders from sharepoint (e.g. '1060-2304-....')..."
            autocomplete="off"
          />
          <div class="step-results-area">
            <div v-if="filteredQueryResults.length" class="results-table-wrap">
              <table class="results-table">
                <thead>
                  <tr>
                    <th style="width: 33%">Name</th>
                    <th style="width: 8%">Type</th>
                    <th style="width: 11%">Modified</th>
                    <th style="width: 13%">Modified By</th>
                    <th style="width: 15%">Path</th>
                    <th style="width: 3rem"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="item in filteredQueryResults"
                    :key="queryResultKey(item)"
                    class="results-row"
                    @click="selectFileResult(item)"
                  >
                    <td class="px-3 py-1">
                      <div class="flex items-center gap-1.5 min-w-0">
                        <Folder v-if="item.item_type === 'Folder'" class="w-3 h-3 text-blue-500 shrink-0" />
                        <FileText v-else class="w-3 h-3 text-gray-400 shrink-0" />
                        <span class="font-medium text-gray-800 truncate" style="font-size:0.71rem" :title="item.name">
                          {{ item.name }}
                        </span>
                      </div>
                    </td>
                    <td class="px-2 py-1">
                      <span v-if="item.item_type === 'Folder'" class="type-badge type-folder">Folder</span>
                      <span v-else class="type-badge type-file">File</span>
                    </td>
                    <td class="px-2 py-1 text-gray-500 truncate max-w-0" style="font-size:0.68rem" :title="item.modified ?? undefined">
                      {{ item.modified || "—" }}
                    </td>
                    <td class="px-2 py-1 text-gray-500 truncate max-w-0" style="font-size:0.68rem" :title="item.modified_by ?? undefined">
                      {{ item.modified_by || "—" }}
                    </td>
                    <td class="px-2 py-1 text-gray-400 font-mono truncate max-w-0" style="font-size:0.66rem" :title="item.path ?? undefined">
                      {{ item.path || "—" }}
                    </td>
                    <td class="px-2 py-1 text-center">
                      <a
                        :href="itemUrl(item)"
                        target="_blank"
                        rel="noopener"
                        @click.stop
                        class="open-btn"
                        :class="{ 'open-btn-disabled': !item.path }"
                        :title="item.path ? `Open: ${item.name}` : 'No path available'"
                      >
                        <ExternalLink class="w-3 h-3" />
                      </a>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="empty-state">
              <FolderOpen class="w-6 h-6 mx-auto mb-1 opacity-40" />
              <p v-if="!selectedEddrItem && !queryFilter">
                Select a document above, or type a Document Number to search directly.
              </p>
              <p v-else-if="docSearchLoading.isLoading.value">Searching…</p>
              <p v-else>No files found.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-4 py-2.5 border-t bg-gray-50 flex items-center justify-between rounded-b-lg">
        <div class="flex items-center gap-2 text-xs text-gray-500">
          <InfoCircle class="w-3.5 h-3.5 text-blue-400 shrink-0" />
          <span>
            Step 1: Search by Document Title → click a document.
            Step 2: Pick a file → auto-fills fields.
            Or use <strong>Step 2 search directly</strong> to find files by Document Number.
          </span>
        </div>
        <button
          @click="emit('close')"
          class="pk-btn-secondary ml-4 px-3 py-1.5 text-sm bg-gray-700 text-white hover:bg-gray-800 rounded shrink-0"
        >
          Close
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── Modal shell ─────────────────────────────────────────────────────────── */
.doc-search-modal.modal-xl {
  width: 125vw;
  height: 94vh;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* nothing escapes the modal */
}

/* ── Body: flex column, no scroll — sections fill height ─────────────────── */
.doc-search-modal-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
}

/* ── Step sections ───────────────────────────────────────────────────────── */
.step-section {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* Step 1 gets ~38% of body height */
.step-section-1 {
  flex: 0 0 38%;
}

/* Step 2 takes the rest */
.step-section-2 {
  flex: 1;
}

/* The "results or empty-state" area inside each step fills remaining height */
.step-results-area {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  margin-top: 0.375rem;
}

/* ── Inputs ──────────────────────────────────────────────────────────────── */
.step-input {
  flex-shrink: 0;
}

/* ── Step label ──────────────────────────────────────────────────────────── */
.step-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  font-weight: 600;
  margin-bottom: 0.3rem;
  color: #374151;
  flex-shrink: 0;
}

.step-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.08rem 0.45rem;
  border-radius: 0.25rem;
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.step-badge-blue { background: #2563eb; color: #fff; }
.step-badge-green { background: #16a34a; color: #fff; }

/* ── Up to date badge ────────────────────────────────────────────────────── */
.badge-up-to-date {
  display: inline-flex;
  align-items: center;
  padding: 0.12rem 0.55rem;
  border-radius: 9999px;
  font-size: 0.68rem;
  font-weight: 600;
  background: #22c55e;
  color: #fff;
}

/* ── Results table wrapper — scrolls vertically only, NO horizontal scroll ─ */
.results-table-wrap {
  flex: 1;
  min-height: 0;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  overflow-x: hidden;  /* no horizontal scroll */
  overflow-y: auto;
}

.results-table {
  width: 100%;
  table-layout: fixed;   /* fixed layout enforces column widths & prevents overflow */
  border-collapse: collapse;
}

.results-table thead tr {
  position: sticky;
  top: 0;
  background: #f3f4f6;
  z-index: 10;
}

.results-table thead th {
  padding: 0.3rem 0.6rem;
  text-align: left;
  font-size: 0.63rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #6b7280;
  white-space: nowrap;
  overflow: hidden;
}

.results-table td {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.results-row {
  cursor: pointer;
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.1s;
}

.results-row:last-child { border-bottom: none; }
.results-row:hover { background: #f0f9ff; }
.row-selected { background: #dbeafe !important; }
.row-selected:hover { background: #bfdbfe !important; }

/* ── Type badges ─────────────────────────────────────────────────────────── */
.type-badge {
  display: inline-block;
  padding: 0.08rem 0.4rem;
  border-radius: 9999px;
  font-size: 0.6rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

.type-file   { background: #dcfce7; color: #15803d; }
.type-folder { background: #dbeafe; color: #1d4ed8; }

/* ── Open link button ────────────────────────────────────────────────────── */
.open-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 0.25rem;
  background: #ecfeff;
  color: #0891b2;
  border: 1px solid #a5f3fc;
  transition: background-color 0.15s;
}

.open-btn:hover { background: #cffafe; }

.open-btn-disabled {
  opacity: 0.3;
  pointer-events: none;
}

/* ── Empty state ─────────────────────────────────────────────────────────── */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  font-size: 0.78rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  padding: 1rem;
}
</style>
