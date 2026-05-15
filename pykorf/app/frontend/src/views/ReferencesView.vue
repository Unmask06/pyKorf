<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import { useSessionStore } from "../stores/session";
import { useToastStore } from "../composables/useToast";
import { useLoading } from "../composables/useLoading";
import {
  getReferences,
  saveReferences,
  addReference,
  deleteReference,
  predictCategory,
  getErrorMessage,
} from "../api/client";
import {
  Plus,
  Trash2,
  ExternalLink,
  Save,
  Search,
  PenSquare,
  Inbox,
  BookText,
  MessageSquare,
  AlertTriangle,
  List,
  FolderOpen,
  Lightbulb,
} from "lucide-vue-next";
import PathBrowser from "../components/PathBrowser.vue";
import ReferenceSearchView from "../components/ReferenceSearchView.vue";
import type {
  AddReferenceRequest,
  DeleteReferenceRequest,
  ReferenceSchema,
  SaveAllReferencesRequest,
} from "../api/generated/types.gen";

const router = useRouter();
const session = useSessionStore();
const toast = useToastStore();

const basis = ref("");
const remarks = ref("");
const hold = ref("");
const references = ref<ReferenceSchema[]>([]);
const dirty = ref(false);

// New reference form
const newRefName = ref("");
const newRefLink = ref("");
const newRefDesc = ref("");
const newRefCategory = ref("");
const editingId = ref("");
const refFilter = ref("");

const showLinkBrowser = ref(false);

const categories = [
  "P&ID",
  "PFD",
  "Datasheet",
  "Specification",
  "Calculation",
  "Drawing",
  "Report",
  "Standard",
  "Other",
];

const categoryTouchedByUser = ref(false);

function onCategoryUserChange() {
  categoryTouchedByUser.value = true;
}

watch(newRefDesc, async (val, oldVal) => {
  if (!val || oldVal || categoryTouchedByUser.value || newRefCategory.value) return;
  try {
    const resp = await predictCategory({ body: { description: val } });
    if (resp.data?.category) {
      newRefCategory.value = resp.data.category;
    }
  } catch {
    // silent — prediction is best-effort
  }
});

function categoryBadgeCls(cat: string): string {
  const map: Record<string, string> = {
    "P&ID": "bg-cyan-100 text-cyan-800",
    PFD: "bg-blue-600 text-white",
    Datasheet: "bg-green-600 text-white",
    Specification: "bg-yellow-100 text-yellow-800",
    Calculation: "bg-red-500 text-white",
    Drawing: "bg-gray-600 text-white",
    Report: "bg-gray-800 text-white border",
    Standard: "bg-gray-100 text-gray-700 border",
  };
  return map[cat] || "bg-gray-500 text-white";
}

// Doc register search — only open when SharePoint/doc-register is configured
const showDocSearch = ref(false);
function openDocSearch() {
  if (!session.skipSpOverride) showDocSearch.value = true;
}

async function fetchReferences() {
  try {
    const response = await getReferences();
    const data = response.data!;
    basis.value = data.basis ?? "";
    remarks.value = data.remarks ?? "";
    hold.value = data.hold ?? "";
    references.value = data.references ?? [];
    dirty.value = false;
  } catch (err: unknown) {
    toast.error(getErrorMessage(err, "Failed to load references."));
  }
}

const saveAllLoading = useLoading(async () => {
  try {
    const req: SaveAllReferencesRequest = {
      basis: basis.value,
      remarks: remarks.value,
      hold: hold.value,
    };
    await saveReferences({ body: req });
    dirty.value = false;
    toast.success("Basis, remarks, and hold saved.");
  } catch (err: unknown) {
    toast.error(getErrorMessage(err, "Failed to save."));
  }
});

const addRefLoading = useLoading(async () => {
  if (!newRefName.value || !newRefLink.value) {
    toast.error("Name and link are required.");
    return;
  }
  try {
    const req: AddReferenceRequest = {
      edit_id: editingId.value,
      name: newRefName.value,
      link: newRefLink.value,
      description: newRefDesc.value,
      category: newRefCategory.value,
    };
    await addReference({ body: req });
    newRefName.value = "";
    newRefLink.value = "";
    newRefDesc.value = "";
    newRefCategory.value = "";
    editingId.value = "";
    categoryTouchedByUser.value = false;
    await fetchReferences();
    toast.success("Reference saved.");
  } catch (err: unknown) {
    toast.error(getErrorMessage(err, "Failed to save reference."));
  }
});

async function deleteReferenceHandler(refId: string) {
  try {
    const req: DeleteReferenceRequest = { ref_id: refId };
    await deleteReference({ body: req });
    await fetchReferences();
    toast.info("Reference deleted.");
  } catch (err: unknown) {
    toast.error(getErrorMessage(err, "Failed to delete reference."));
  }
}

function editReference(ref: ReferenceSchema) {
  editingId.value = ref.id;
  newRefName.value = ref.name;
  newRefLink.value = ref.link;
  newRefDesc.value = ref.description ?? "";
  newRefCategory.value = ref.category ?? "";
  categoryTouchedByUser.value = false;
}

function cancelEdit() {
  editingId.value = "";
  newRefName.value = "";
  newRefLink.value = "";
  newRefDesc.value = "";
  newRefCategory.value = "";
  categoryTouchedByUser.value = false;
}

function handleDocSearchSelect(name: string, link: string, description: string) {
  newRefName.value = name;
  newRefLink.value = link;
  newRefDesc.value = description;
  showDocSearch.value = false;
}

function markDirty() {
  dirty.value = true;
}

const filteredReferences = computed(() => {
  if (!refFilter.value) return references.value;
  const q = refFilter.value.toLowerCase();
  return references.value.filter(
    (r) =>
      r.name.toLowerCase().includes(q) ||
      (r.category ?? "").toLowerCase().includes(q) ||
      (r.description ?? "").toLowerCase().includes(q) ||
      r.link.toLowerCase().includes(q),
  );
});

onMounted(() => {
  if (!session.isLoaded) router.push("/");
  fetchReferences();
});

</script>

<template>
  <div class="flex gap-4 flex-wrap lg:flex-nowrap">
    <!-- ── Left: Design Basis / Remarks / Hold ─────────────── -->
    <div class="w-full lg:w-1/4 space-y-3">
      <form @submit.prevent="saveAllLoading.execute()" class="space-y-3">
        <!-- Design Basis -->
        <div class="pk-card">
          <div class="pk-card-header flex items-center gap-1">
            <BookText class="w-4 h-4 text-blue-600" /> Design Basis
          </div>
          <div class="p-3">
            <textarea
              v-model="basis"
              @input="markDirty"
              rows="12"
              class="pk-textarea font-mono"
              placeholder="Enter design basis, project notes, assumptions, or any free-text context for this model…"
              style="font-size: 0.85rem"
            />
          </div>
        </div>

        <!-- Remarks -->
        <div class="pk-card">
          <div class="pk-card-header flex items-center gap-1">
            <MessageSquare class="w-4 h-4 text-gray-500" /> Remarks
          </div>
          <div class="p-3">
            <textarea
              v-model="remarks"
              @input="markDirty"
              rows="6"
              class="pk-textarea font-mono"
              placeholder="General remarks, comments, or observations…"
              style="font-size: 0.85rem"
            />
          </div>
        </div>

        <!-- Hold Items -->
        <div class="pk-card">
          <div class="pk-card-header flex items-center gap-1">
            <AlertTriangle class="w-4 h-4 text-yellow-500" /> Hold Items
          </div>
          <div class="p-3">
            <textarea
              v-model="hold"
              @input="markDirty"
              rows="6"
              class="pk-textarea font-mono"
              placeholder="Open actions, holds, or items pending resolution…"
              style="font-size: 0.85rem"
            />
          </div>
        </div>

        <button
          type="submit"
          class="pk-btn-primary w-full"
          :disabled="saveAllLoading.isLoading.value"
        >
          <Save class="w-4 h-4" /> Save All
        </button>
      </form>

      <!-- How to Use -->
      <div class="pk-card">
        <div class="pk-card-header flex items-center gap-1">
          <Lightbulb class="w-4 h-4" /> How to Use
        </div>
        <div class="p-4 text-sm text-gray-500">
          <ol class="pl-4 space-y-1 mb-0">
            <li>
              Write design basis, remarks, and hold items in the text areas and
              click <strong>Save All</strong>.
            </li>
            <li>
              Click the <Search class="w-3 h-3 inline" /> button next to the
              Name field, select a document in Step 1, then pick its file in
              Step 2.
            </li>
            <li>
              Select a <strong>Category</strong> and click
              <strong>Add Reference</strong>.
            </li>
            <li>
              Shortcuts are <strong>auto-created</strong> in the
              <code class="bg-gray-100 rounded px-1">reference/</code> folder
              when you add, edit, or delete references.
            </li>
            <li>
              Use the browse button on the Link field to auto-detect SharePoint
              URLs for synced folders.
            </li>
          </ol>
        </div>
      </div>
    </div>

    <!-- ── Right: References table + Add form ──────────────── -->
    <div class="w-full lg:w-3/4 space-y-3">
      <!-- Add reference form -->
      <div class="pk-card">
        <div class="pk-card-header flex items-center gap-2">
          <Plus class="w-4 h-4 text-green-500" />
          {{ editingId ? "Edit Reference" : "Add Reference" }}
        </div>
        <div class="p-3">
          <form @submit.prevent="addRefLoading.execute()">
            <input type="hidden" v-model="editingId" />
            <div class="grid grid-cols-12 gap-2 mb-2">
              <div class="col-span-5">
                <label class="text-xs font-semibold mb-1 block"
                  >Name <span class="text-red-500">*</span></label
                >
                <div class="flex">
                  <input
                    v-model="newRefName"
                    type="text"
                    class="pk-input text-sm"
                    :class="!session.skipSpOverride ? 'rounded-none' : 'rounded'"
                    placeholder="e.g. P&ID-001"
                    required
                    autocomplete="off"
                  />
                  <button
                    v-if="!session.skipSpOverride"
                    type="button"
                    @click="openDocSearch()"
                    class="flex items-center justify-center px-2 py-1 text-xs border border-l-0 border-cyan-300 rounded-r-md bg-cyan-50 text-cyan-600 hover:bg-cyan-100"
                    title="Search Document Register"
                  >
                    <Search class="w-3.5 h-3.5" />
                  </button>
                </div>
                <div v-if="!session.skipSpOverride" class="pk-hint">
                  Click <Search class="w-3 h-3 inline" /> to search the Document
                  Register, then choose a file to auto-fill fields.
                </div>
                <div v-else class="pk-hint text-yellow-600">
                  <AlertTriangle class="w-3 h-3 inline" /> Document Register
                  search is disabled. Configure SharePoint overrides in
                  <a href="/preferences" class="underline">Preferences</a> to enable.
                </div>
              </div>
              <div class="col-span-3">
                <label class="text-xs font-semibold mb-1 block"
                  >Category <span class="text-red-500">*</span></label
                >
                <select
                  v-model="newRefCategory"
                  @change="onCategoryUserChange"
                  class="pk-select w-full"
                  required
                >
                  <option value="" disabled>Select…</option>
                  <option v-for="cat in categories" :key="cat" :value="cat">
                    {{ cat }}
                  </option>
                </select>
              </div>
              <div class="col-span-4">
                <label class="text-xs font-semibold mb-1 block"
                  >Link / URL <span class="text-red-500">*</span></label
                >
                <div class="flex">
                  <input
                    v-model="newRefLink"
                    type="text"
                    class="pk-input-mono text-sm rounded-none"
                    placeholder="https://… or C:\path\to\file"
                    required
                    autocomplete="off"
                  />
                  <button
                    type="button"
                    @click="showLinkBrowser = true"
                    class="flex items-center justify-center px-2 py-1 text-xs border border-l-0 border-gray-300 rounded-r-md bg-gray-100 hover:bg-gray-50"
                    title="Browse — SharePoint URL auto-detected for synced folders"
                  >
                    <FolderOpen class="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
            <div class="mb-2">
              <label class="text-xs font-semibold mb-1 block"
                >Description</label
              >
              <input
                v-model="newRefDesc"
                type="text"
                class="pk-input text-sm"
                placeholder="Brief note about this reference (optional)"
                autocomplete="off"
              />
            </div>
            <div class="flex gap-2">
              <button
                type="submit"
                class="bg-green-600 text-white rounded px-3 py-1 text-sm hover:bg-green-700 flex items-center gap-1"
                :disabled="addRefLoading.isLoading.value"
              >
                <Plus class="w-3.5 h-3.5" />
                {{ editingId ? "Update" : "Add Reference" }}
              </button>
              <button
                v-if="editingId"
                @click="cancelEdit"
                type="button"
                class="pk-btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- References table -->
      <div class="pk-card">
        <div class="pk-card-header flex items-center gap-2">
          <List class="w-4 h-4 text-blue-600" /> References
          <span class="pk-badge-blue ml-1">{{ references.length }}</span>
          <input
            v-model="refFilter"
            type="text"
            class="pk-input ml-auto"
            placeholder="Filter…"
            style="max-width: 180px"
          />
        </div>

        <template v-if="references.length">
          <div class="overflow-x-auto">
            <table class="pk-table">
              <thead class="bg-gray-800 text-white">
                <tr>
                  <th
                    class="px-3 py-2 text-left text-sm font-semibold"
                    style="width: 25%"
                  >
                    Name
                  </th>
                  <th
                    class="px-3 py-2 text-left text-sm font-semibold"
                    style="width: 10%"
                  >
                    Category
                  </th>
                  <th
                    class="px-3 py-2 text-left text-sm font-semibold"
                    style="width: 20%"
                  >
                    Link
                  </th>
                  <th
                    class="px-3 py-2 text-left text-sm font-semibold"
                    style="width: 25%"
                  >
                    Description
                  </th>
                  <th
                    class="px-3 py-2 text-left text-sm font-semibold"
                    style="width: 6rem"
                  ></th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="ref in filteredReferences"
                  :key="ref.id"
                  class="hover:bg-gray-50"
                >
                  <td class="font-semibold text-sm">{{ ref.name }}</td>
                  <td>
                    <span
                      class="text-xs px-1.5 py-0.5 rounded"
                      :class="categoryBadgeCls(ref.category ?? '')"
                    >
                      {{ ref.category ?? '' }}
                    </span>
                  </td>
                    <td>
                    <a
                      v-if="ref.link"
                      :href="ref.link"
                      target="_blank"
                      rel="noopener"
                      class="text-blue-600 text-xs hover:underline inline-flex items-center gap-1 ref-link"
                      :title="ref.link"
                    >
                      <ExternalLink class="w-3 h-3" /> {{ ref.link }}
                    </a>
                  </td>
                  <td class="text-xs text-gray-500">{{ ref.description ?? "" }}</td>
                  <td class="text-right">
                    <button
                      @click="editReference(ref)"
                      class="border border-gray-300 rounded px-1 py-0 mr-1 text-gray-500 hover:text-blue-600 hover:border-blue-300"
                      title="Edit"
                    >
                      <PenSquare class="w-3 h-3" />
                    </button>
                    <button
                      @click="deleteReferenceHandler(ref.id)"
                      class="border border-red-200 rounded px-1 py-0 text-red-400 hover:text-red-600 hover:border-red-400"
                      title="Delete"
                      :confirm="'Delete this reference?'"
                    >
                      <Trash2 class="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
        <template v-else>
          <div class="text-center text-gray-400 py-5">
            <Inbox class="w-8 h-8 mx-auto mb-2" />
            No references yet. Use the form above to add your first reference.
          </div>
        </template>
      </div>
    </div>
  </div>

  <!-- Path browser for Link field -->
  <PathBrowser
    v-if="showLinkBrowser"
    filter="any"
    :initialPath="newRefLink"
    @close="showLinkBrowser = false"
    @select="
      (p: string) => {
        newRefLink = p;
        showLinkBrowser = false;
      }
    "
  />

  <!-- Doc Register Search Modal -->
  <ReferenceSearchView
    v-if="showDocSearch"
    :initial-query="newRefName"
    @close="showDocSearch = false"
    @select="handleDocSearchSelect"
  />
</template>

<style scoped>
/* Ref link ellipsis */
.ref-link {
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
/* Increased table row padding and height */
.pk-table td,
.pk-table th {
  padding: 0.75rem 1rem;
}
.pk-table tbody tr {
  height: 3.5rem;
}
</style>
