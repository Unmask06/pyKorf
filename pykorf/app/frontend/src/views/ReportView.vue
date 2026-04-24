<script setup lang="ts">
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  Clipboard,
  FileSpreadsheet,
  FileText,
  Folder,
  FolderOpen,
  Layers,
  X,
} from "lucide-vue-next";
import { onMounted, ref } from "vue";
import {
  generateReport,
  batchReport,
  getPreferences,
  getErrorMessage,
  korfExcelStatus,
} from "../api/client";
import PathBrowser from "../components/PathBrowser.vue";
import { useLoading } from "../composables/useLoading";
import { useToastStore } from "../composables/useToast";
import { useSessionStore } from "../stores/session";
import type {
  BatchReportRequest,
  GenerateReportRequest,
} from "../api/generated/types.gen";

const session = useSessionStore();
const toast = useToastStore();

const reportPath = ref("");
const batchFolder = ref("");
const singleReport = ref(false);
const showBatchBrowser = ref(false);

// KORF Excel source
const korfExcelPath = ref("");
const reportSource = ref<"korf" | "pykorf" | null>(null);
const korfIsStale = ref(false);
const korfExists = ref(false);

const genLoading = useLoading(async () => {
  const req: GenerateReportRequest = {
    report_path: reportPath.value || null,
    korf_excel_path: korfExcelPath.value || null,
  };
  const res = await generateReport({ body: req });
  if (!res.data?.success) {
    throw new Error(res.data?.errors?.[0] || 'Report generation failed');
  }
  // Detect source from response message
  const msg = res.data.messages?.[0]?.message || "";
  reportSource.value = msg.includes("KORF report") ? "korf" : "pykorf";
  return res.data;
});

const batchLoading = useLoading(async () => {
  const req: BatchReportRequest = {
    batch_folder: batchFolder.value || null,
    single_report: singleReport.value,
  };
  const res = await batchReport({ body: req });
  if (!res.data?.success) {
    throw new Error(res.data?.errors?.[0] || 'Batch report failed');
  }
  return res.data;
});

async function generate() {
  try {
    await genLoading.execute();
    if (reportSource.value === "korf") {
      toast.success("KORF Excel report generated (multi-case).");
    } else {
      toast.success("Report generated successfully.");
    }
  } catch (err: unknown) {
    toast.error(getErrorMessage(err, "An unexpected error occurred."));
  }
}

async function doBatch() {
  try {
    await batchLoading.execute();
    toast.success("Batch report generated.");
  } catch (err: unknown) {
    toast.error(getErrorMessage(err, "An unexpected error occurred."));
  }
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text);
  toast.info("Path copied to clipboard.");
}

onMounted(async () => {
  if (!session.isLoaded) return;
  const kdf = session.kdfPath;
  if (kdf) {
    const sep = kdf.includes("\\") ? "\\" : "/";
    const lastSep = Math.max(kdf.lastIndexOf("\\"), kdf.lastIndexOf("/"));
    const folder = kdf.substring(0, lastSep);
    const filename = kdf.substring(lastSep + 1);
    const stem = filename.includes(".")
      ? filename.substring(0, filename.lastIndexOf("."))
      : filename;
    reportPath.value = `${folder}${sep}${stem}_report.xlsx`;
    korfExcelPath.value = `${folder}${sep}${stem}.xlsx`;
  }
  try {
    const response = await getPreferences();
    if (response.data!.last_batch_folder_path) {
      batchFolder.value = response.data!.last_batch_folder_path;
    }
  } catch {
    // ignore — prefill is best-effort
  }
  // Check KORF Excel staleness
  try {
    const status = await korfExcelStatus();
    if (status.data) {
      korfExists.value = !!status.data.korf_excel_path;
      korfIsStale.value = status.data.is_stale || false;
    }
  } catch {
    // ignore — staleness check is best-effort
  }
});
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <!-- Column 1: Generate Report -->
    <div class="pk-card">
      <div class="pk-card-header flex items-center gap-1">
        <FileText class="w-4 h-4 text-green-600" /> Generate Report
      </div>
      <div class="p-4 flex flex-col">
        <div class="space-y-3">
          <div>
            <label class="pk-label">Output File</label>
            <div class="flex">
              <span
                class="flex items-center justify-center px-3 py-1.5 text-sm bg-gray-100 border border-r-0 border-gray-300 rounded-l-md"
              >
                <FileText class="w-4 h-4 text-gray-500" />
              </span>
              <textarea
                v-model="reportPath"
                class="pk-input-mono resize-none rounded-none w-full"
                rows="2"
                style="font-size: 0.82rem"
                readonly
              />
              <button
                type="button"
                @click="copyToClipboard(reportPath)"
                class="flex items-center justify-center px-3 py-1.5 text-sm border border-l-0 border-gray-300 rounded-r-md bg-gray-100 hover:bg-gray-50"
                title="Copy path"
              >
                <Clipboard class="w-4 h-4" />
              </button>
            </div>
            <div class="pk-hint">Auto-derived from the open KDF file.</div>
          </div>
          <div>
            <label class="pk-label flex items-center gap-2">
              KORF Excel File
              <span class="text-xs text-gray-400 font-normal">(optional)</span>
            </label>
            <div class="flex">
              <span
                class="flex items-center justify-center px-3 py-1.5 text-sm bg-gray-100 border border-r-0 border-gray-300 rounded-l-md"
              >
                <FileSpreadsheet class="w-4 h-4 text-gray-500" />
              </span>
              <textarea
                v-model="korfExcelPath"
                class="pk-input-mono resize-none rounded-none w-full"
                rows="2"
                placeholder="Auto-detected from KDF folder"
                style="font-size: 0.82rem"
              />
              <button
                v-if="korfExcelPath"
                type="button"
                @click="korfExcelPath = ''"
                class="flex items-center justify-center px-2 py-1.5 text-sm border border-l-0 border-gray-300 rounded-r-md bg-gray-100 hover:bg-gray-50 text-gray-500"
                title="Clear"
              >
                <X class="w-3.5 h-3.5" />
              </button>
            </div>
            <div class="pk-hint">
              To export from KORF: <strong>Hydraulics &gt; Results &gt; View
              Excel Report</strong>, then save the <strong>XML</strong> as
              <strong>XLSX</strong> with the same name as the KDF file. Enables
              multi-case reports with per-case sheets.
            </div>
          </div>
        </div>
        <div class="mt-3 flex items-center gap-2 flex-wrap">
          <template v-if="korfExists && korfIsStale">
            <AlertTriangle class="w-4 h-4 text-amber-600 shrink-0" />
            <span
              class="text-xs font-medium text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-0.5"
              >Stale KORF Excel Report</span
            >
          </template>
          <template v-else>
            <CheckCircle2
              v-if="reportSource === 'korf'"
              class="w-4 h-4 text-green-600 shrink-0"
            />
            <span
              v-if="reportSource === 'korf'"
              class="text-xs font-medium text-green-700 bg-green-50 border border-green-200 rounded px-2 py-0.5"
              >KORF Excel source</span
            >
            <CheckCircle2
              v-if="reportSource === 'pykorf'"
              class="w-4 h-4 text-blue-600 shrink-0"
            />
            <span
              v-if="reportSource === 'pykorf'"
              class="text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded px-2 py-0.5"
              >pyKorf default source</span
            >
          </template>
        </div>
        <div v-if="korfExists && korfIsStale" class="mt-2 text-xs text-amber-600">
          KORF file has been updated after report generation. Regenerate the report from KORF again.
        </div>
        <button
          @click="generate"
          class="mt-3 w-full bg-green-600 text-white rounded py-1.5 text-sm hover:bg-green-700 flex items-center justify-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="genLoading.isLoading.value || (korfExists && korfIsStale)"
          :title="korfExists && korfIsStale ? 'KORF Excel is stale — regenerate from KORF first' : ''"
        >
          <span v-if="genLoading.isLoading.value" class="pk-spinner" />
          <ArrowDownRight class="w-4 h-4" /> Generate Report
        </button>
      </div>
    </div>

    <!-- Column 2: Batch Report + Export/Import (coming soon) -->
    <div class="space-y-4">
      <!-- Batch Report -->
      <div class="pk-card">
        <div class="pk-card-header flex items-center gap-1">
          <Layers class="w-4 h-4 text-gray-500" /> Batch Report
        </div>
        <div class="p-4 flex flex-col">
          <div class="mb-3">
            <label class="pk-label">KDF Folder</label>
            <div class="flex">
              <span
                class="flex items-center justify-center px-3 py-1.5 text-sm bg-gray-100 border border-r-0 border-gray-300 rounded-l-md"
              >
                <Folder class="w-4 h-4 text-gray-500" />
              </span>
              <textarea
                v-model="batchFolder"
                class="pk-input-mono resize-none rounded-none w-full"
                rows="2"
                placeholder="Folder containing .kdf files"
                style="font-size: 0.82rem"
              />
              <button
                type="button"
                @click="showBatchBrowser = true"
                class="flex items-center justify-center px-3 py-1.5 text-sm border border-l-0 border-gray-300 rounded-r-md bg-gray-100 hover:bg-gray-50"
                title="Browse folder"
              >
                <FolderOpen class="w-4 h-4" />
              </button>
            </div>
            <div class="pk-hint">
              All <code class="bg-gray-100 rounded px-1">.kdf</code> files in
              this folder will be processed into a combined report.
            </div>
          </div>
          <div class="mb-3 flex items-center gap-2 text-sm text-gray-700">
            <input
              id="singleReport"
              type="checkbox"
              v-model="singleReport"
              class="h-4 w-4 rounded border-gray-300 text-green-600 focus:ring-green-500"
            />
            <label for="singleReport"
              >Generate individual report for each KDF</label
            >
          </div>
          <button
            @click="doBatch"
            class="w-full bg-gray-500 text-white rounded py-1.5 text-sm hover:bg-gray-600 flex items-center justify-center gap-1 disabled:opacity-50"
            :disabled="batchLoading.isLoading.value"
          >
            <span v-if="batchLoading.isLoading.value" class="pk-spinner" />
            <Layers class="w-4 h-4" /> Generate Batch Report
          </button>
        </div>
      </div>

      <!-- Export to Excel (Coming Soon) -->
      <div class="pk-card opacity-60">
        <div class="pk-card-header flex items-center gap-1">
          <ArrowUpRight class="w-4 h-4 text-blue-600" /> Export to Excel
          <span
            class="ml-auto text-[10px] font-semibold uppercase tracking-wider text-gray-400 bg-gray-100 border border-gray-200 rounded px-1.5 py-0.5"
            >Coming Soon</span
          >
        </div>
        <div class="p-4 flex flex-col items-center justify-center text-gray-400 text-sm py-8">
          <ArrowUpRight class="w-8 h-8 mb-2 opacity-30" />
          <span>Export model to Excel — coming soon</span>
        </div>
      </div>

      <!-- Import from Excel (Coming Soon) -->
      <div class="pk-card opacity-60">
        <div class="pk-card-header flex items-center gap-1">
          <ArrowDownRight class="w-4 h-4 text-yellow-500" /> Import from Excel
          <span
            class="ml-auto text-[10px] font-semibold uppercase tracking-wider text-gray-400 bg-gray-100 border border-gray-200 rounded px-1.5 py-0.5"
            >Coming Soon</span
          >
        </div>
        <div class="p-4 flex flex-col items-center justify-center text-gray-400 text-sm py-8">
          <ArrowDownRight class="w-8 h-8 mb-2 opacity-30" />
          <span>Import model from Excel — coming soon</span>
        </div>
      </div>
    </div>
  </div>

  <PathBrowser
    v-if="showBatchBrowser"
    filter="folder"
    @close="showBatchBrowser = false"
    @select="
      (p: string) => {
        batchFolder = p;
        showBatchBrowser = false;
      }
    "
  />
</template>
