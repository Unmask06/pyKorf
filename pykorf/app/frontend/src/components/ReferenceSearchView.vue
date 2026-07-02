<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from "vue";
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
import {
  searchEddr,
  searchQuery,
  rebuildDocRegisterDb,
  getDocRegisterStatus,
} from "../api/client";
import type {
  EddrResult,
  QueryEntryResult,
} from "../api/generated/types.gen";

const props = defineProps<{
  initialQuery?: string;
  standalone?: boolean;
}>();

const emit = defineEmits<{
  close: [];
  select: [name: string, link: string, description: string];
}>();

const spSiteUrl = ref("");
const isStale = ref(false);
const docSearchQuery = ref("");
const docSearchResults = ref<EddrResult[]>([]);
const queryResults = ref<QueryEntryResult[]>([]);
const selectedEddrItem = ref<EddrResult | null>(null);
const docSearchMode = ref<"eddr" | "query">("eddr");
const queryFilter = ref("");

// Step 2 sheet filter — "All" merges Process/Client/Mechanical.
const sheetFilter = ref<"All" | "Process" | "Client" | "Mechanical">("All");
const SHEET_OPTIONS = ["All", "Process", "Client", "Mechanical"] as const;

// Step 1 source filter — "All" merges FE / DE EDDR results.
const sourceFilter = ref<"All" | "FE" | "DE">("All");
const SOURCE_OPTIONS = ["All", "FE", "DE"] as const;

function docResultKey(item: EddrResult): string {
  return `${item.source ?? "FE"}:${item.document_no}`;
}

function queryResultKey(item: QueryEntryResult): string {
  return `${item.sheet ?? ""}:${item.name}:${item.path || ""}`;
}

function formatSharePointUrl(path: string): string {
  if (!path) return "#";
  if (path.startsWith("http")) return path;
  if (path.startsWith("sites/")) {
    const base = spSiteUrl.value.replace(/\/+$/, "");
    const clean = path.replace(/\\/g, "/");
    return base ? `${base}/${clean}` : clean;
  }
  return path;
}

function itemUrl(item: QueryEntryResult): string {
  if (!item.path) return "#";
  const folder = item.path.replace(/\/+$/, "").replace(/\\+$/, "");
  const full = `${folder}/${item.name}`;
  return formatSharePointUrl(full);
}

// Source badge class for Step 1 (FE = blue, DE = purple)
function sourceBadgeClass(source?: string): string {
  return source === "DE" ? "src-badge src-de" : "src-badge src-fe";
}

// Sheet badge class for Step 2
function sheetBadgeClass(sheet?: string | null): string {
  switch (sheet) {
    case "Process":
      return "sheet-badge sheet-process";
    case "Client":
      return "sheet-badge sheet-client";
    case "Mechanical":
      return "sheet-badge sheet-mechanical";
    default:
      return "sheet-badge sheet-unknown";
  }
}

// Per-source counts shown in the Step 1 filter tabs
const sourceCounts = computed(() => {
  const counts: Record<string, number> = { All: 0, FE: 0, DE: 0 };
  for (const item of docSearchResults.value) {
    counts.All += 1;
    const src = item.source ?? "FE";
    if (src in counts) counts[src] += 1;
  }
  return counts;
});

const filteredDocSearchResults = computed(() => {
  if (sourceFilter.value === "All") return docSearchResults.value;
  return docSearchResults.value.filter(
    (item) => (item.source ?? "FE") === sourceFilter.value,
  );
});

const filteredQueryResults = computed(() => {
  let rows = queryResults.value;
  if (sheetFilter.value !== "All") {
    rows = rows.filter((item) => item.sheet === sheetFilter.value);
  }
  if (!queryFilter.value) return rows;
  const q = queryFilter.value.toLowerCase();
  return rows.filter(
    (item) =>
      item.name.toLowerCase().includes(q) ||
      (item.path || "").toLowerCase().includes(q) ||
      (item.modified_by || "").toLowerCase().includes(q),
  );
});

// Per-sheet counts shown in the filter tabs
const sheetCounts = computed(() => {
  const counts: Record<string, number> = { All: 0, Process: 0, Client: 0, Mechanical: 0 };
  for (const item of queryResults.value) {
    counts.All += 1;
    if (item.sheet && item.sheet in counts) counts[item.sheet] += 1;
  }
  return counts;
});

const docSearchLoading = useLoading(async () => {
  if (docSearchMode.value === "eddr") {
    if (!docSearchQuery.value.trim()) {
      docSearchResults.value = [];
      return;
    }
    const response = await searchEddr({ query: { q: docSearchQuery.value } });
    docSearchResults.value = response.data!.results ?? [];
  } else {
    const docNo =
      selectedEddrItem.value?.document_no ??
      (!selectedEddrItem.value && queryFilter.value.trim()
        ? queryFilter.value.trim()
        : "");
    if (!docNo) {
      queryResults.value = [];
      return;
    }
    const response = await searchQuery({ query: { doc_no: docNo } });
    queryResults.value = response.data!.results ?? [];
  }
});

const refreshDbLoading = useLoading(async () => {
  await rebuildDocRegisterDb({ body: {} });
  isStale.value = false;
  // Re-search with existing query
  if (docSearchQuery.value.trim()) {
    await docSearchLoading.execute();
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
  sheetFilter.value = "All";
  sourceFilter.value = "All";
  docSearchMode.value = "query";
  await docSearchLoading.execute();
}

function selectFileResult(item: QueryEntryResult) {
  if (props.standalone) {
    const url = itemUrl(item);
    if (url && url !== "#") {
      window.open(url, "_blank");
    }
    return;
  }
  const docNo = selectedEddrItem.value?.document_no ?? queryFilter.value.trim();
  const title = selectedEddrItem.value?.title ?? queryFilter.value.trim();
  emit("select", docNo, itemUrl(item), title);
  emit("close");
}

watch(docSearchQuery, (query) => {
  clearDocSearchTimer();
  selectedEddrItem.value = null;
  queryResults.value = [];
  queryFilter.value = "";
  sheetFilter.value = "All";
  sourceFilter.value = "All";
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

onMounted(async () => {
  try {
    const response = await getDocRegisterStatus();
    const data = response.data!;
    spSiteUrl.value = data.sp_site_url ?? "";
    isStale.value = data.is_stale ?? false;
  } catch { /* ignore */ }

  if (props.initialQuery?.trim()) {
    docSearchQuery.value = props.initialQuery.trim();
    docSearchMode.value = "eddr";
    void docSearchLoading.execute();
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
      <div
        class="pk-modal-header flex items-center justify-between pb-3 border-b"
      >
        <div class="flex items-center gap-2">
          <h6 class="font-semibold text-lg flex items-center gap-2">
            <Search class="w-5 h-5 text-cyan-500" /> Search Document Register
          </h6>
          <span
            class="badge-status"
            :class="{ 'badge-up-to-date': !isStale, 'badge-stale': isStale }"
          >
            {{ isStale ? 'Stale — Refresh DB' : 'Up to date' }}
          </span>
        </div>
        <div class="flex items-center gap-1">
          <button
            @click="refreshDbLoading.execute()"
            class="pk-btn-ghost text-sm flex items-center gap-1.5 px-2 py-1 rounded hover:bg-gray-100"
            title="Refresh database"
            :disabled="refreshDbLoading.isLoading.value"
          >
            <span
              v-if="refreshDbLoading.isLoading.value"
              class="refresh-spinner"
              aria-label="Refreshing"
            />
            <RotateCw v-else class="w-3.5 h-3.5" />
            <span :class="{ 'refresh-loading-text': refreshDbLoading.isLoading.value }">
              {{ refreshDbLoading.isLoading.value ? "Refreshing…" : "Refresh DB" }}
            </span>
          </button>
          <button
            @click="emit('close')"
            class="text-gray-400 hover:text-gray-600 p-1 rounded hover:bg-gray-100"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
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
            Search Document by Title in FEED (FE) / Detailed Engineering (DE) EDDR 
          </label>
          <div class="step1-controls">
            <input
              v-model="docSearchQuery"
              @keyup.enter="
                docSearchMode = 'eddr';
                docSearchLoading.execute();
              "
              type="text"
              class="pk-input w-full step-input step1-search-input"
              placeholder="Search by document title (e.g. 'Quench Column', 'Data sheet', 'P&ID')..."
              autocomplete="off"
            />
            <div class="source-tabs">
              <button
                v-for="opt in SOURCE_OPTIONS"
                :key="opt"
                type="button"
                class="source-tab"
                :class="{
                  'source-tab-active': sourceFilter === opt,
                  'source-tab-fe': opt === 'FE',
                  'source-tab-de': opt === 'DE',
                }"
                @click="sourceFilter = opt"
              >
                {{ opt }}
                <span class="source-tab-count">{{ sourceCounts[opt] ?? 0 }}</span>
              </button>
            </div>
          </div>
          <div class="step-results-area">
            <div v-if="filteredDocSearchResults.length" class="results-table-wrap">
              <table class="results-table">
                <thead>
                  <tr>
                    <th style="width: 6%">Src</th>
                    <th style="width: 22%">Document No</th>
                    <th>Title</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="item in filteredDocSearchResults"
                    :key="docResultKey(item)"
                    @click="selectEddrItem(item)"
                    class="results-row"
                    :class="{
                      'row-selected':
                        selectedEddrItem?.document_no === item.document_no &&
                        (selectedEddrItem?.source ?? 'FE') === (item.source ?? 'FE'),
                    }"
                  >
                    <td class="px-2 py-1">
                      <span :class="sourceBadgeClass(item.source)">
                        {{ item.source ?? 'FE' }}
                      </span>
                    </td>
                    <td
                      class="font-mono font-semibold text-gray-800 px-3 py-1"
                      style="font-size: 0.7rem"
                    >
                      <div>{{ item.document_no }}</div>
                      <div
                        v-if="item.source === 'DE' && item.contractor_doc_no"
                        class="font-normal text-gray-400"
                        style="font-size: 0.62rem"
                        :title="`Contractor: ${item.contractor_doc_no}`"
                      >
                        Ctr: {{ item.contractor_doc_no }}
                      </div>
                    </td>
                    <td
                      class="px-3 py-1 text-gray-700"
                      style="font-size: 0.73rem"
                    >
                      {{ item.title }}
                    </td>
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
          <div class="step2-controls">
            <input
              v-model="queryFilter"
              type="text"
              class="pk-input step-input step2-filter-input"
              placeholder="Filter files/folders (e.g. '1060-2304-....')..."
              autocomplete="off"
            />
            <div class="sheet-tabs">
              <button
                v-for="opt in SHEET_OPTIONS"
                :key="opt"
                type="button"
                class="sheet-tab"
                :class="{ 'sheet-tab-active': sheetFilter === opt }"
                @click="sheetFilter = opt"
              >
                {{ opt }}
                <span class="sheet-tab-count">{{ sheetCounts[opt] ?? 0 }}</span>
              </button>
            </div>
          </div>
          <div class="step-results-area">
            <div v-if="filteredQueryResults.length" class="results-table-wrap">
              <table class="results-table">
                <thead>
                  <tr>
                    <th style="width: 36%">Name</th>
                    <th style="width: 7%">Sheet</th>
                    <th style="width: 6%">Type</th>
                    <th style="width: 11%">Modified</th>
                    <th style="width: 12%">Modified By</th>
                    <th style="width: 22%">Path</th>
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
                        <Folder
                          v-if="item.item_type === 'Folder'"
                          class="w-3 h-3 text-blue-500 shrink-0"
                        />
                        <FileText
                          v-else
                          class="w-3 h-3 text-gray-400 shrink-0"
                        />
                        <span
                          class="font-medium text-gray-800 truncate"
                          style="font-size: 0.71rem"
                          :title="item.name"
                        >
                          {{ item.name }}
                        </span>
                      </div>
                    </td>
                    <td class="px-2 py-1">
                      <span :class="sheetBadgeClass(item.sheet)">
                        {{ item.sheet || '—' }}
                      </span>
                    </td>
                    <td class="px-2 py-1">
                      <span
                        v-if="item.item_type === 'Folder'"
                        class="type-badge type-folder"
                        >Folder</span
                      >
                      <span v-else class="type-badge type-file">File</span>
                    </td>
                    <td
                      class="px-2 py-1 text-gray-500 truncate max-w-0"
                      style="font-size: 0.68rem"
                      :title="item.modified ?? undefined"
                    >
                      {{ item.modified || "—" }}
                    </td>
                    <td
                      class="px-2 py-1 text-gray-500 truncate max-w-0"
                      style="font-size: 0.68rem"
                      :title="item.modified_by ?? undefined"
                    >
                      {{ item.modified_by || "—" }}
                    </td>
                    <td
                      class="px-2 py-1 text-gray-400 font-mono truncate max-w-0"
                      style="font-size: 0.66rem"
                      :title="item.path ?? undefined"
                    >
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
                        :title="
                          item.path ? `Open: ${item.name}` : 'No path available'
                        "
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
                Select a document above, or type a Document Number to search
                directly.
              </p>
              <div v-else-if="docSearchLoading.isLoading.value" class="searching-loader">
                <span class="searching-spinner" aria-label="Searching" />
                <span class="searching-text">Searching…</span>
              </div>
              <p v-else>No files found.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div
        class="px-4 py-2.5 border-t bg-gray-50 flex items-center justify-between rounded-b-lg"
      >
        <div class="flex items-center gap-2 text-xs text-gray-500">
          <InfoCircle class="w-3.5 h-3.5 text-blue-400 shrink-0" />
          <span>
            Step 1: Search by Document Title → click a document. Step 2: Pick a
            file → auto-fills fields. Use the
            <strong>Sheet tabs</strong> to filter by Process / Client /
            Mechanical.
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
  width: 85vw !important;
  max-width: 92vw !important;
  height: 80vh !important;
  max-height: 92vh !important;
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

/* ── Step 1 controls: search input + source tabs (All/FE/DE) ─────────────── */
.step1-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.step1-search-input {
  flex: 1;
  min-width: 0;
}

.source-tabs {
  display: flex;
  gap: 0.2rem;
  flex-shrink: 0;
}

.source-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.18rem 0.5rem;
  border-radius: 0.375rem;
  font-size: 0.66rem;
  font-weight: 600;
  border: 1px solid #e5e7eb;
  background: #fff;
  color: #6b7280;
  cursor: pointer;
  transition: background-color 0.12s, color 0.12s, border-color 0.12s;
  white-space: nowrap;
}

.source-tab:hover {
  background: #f3f4f6;
}

.source-tab-active {
  color: #fff;
  border-color: transparent;
}

.source-tab-active.source-tab-fe {
  background: #1d4ed8;
}

.source-tab-active.source-tab-de {
  background: #6d28d9;
}

.source-tab-active:not(.source-tab-fe):not(.source-tab-de) {
  background: #2563eb;
}

.source-tab-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.1rem;
  padding: 0 0.25rem;
  border-radius: 9999px;
  font-size: 0.58rem;
  font-weight: 700;
  background: rgba(0, 0, 0, 0.08);
}

.source-tab-active .source-tab-count {
  background: rgba(255, 255, 255, 0.25);
}

/* ── Step 2 controls: filter input + sheet tabs ──────────────────────────── */
.step2-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.step2-filter-input {
  flex: 1;
  min-width: 0;
}

.sheet-tabs {
  display: flex;
  gap: 0.2rem;
  flex-shrink: 0;
}

.sheet-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.18rem 0.5rem;
  border-radius: 0.375rem;
  font-size: 0.66rem;
  font-weight: 600;
  border: 1px solid #e5e7eb;
  background: #fff;
  color: #6b7280;
  cursor: pointer;
  transition: background-color 0.12s, color 0.12s, border-color 0.12s;
  white-space: nowrap;
}

.sheet-tab:hover {
  background: #f3f4f6;
}

.sheet-tab-active {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}

.sheet-tab-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.1rem;
  padding: 0 0.25rem;
  border-radius: 9999px;
  font-size: 0.58rem;
  font-weight: 700;
  background: rgba(0, 0, 0, 0.08);
}

.sheet-tab-active .sheet-tab-count {
  background: rgba(255, 255, 255, 0.25);
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

.step-badge-blue {
  background: #2563eb;
  color: #fff;
}
.step-badge-green {
  background: #16a34a;
  color: #fff;
}

/* ── Status badge ────────────────────────────────────────────────────── */
.badge-status {
  display: inline-flex;
  align-items: center;
  padding: 0.12rem 0.55rem;
  border-radius: 9999px;
  font-size: 0.68rem;
  font-weight: 600;
}

.badge-up-to-date {
  background: #22c55e;
  color: #fff;
}

.badge-stale {
  background: #f59e0b;
  color: #fff;
}

/* ── Source badge (Step 1: FE / DE) ──────────────────────────────────────── */
.src-badge {
  display: inline-block;
  padding: 0.08rem 0.4rem;
  border-radius: 0.25rem;
  font-size: 0.6rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

.src-fe {
  background: #dbeafe;
  color: #1d4ed8;
}

.src-de {
  background: #ede9fe;
  color: #6d28d9;
}

/* ── Sheet badge (Step 2: Process / Client / Mechanical) ─────────────────── */
.sheet-badge {
  display: inline-block;
  padding: 0.08rem 0.4rem;
  border-radius: 9999px;
  font-size: 0.58rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

.sheet-process {
  background: #dcfce7;
  color: #15803d;
}

.sheet-client {
  background: #dbeafe;
  color: #1d4ed8;
}

.sheet-mechanical {
  background: #ffedd5;
  color: #c2410c;
}

.sheet-unknown {
  background: #f3f4f6;
  color: #6b7280;
}

/* ── Results table wrapper — scrolls vertically only, NO horizontal scroll ─ */
.results-table-wrap {
  flex: 1;
  min-height: 0;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  overflow-x: hidden; /* no horizontal scroll */
  overflow-y: auto;
}

.results-table {
  width: 100%;
  table-layout: fixed; /* fixed layout enforces column widths & prevents overflow */
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

.results-row:last-child {
  border-bottom: none;
}
.results-row:hover {
  background: #f0f9ff;
}
.row-selected {
  background: #dbeafe !important;
}
.row-selected:hover {
  background: #bfdbfe !important;
}

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

.type-file {
  background: #dcfce7;
  color: #15803d;
}
.type-folder {
  background: #dbeafe;
  color: #1d4ed8;
}

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

.open-btn:hover {
  background: #cffafe;
}

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

/* ── Refresh DB button — high-contrast inline spinner ─────────────────────── */
.refresh-spinner {
  display: inline-block;
  width: 0.95rem;
  height: 0.95rem;
  border: 2.5px solid rgba(8, 145, 178, 0.2);
  border-top-color: #0891b2;
  border-right-color: #0891b2;
  border-radius: 50%;
  animation: refresh-spin 0.7s linear infinite;
  flex-shrink: 0;
}

.refresh-loading-text {
  color: #0891b2;
  font-weight: 600;
}

@keyframes refresh-spin {
  to { transform: rotate(360deg); }
}

/* ── Searching loader (Step 2 empty state while loading) ─────────────────── */
.searching-loader {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.5rem 1rem;
  background: #ecfdf5;
  border: 1px solid #34d399;
  border-radius: 9999px;
  box-shadow: 0 1px 3px rgba(16, 185, 129, 0.15);
}

.searching-spinner {
  display: inline-block;
  width: 1.15rem;
  height: 1.15rem;
  border: 3px solid rgba(16, 185, 129, 0.25);
  border-top-color: #059669;
  border-right-color: #059669;
  border-radius: 50%;
  animation: refresh-spin 0.65s linear infinite;
  flex-shrink: 0;
}

.searching-text {
  color: #047857;
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  animation: searching-pulse 1.1s ease-in-out infinite;
}

@keyframes searching-pulse {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.55; }
}
</style>
