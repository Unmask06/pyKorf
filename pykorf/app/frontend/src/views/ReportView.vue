<script setup lang="ts">
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  Clipboard,
  FileText,
  Folder,
  FolderOpen,
  Layers,
  Settings,
  X,
} from "lucide-vue-next";
import { computed, onMounted, ref, watch } from "vue";
import {
  generateReport,
  batchReport,
  getPreferences,
  getErrorMessage,
  korfExcelStatus,
  saveProjectInfo,
} from "../api/client";
import PathBrowser from "../components/PathBrowser.vue";
import ReportCustomizeModal from "../components/ReportCustomizeModal.vue";
import ReportModeToggle from "../components/ReportModeToggle.vue";
import { useLoading } from "../composables/useLoading";
import { useToastStore } from "../composables/useToast";
import { useSessionStore } from "../stores/session";
import type {
  BatchReportRequest,
  GenerateReportRequest,
  ProjectInfoResponse,
  SmartDefaultsResponse,
} from "../api/generated/types.gen";

interface ProjectInfoRequiredResponse {
  project_info_required: boolean;
  project_info: ProjectInfoResponse;
  smart_defaults: SmartDefaultsResponse;
  required_fields: string[];
  incomplete_fields: string[];
}

const session = useSessionStore();
const toast = useToastStore();

// Project info modal (shown when report generation requires project info)
const showProjectInfoModal = ref(false);
const projectInfoRequired = ref<ProjectInfoRequiredResponse | null>(null);
const editInfo = ref<ProjectInfoResponse>({});
const smartDefaults = ref<SmartDefaultsResponse>({});
const pendingReportReq = ref<GenerateReportRequest | null>(null);
const saveProjectLoading = ref(false);

function isRequired(field: string): boolean {
  return projectInfoRequired.value?.incomplete_fields?.includes(field) ?? false;
}

// Report mode toggle
const isMultiCase = ref(false);
const isBatchMultiCase = ref(false);

// Multi-case status (auto-detected via backend)
const korfIsStale = ref(false);
const korfExists = ref(false);

// Batch report
const batchFolder = ref("");
const singleReport = ref(false);
const showBatchBrowser = ref(false);

// Batch multi-case validation
const batchValidCount = ref(0);
const batchTotalCount = ref(0);
const batchProblems = ref<string[]>([]);
const batchValidating = ref(false);

// Report column customization
const showCustomizeModal = ref(false);
const pipeColumns = ref<string[]>([]);

const reportPath = computed(() => {
  if (!session.kdfPath) return "";
  const kdf = session.kdfPath;
  const sep = kdf.includes("\\") ? "\\" : "/";
  const lastSep = Math.max(kdf.lastIndexOf("\\"), kdf.lastIndexOf("/"));
  const folder = kdf.substring(0, lastSep);
  const filename = kdf.substring(lastSep + 1);
  const stem = filename.includes(".")
    ? filename.substring(0, filename.lastIndexOf("."))
    : filename;
  const suffix = isMultiCase.value ? "_multi-case_report.xlsx" : "_report.xlsx";
  return `${folder}${sep}${stem}${suffix}`;
});

const canGenerate = computed(() => {
  if (genLoading.isLoading.value) return false;
  if (isMultiCase.value) {
    if (!korfExists.value) return false;
    if (korfIsStale.value) return false;
  }
  return true;
});

const canBatchGenerate = computed(() => {
  if (batchLoading.isLoading.value) return false;
  if (batchValidating.value) return false;
  if (!batchFolder.value) return false;
  if (isBatchMultiCase.value && batchValidCount.value === 0) return false;
  return true;
});

const batchTooltip = computed(() => {
  if (!batchFolder.value) return "";
  if (isBatchMultiCase.value && batchValidCount.value === 0) {
    return "No KDF files have valid KORF Excel reports";
  }
  return "";
});

const generateTooltip = computed(() => {
  if (isMultiCase.value) {
    if (!korfExists.value)
      return "Multi-case requires a KORF Excel report. Generate it from KORF first.";
    if (korfIsStale.value)
      return "KORF Excel is stale — regenerate from KORF first";
  }
  return "";
});

const genLoading = useLoading(async () => {
  const req: GenerateReportRequest = {
    report_path: reportPath.value || null,
    mode: isMultiCase.value ? "multi" : "single",
    pipe_columns: pipeColumns.value.length > 0 ? pipeColumns.value : undefined,
  };
  const res = await generateReport({ body: req });
  if (!res.data) {
    throw new Error("Report generation failed");
  }
  // Check if project info is required
  if ("project_info_required" in res.data && res.data.project_info_required) {
    const projResp = res.data as ProjectInfoRequiredResponse;
    projectInfoRequired.value = projResp;
    editInfo.value = { ...(projResp.project_info || {}) };
    smartDefaults.value = projResp.smart_defaults || {};
    pendingReportReq.value = req;
    showProjectInfoModal.value = true;
    return null;
  }
  if ("success" in res.data && !res.data.success) {
    throw new Error(res.data.errors?.[0] || "Report generation failed");
  }
  return res.data;
});

const batchLoading = useLoading(async () => {
  const req: BatchReportRequest = {
    batch_folder: batchFolder.value || null,
    single_report: singleReport.value,
    mode: isBatchMultiCase.value ? "multi" : "single",
    pipe_columns: pipeColumns.value.length > 0 ? pipeColumns.value : undefined,
  };
  const res = await batchReport({ body: req });
  if (!res.data?.success) {
    throw new Error(res.data?.errors?.[0] || "Batch report failed");
  }
  return res.data;
});

async function generate() {
  try {
    const result = await genLoading.execute();
    if (result === null) return; // project info modal shown
    if (isMultiCase.value) {
      toast.success("Multi-case report generated from KORF Excel.");
    } else {
      toast.success("Single-case report generated from KDF.");
    }
  } catch (err: unknown) {
    toast.error(getErrorMessage(err, "An unexpected error occurred."));
  }
}

async function saveProjectAndRetry() {
  saveProjectLoading.value = true;
  try {
    await saveProjectInfo({ body: editInfo.value });
    showProjectInfoModal.value = false;
    toast.success("Project info saved. Generating report...");
    if (pendingReportReq.value) {
      const res = await generateReport({ body: pendingReportReq.value });
      if (res.data && "success" in res.data && res.data.success) {
        toast.success("Report generated successfully.");
      } else if (res.data && "errors" in res.data) {
        throw new Error(res.data.errors?.[0] || "Report generation failed");
      }
    }
  } catch (err: unknown) {
    toast.error(
      getErrorMessage(err, "Failed to save project info or generate report."),
    );
  } finally {
    saveProjectLoading.value = false;
  }
}

async function doBatch() {
  try {
    const result = await batchLoading.execute();
    const skipCount =
      result?.messages?.filter(
        (m) =>
          m.type === "warning" &&
          (m.message?.includes("skipped") ||
            m.message?.includes("missing") ||
            m.message?.includes("stale")),
      ).length || 0;
    if (skipCount > 0) {
      toast.warning(
        `Batch report generated. ${skipCount} KDF(s) skipped (KORF Excel missing/stale).`,
      );
    } else {
      toast.success("Batch report generated.");
    }
  } catch (err: unknown) {
    toast.error(getErrorMessage(err, "An unexpected error occurred."));
  }
}

async function runBatchValidation() {
  if (!batchFolder.value || !isBatchMultiCase.value) return;
  batchValidating.value = true;
  try {
    const req: BatchReportRequest = {
      batch_folder: batchFolder.value || null,
      single_report: false,
      mode: "multi",
      validate_only: true,
    };
    const res = await batchReport({ body: req });
    if (res.data) {
      const problems: string[] = [];
      let validCount = 0;
      let totalCount = 0;
      for (const msg of res.data.messages || []) {
        if (msg.type === "info" && msg.message) {
          // Parse "X of Y KDF files have valid KORF Excel"
          const match = msg.message.match(/(\d+)\s+of\s+(\d+)/);
          if (match) {
            validCount = parseInt(match[1]);
            totalCount = parseInt(match[2]);
          }
        } else if (msg.type === "warning" && msg.message) {
          problems.push(msg.message);
        }
      }
      batchValidCount.value = validCount;
      batchTotalCount.value = totalCount;
      batchProblems.value = problems;
    }
  } catch {
    batchValidCount.value = 0;
    batchTotalCount.value = 0;
    batchProblems.value = [];
  } finally {
    batchValidating.value = false;
  }
}

watch(isBatchMultiCase, (val) => {
  if (val && batchFolder.value) {
    runBatchValidation();
  } else {
    batchProblems.value = [];
  }
});

watch(batchFolder, (val) => {
  if (val && isBatchMultiCase.value) {
    runBatchValidation();
  } else {
    batchProblems.value = [];
  }
});

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text);
  toast.info("Path copied to clipboard.");
}

onMounted(async () => {
  if (!session.isLoaded) return;
  try {
    const response = await getPreferences();
    if (response.data!.last_batch_folder_path) {
      batchFolder.value = response.data!.last_batch_folder_path;
    }
  } catch {
    // ignore — prefill is best-effort
  }
  // Check KORF Excel status (for multi-case mode)
  await checkKorfExcelStatus();
});

async function checkKorfExcelStatus() {
  try {
    const status = await korfExcelStatus();
    if (status.data) {
      korfExists.value = !!status.data.korf_excel_path;
      korfIsStale.value = status.data.is_stale || false;
    }
  } catch {
    // ignore — staleness check is best-effort
  }
}

function onToggleMultiCase(value: boolean) {
  isMultiCase.value = value;
  if (value) {
    checkKorfExcelStatus();
  }
}
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
                :value="reportPath"
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
            <div class="pk-hint flex items-center gap-1">
              Auto-derived from KDF file.
              <span v-if="isMultiCase" class="text-xs text-gray-500"
                >(multi-case)</span
              >
            </div>
          </div>

          <!-- Report Mode Toggle -->
          <ReportModeToggle
            v-model="isMultiCase"
            @update:model-value="onToggleMultiCase"
          />

          <!-- Multi-case status & instructions -->
          <div
            v-if="isMultiCase"
            class="bg-blue-50 border border-blue-200 rounded p-3"
          >
            <div class="flex items-center gap-2">
              <CheckCircle2
                v-if="korfExists && !korfIsStale"
                class="w-4 h-4 text-green-600 shrink-0"
              />
              <AlertTriangle
                v-else
                class="w-4 h-4 shrink-0"
                :class="
                  korfExists && korfIsStale ? 'text-amber-600' : 'text-red-600'
                "
              />
              <span
                class="text-xs font-medium"
                :class="
                  korfExists && !korfIsStale
                    ? 'text-green-700'
                    : korfExists && korfIsStale
                      ? 'text-amber-700'
                      : 'text-red-700'
                "
              >
                {{
                  korfExists && !korfIsStale
                    ? "KORF Excel detected and ready"
                    : korfExists && korfIsStale
                      ? "KORF Excel is stale — regenerate from KORF"
                      : "KORF Excel not found in KDF folder"
                }}
              </span>
            </div>
            <div class="pk-hint mt-1">
              To export from KORF:
              <strong>Hydraulics &gt; Results &gt; View Excel Report</strong>,
              save the <strong>XML</strong> as <strong>XLSX</strong> with the
              same name as the KDF file.
            </div>
          </div>
        </div>

        <div class="mt-3 flex gap-2">
          <button
            @click="showCustomizeModal = true"
            class="flex items-center justify-center gap-1 rounded border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
            title="Customize report columns"
          >
            <Settings class="w-4 h-4" />
          </button>
          <button
            @click="generate"
            class="flex-1 bg-green-600 text-white rounded py-1.5 text-sm hover:bg-green-700 flex items-center justify-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="!canGenerate"
            :title="generateTooltip"
          >
            <span v-if="genLoading.isLoading.value" class="pk-spinner" />
            <ArrowDownRight class="w-4 h-4" /> Generate Report
          </button>
        </div>
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

          <!-- Batch Report Mode Toggle -->
          <ReportModeToggle v-model="isBatchMultiCase" />

          <!-- Batch multi-case validation results -->
          <div v-if="isBatchMultiCase && batchTotalCount > 0" class="mb-3">
            <div class="flex items-center gap-2 mb-1">
              <span v-if="batchValidating" class="pk-spinner" />
              <CheckCircle2
                v-else-if="batchValidCount === batchTotalCount"
                class="w-4 h-4 text-green-600 shrink-0"
              />
              <AlertTriangle
                v-else
                class="w-4 h-4 shrink-0"
                :class="
                  batchValidCount === 0 ? 'text-red-600' : 'text-amber-600'
                "
              />
              <span
                class="text-xs font-medium"
                :class="
                  batchValidCount === batchTotalCount
                    ? 'text-green-700'
                    : batchValidCount === 0
                      ? 'text-red-700'
                      : 'text-amber-700'
                "
              >
                {{ batchValidCount }} of {{ batchTotalCount }} KDF files have
                valid KORF Excel
              </span>
            </div>
            <textarea
              v-if="batchProblems.length > 0"
              class="pk-input-mono resize-none rounded w-full mt-2 p-2 text-xs bg-gray-50 border border-gray-200"
              :value="batchProblems.join('\n')"
              rows="4"
              readonly
            />
            <div
              v-if="!batchValidating && batchValidCount === 0"
              class="mt-1 text-xs text-red-600"
            >
              No KDF files have valid KORF Excel reports. Generate them from
              KORF first.
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
            class="w-full bg-gray-500 text-white rounded py-1.5 text-sm hover:bg-gray-600 flex items-center justify-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="!canBatchGenerate"
            :title="batchTooltip"
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
        <div
          class="p-4 flex flex-col items-center justify-center text-gray-400 text-sm py-8"
        >
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
        <div
          class="p-4 flex flex-col items-center justify-center text-gray-400 text-sm py-8"
        >
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

  <!-- Project Info Modal (shown when report requires project info) -->
  <div v-if="showProjectInfoModal" class="pk-modal-backdrop">
    <div class="pk-modal" style="max-width: 520px">
      <div class="pk-modal-header">
        <h6 class="font-semibold flex items-center gap-1 text-amber-600">
          <AlertTriangle class="w-4 h-4" /> Project Info Required
        </h6>
        <button
          @click="showProjectInfoModal = false"
          class="text-gray-400 hover:text-gray-600"
        >
          <X class="w-4 h-4" />
        </button>
      </div>
      <div class="p-4 space-y-2 overflow-auto">
        <p class="text-xs text-gray-500 mb-2">
          Please fill in the required fields before generating the report.
        </p>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="pk-label-sm"
              >Company
              <span v-if="isRequired('company1')" class="text-red-500"
                >*</span
              ></label
            >
            <input
              v-model="editInfo.company1"
              type="text"
              class="pk-input"
              :placeholder="smartDefaults?.company1 || ''"
            />
          </div>
          <div>
            <label class="pk-label-sm"
              >Company 2
              <span v-if="isRequired('company2')" class="text-red-500"
                >*</span
              ></label
            >
            <input
              v-model="editInfo.company2"
              type="text"
              class="pk-input"
              :placeholder="smartDefaults?.company2 || ''"
            />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="pk-label-sm"
              >Project Name
              <span v-if="isRequired('project_name1')" class="text-red-500"
                >*</span
              ></label
            >
            <input
              v-model="editInfo.project_name1"
              type="text"
              class="pk-input"
              :placeholder="smartDefaults?.project_name1 || ''"
            />
          </div>
          <div>
            <label class="pk-label-sm">Project Name 2</label>
            <input
              v-model="editInfo.project_name2"
              type="text"
              class="pk-input"
              :placeholder="smartDefaults?.project_name2 || ''"
            />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="pk-label-sm">Document No</label>
            <input
              v-model="editInfo.item_name1"
              type="text"
              class="pk-input"
              :placeholder="smartDefaults?.item_name1 || ''"
            />
          </div>
          <div>
            <label class="pk-label-sm">Item / Tag</label>
            <input
              v-model="editInfo.item_name2"
              type="text"
              class="pk-input"
              :placeholder="smartDefaults?.item_name2 || ''"
            />
          </div>
        </div>
        <div class="grid grid-cols-3 gap-2">
          <div>
            <label class="pk-label-sm"
              >Prepared
              <span v-if="isRequired('prepared_by')" class="text-red-500"
                >*</span
              ></label
            >
            <input
              v-model="editInfo.prepared_by"
              type="text"
              class="pk-input"
              :placeholder="smartDefaults?.prepared_by || ''"
            />
          </div>
          <div>
            <label class="pk-label-sm">Checked</label>
            <input
              v-model="editInfo.checked_by"
              type="text"
              class="pk-input"
              :placeholder="smartDefaults?.checked_by || ''"
            />
          </div>
          <div>
            <label class="pk-label-sm">Approved</label>
            <input
              v-model="editInfo.approved_by"
              type="text"
              class="pk-input"
              :placeholder="smartDefaults?.approved_by || ''"
            />
          </div>
        </div>
        <div class="grid grid-cols-3 gap-2">
          <div>
            <label class="pk-label-sm">Date</label>
            <input
              v-model="editInfo.date"
              type="text"
              class="pk-input"
              :placeholder="smartDefaults?.date || ''"
            />
          </div>
          <div>
            <label class="pk-label-sm">Project No</label>
            <input
              v-model="editInfo.project_no"
              type="text"
              class="pk-input"
              :placeholder="smartDefaults?.project_no || ''"
            />
          </div>
          <div>
            <label class="pk-label-sm">Rev</label>
            <input
              v-model="editInfo.revision"
              type="text"
              class="pk-input"
              :placeholder="smartDefaults?.revision || ''"
            />
          </div>
        </div>
      </div>
      <div class="px-4 py-2 border-t flex justify-end gap-2">
        <button @click="showProjectInfoModal = false" class="pk-btn-secondary">
          Cancel
        </button>
        <button
          @click="saveProjectAndRetry()"
          class="pk-btn-primary"
          :disabled="saveProjectLoading"
        >
          <span v-if="saveProjectLoading" class="pk-spinner" />
          Save & Generate Report
        </button>
      </div>
    </div>
  </div>

  <ReportCustomizeModal
    v-model="pipeColumns"
    v-model:open="showCustomizeModal"
  />
</template>
