<template>
  <div>
    <!-- Header -->
    <div class="d-flex align-center mb-6">
      <div>
        <div class="text-h5 font-weight-bold">Training Data</div>
        <div class="text-caption text-medium-emphasis">Manage TTS voice training datasets</div>
      </div>
      <v-spacer />
      <v-btn color="primary" prepend-icon="mdi-plus" @click="showCreate = true">
        New Dataset
      </v-btn>
    </div>

    <!-- Dataset list / detail split -->
    <div class="d-flex gap-4">

      <!-- Dataset list -->
      <div style="width:280px; flex-shrink:0;">
        <v-list density="compact" nav class="px-0">
          <v-list-item
            v-for="ds in datasets"
            :key="ds.id"
            :active="activeId === ds.id"
            active-color="primary"
            @click="selectDataset(ds.id)"
            class="rounded-lg mb-1"
            style="cursor:pointer;"
          >
            <v-list-item-title class="text-body-2 font-weight-medium">{{ ds.name }}</v-list-item-title>
            <v-list-item-subtitle class="text-caption">
              {{ ds.item_count }} items · {{ durationLabel(ds.total_duration_ms) }}
            </v-list-item-subtitle>
            <template #append>
              <v-btn size="x-small" icon variant="text" color="error" @click.stop="confirmDelete(ds)">
                <v-icon size="14">mdi-close</v-icon>
              </v-btn>
            </template>
          </v-list-item>
        </v-list>

        <v-empty-state
          v-if="!datasets.length && !loading"
          icon="mdi-database-outline"
          title="No datasets"
          text="Create your first training dataset."
          style="font-size:12px;"
        />
      </div>

      <!-- Dataset detail -->
      <div class="flex-1" v-if="activeDataset">
        <div class="d-flex align-center mb-3">
          <span class="text-subtitle-1 font-weight-semibold">{{ activeDataset.name }}</span>
          <v-spacer />
          <v-btn size="small" prepend-icon="mdi-microphone-plus" variant="tonal" @click="showGenerate = true" class="mr-2">
            Generate
          </v-btn>
          <v-btn size="small" prepend-icon="mdi-upload" variant="tonal" @click="showUpload = true" class="mr-2">
            Import WAV
          </v-btn>
          <v-btn size="small" prepend-icon="mdi-download" variant="tonal" :loading="exporting" @click="exportDataset">
            Export ZIP
          </v-btn>
        </div>

        <v-table density="compact" class="rounded-lg" style="background:rgba(255,255,255,0.03);">
          <thead>
            <tr>
              <th>Text</th>
              <th style="width:80px;">Source</th>
              <th style="width:80px;">Duration</th>
              <th style="width:120px;">Rating</th>
              <th style="width:60px;"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in activeDataset.items" :key="item.id">
              <td class="py-2" style="max-width:320px;">
                <span class="text-body-2">{{ item.text }}</span>
              </td>
              <td>
                <v-chip size="x-small" :color="sourceColor(item.source)">{{ item.source }}</v-chip>
              </td>
              <td class="text-caption text-medium-emphasis">
                {{ item.duration_ms ? (item.duration_ms / 1000).toFixed(1) + 's' : '—' }}
              </td>
              <td>
                <v-rating
                  :model-value="item.quality_rating ?? 0"
                  density="compact"
                  size="14"
                  color="amber"
                  half-increments
                  @update:model-value="v => rateItem(item, v)"
                />
              </td>
              <td>
                <v-btn size="x-small" icon variant="text" color="error" @click="confirmDeleteItem(item)">
                  <v-icon size="14">mdi-delete-outline</v-icon>
                </v-btn>
              </td>
            </tr>
          </tbody>
        </v-table>

        <v-empty-state
          v-if="!activeDataset.items?.length"
          icon="mdi-microphone-outline"
          title="No items"
          text="Generate or import audio items to get started."
        />
      </div>
    </div>

    <!-- Create dataset dialog -->
    <v-dialog v-model="showCreate" max-width="460">
      <v-card class="glass-bright">
        <v-card-title class="pt-5 px-6">New Dataset</v-card-title>
        <v-card-text class="px-6">
          <v-text-field v-model="createForm.name" label="Name" variant="outlined" density="compact" autofocus />
          <v-textarea v-model="createForm.description" label="Description" variant="outlined" density="compact" rows="2" />
        </v-card-text>
        <v-card-actions class="px-6 pb-5">
          <v-spacer />
          <v-btn variant="text" @click="showCreate = false">Cancel</v-btn>
          <v-btn color="primary" :loading="saving" @click="createDataset">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Generate item dialog -->
    <v-dialog v-model="showGenerate" max-width="460">
      <v-card class="glass-bright">
        <v-card-title class="pt-5 px-6">Generate TTS Item</v-card-title>
        <v-card-text class="px-6">
          <v-textarea v-model="genForm.text" label="Text" variant="outlined" density="compact" rows="3" autofocus />
          <v-text-field v-model.number="genForm.speaker_id" label="Speaker ID (optional)" variant="outlined" density="compact" type="number" />
        </v-card-text>
        <v-card-actions class="px-6 pb-5">
          <v-spacer />
          <v-btn variant="text" @click="showGenerate = false">Cancel</v-btn>
          <v-btn color="primary" :loading="generating" @click="generateItem">Generate</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Upload WAV dialog -->
    <v-dialog v-model="showUpload" max-width="460">
      <v-card class="glass-bright">
        <v-card-title class="pt-5 px-6">Import WAV</v-card-title>
        <v-card-text class="px-6">
          <v-textarea v-model="uploadForm.text" label="Transcript" variant="outlined" density="compact" rows="3" autofocus />
          <v-file-input v-model="uploadForm.file" label="WAV file" accept="audio/wav" variant="outlined" density="compact" prepend-icon="" />
        </v-card-text>
        <v-card-actions class="px-6 pb-5">
          <v-spacer />
          <v-btn variant="text" @click="showUpload = false">Cancel</v-btn>
          <v-btn color="primary" :loading="uploading" @click="importItem">Import</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete dataset -->
    <v-dialog v-model="showDelete" max-width="380">
      <v-card class="glass-bright">
        <v-card-title class="pt-5 px-6">Delete Dataset?</v-card-title>
        <v-card-text class="px-6">Permanently delete "<strong>{{ deleteTarget?.name }}</strong>" and all its items?</v-card-text>
        <v-card-actions class="px-6 pb-5">
          <v-spacer />
          <v-btn variant="text" @click="showDelete = false">Cancel</v-btn>
          <v-btn color="error" :loading="deleting" @click="deleteDataset">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete item -->
    <v-dialog v-model="showDeleteItem" max-width="360">
      <v-card class="glass-bright">
        <v-card-title class="pt-5 px-6">Delete Item?</v-card-title>
        <v-card-actions class="px-6 pb-5">
          <v-spacer />
          <v-btn variant="text" @click="showDeleteItem = false">Cancel</v-btn>
          <v-btn color="error" @click="deleteItem">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { trainingApi } from '@/api'

const datasets = ref([])
const loading  = ref(false)
const saving   = ref(false)
const deleting = ref(false)
const generating = ref(false)
const uploading  = ref(false)
const exporting  = ref(false)

const activeId = ref(null)
const activeDataset = ref(null)

const showCreate   = ref(false)
const showGenerate = ref(false)
const showUpload   = ref(false)
const showDelete   = ref(false)
const showDeleteItem = ref(false)

const deleteTarget = ref(null)
const deleteItemTarget = ref(null)

const createForm = ref({ name: '', description: '' })
const genForm    = ref({ text: '', speaker_id: null })
const uploadForm = ref({ text: '', file: null })

function durationLabel(ms) {
  if (!ms) return '0s'
  const s = Math.round(ms / 1000)
  return s >= 60 ? `${Math.floor(s/60)}m ${s%60}s` : `${s}s`
}

function sourceColor(src) {
  return { generated: 'primary', imported: 'secondary', recorded: 'success' }[src] ?? 'default'
}

async function load() {
  loading.value = true
  try {
    const { data } = await trainingApi.listDatasets()
    datasets.value = data
  } finally {
    loading.value = false
  }
}

async function selectDataset(id) {
  activeId.value = id
  const { data } = await trainingApi.getDataset(id)
  activeDataset.value = data
}

async function createDataset() {
  if (!createForm.value.name.trim()) return
  saving.value = true
  try {
    const { data } = await trainingApi.createDataset(createForm.value)
    datasets.value.unshift(data)
    showCreate.value = false
    createForm.value = { name: '', description: '' }
    await selectDataset(data.id)
  } finally {
    saving.value = false
  }
}

function confirmDelete(ds) {
  deleteTarget.value = ds
  showDelete.value = true
}

async function deleteDataset() {
  deleting.value = true
  try {
    await trainingApi.deleteDataset(deleteTarget.value.id)
    datasets.value = datasets.value.filter(d => d.id !== deleteTarget.value.id)
    if (activeId.value === deleteTarget.value.id) {
      activeId.value = null
      activeDataset.value = null
    }
    showDelete.value = false
  } finally {
    deleting.value = false
  }
}

async function generateItem() {
  if (!genForm.value.text.trim()) return
  generating.value = true
  try {
    const form = new FormData()
    form.append('text', genForm.value.text)
    if (genForm.value.speaker_id !== null) form.append('speaker_id', genForm.value.speaker_id)
    const { data } = await trainingApi.generateItem(activeId.value, form)
    activeDataset.value.items.push(data)
    const ds = datasets.value.find(d => d.id === activeId.value)
    if (ds) ds.item_count++
    showGenerate.value = false
    genForm.value = { text: '', speaker_id: null }
  } finally {
    generating.value = false
  }
}

async function importItem() {
  if (!uploadForm.value.text.trim() || !uploadForm.value.file) return
  uploading.value = true
  try {
    const form = new FormData()
    form.append('text', uploadForm.value.text)
    form.append('source', 'imported')
    form.append('audio', uploadForm.value.file)
    const { data } = await trainingApi.addItem(activeId.value, form)
    activeDataset.value.items.push(data)
    const ds = datasets.value.find(d => d.id === activeId.value)
    if (ds) ds.item_count++
    showUpload.value = false
    uploadForm.value = { text: '', file: null }
  } finally {
    uploading.value = false
  }
}

async function rateItem(item, rating) {
  const { data } = await trainingApi.updateItem(activeId.value, item.id, { quality_rating: rating })
  Object.assign(item, data)
}

function confirmDeleteItem(item) {
  deleteItemTarget.value = item
  showDeleteItem.value = true
}

async function deleteItem() {
  await trainingApi.deleteItem(activeId.value, deleteItemTarget.value.id)
  activeDataset.value.items = activeDataset.value.items.filter(i => i.id !== deleteItemTarget.value.id)
  const ds = datasets.value.find(d => d.id === activeId.value)
  if (ds) ds.item_count = Math.max(0, ds.item_count - 1)
  showDeleteItem.value = false
}

async function exportDataset() {
  exporting.value = true
  try {
    const { data } = await trainingApi.exportDataset(activeId.value)
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = `training_${activeId.value}.zip`
    a.click()
    URL.revokeObjectURL(url)
  } finally {
    exporting.value = false
  }
}

onMounted(load)
</script>
