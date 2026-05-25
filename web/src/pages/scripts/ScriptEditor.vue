<template>
  <div v-if="script" class="d-flex gap-4" style="min-height: calc(100vh - 160px);">

    <!-- Left: Scene list -->
    <div style="width:240px; flex-shrink:0;">
      <div class="d-flex align-center mb-3">
        <span class="text-subtitle-2 font-weight-semibold">Scenes</span>
        <v-spacer />
        <v-btn size="x-small" icon variant="text" @click="addScene">
          <v-icon>mdi-plus</v-icon>
        </v-btn>
      </div>
      <v-list density="compact" nav class="px-0">
        <v-list-item
          v-for="scene in sortedScenes"
          :key="scene.id"
          :active="activeSceneId === scene.id"
          active-color="primary"
          @click="activeSceneId = scene.id"
          class="rounded-lg mb-1"
          style="cursor:pointer;"
        >
          <v-list-item-title class="text-body-2">{{ scene.title }}</v-list-item-title>
          <template #append>
            <v-btn size="x-small" icon variant="text" color="error" @click.stop="confirmDeleteScene(scene)">
              <v-icon size="14">mdi-close</v-icon>
            </v-btn>
          </template>
        </v-list-item>
      </v-list>
    </div>

    <!-- Right: Lines table -->
    <div class="flex-1 overflow-hidden">
      <div v-if="activeScene">
        <div class="d-flex align-center mb-3">
          <v-text-field
            v-model="activeScene.title"
            variant="outlined"
            density="compact"
            hide-details
            style="max-width:300px;"
            @blur="saveSceneTitle(activeScene)"
          />
          <v-spacer />
          <v-btn size="small" prepend-icon="mdi-plus" variant="tonal" @click="addLine">
            Add Line
          </v-btn>
          <v-btn size="small" prepend-icon="mdi-lightning-bolt" class="ml-2" variant="tonal" color="secondary" @click="synthesizeAll" :loading="synthesizing">
            Synthesize All
          </v-btn>
          <v-btn size="small" prepend-icon="mdi-download" class="ml-2" variant="tonal" @click="exportZip" :loading="exporting">
            Export ZIP
          </v-btn>
        </div>

        <v-table density="compact" class="rounded-lg" style="background:rgba(255,255,255,0.03);">
          <thead>
            <tr>
              <th style="width:48px;">#</th>
              <th style="width:160px;">Character</th>
              <th>Text</th>
              <th style="width:120px;">Audio</th>
              <th style="width:100px;">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(line, idx) in sortedLines" :key="line.id">
              <td class="text-caption text-medium-emphasis">{{ idx + 1 }}</td>
              <td>
                <v-select
                  :model-value="line.character_id"
                  :items="characterItems"
                  item-title="name"
                  item-value="id"
                  variant="plain"
                  density="compact"
                  hide-details
                  clearable
                  style="min-width:120px;"
                  @update:model-value="v => updateLine(line, { character_id: v })"
                />
              </td>
              <td>
                <v-textarea
                  :model-value="line.text"
                  variant="plain"
                  density="compact"
                  hide-details
                  rows="1"
                  auto-grow
                  @blur="e => updateLine(line, { text: e.target.value })"
                />
              </td>
              <td>
                <div v-if="line.audio_path" class="d-flex align-center gap-1">
                  <v-icon size="16" color="success">mdi-check-circle</v-icon>
                  <span class="text-caption">{{ msToSec(line.duration_ms) }}</span>
                </div>
                <span v-else class="text-caption text-medium-emphasis">—</span>
              </td>
              <td>
                <div class="d-flex gap-1">
                  <v-btn size="x-small" icon variant="text" :loading="synthLine === line.id" @click="synthesizeLine(line)">
                    <v-icon size="16">mdi-microphone</v-icon>
                  </v-btn>
                  <v-btn size="x-small" icon variant="text" color="error" @click="confirmDeleteLine(line)">
                    <v-icon size="16">mdi-delete-outline</v-icon>
                  </v-btn>
                </div>
              </td>
            </tr>
          </tbody>
        </v-table>
      </div>

      <v-empty-state
        v-else-if="sortedScenes.length === 0"
        icon="mdi-movie-edit-outline"
        title="No scenes yet"
        text="Add a scene to start writing."
      />

      <div v-else class="text-medium-emphasis pa-4">Select a scene to edit its lines.</div>
    </div>

    <!-- Delete scene confirm -->
    <v-dialog v-model="showDeleteScene" max-width="360">
      <v-card class="glass-bright">
        <v-card-title class="pt-5 px-6">Delete Scene?</v-card-title>
        <v-card-text class="px-6">This will delete all lines in "<strong>{{ deleteSceneTarget?.title }}</strong>".</v-card-text>
        <v-card-actions class="px-6 pb-5">
          <v-spacer />
          <v-btn variant="text" @click="showDeleteScene = false">Cancel</v-btn>
          <v-btn color="error" @click="deleteScene">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete line confirm -->
    <v-dialog v-model="showDeleteLine" max-width="360">
      <v-card class="glass-bright">
        <v-card-title class="pt-5 px-6">Delete Line?</v-card-title>
        <v-card-actions class="px-6 pb-5">
          <v-spacer />
          <v-btn variant="text" @click="showDeleteLine = false">Cancel</v-btn>
          <v-btn color="error" @click="deleteLine">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>

  <div v-else class="d-flex justify-center py-16">
    <v-progress-circular indeterminate color="primary" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { scriptsApi, charactersApi } from '@/api'

const route = useRoute()
const scriptId = route.params.id

const script = ref(null)
const characters = ref([])
const activeSceneId = ref(null)

const synthesizing = ref(false)
const exporting = ref(false)
const synthLine = ref(null)

const showDeleteScene = ref(false)
const showDeleteLine  = ref(false)
const deleteSceneTarget = ref(null)
const deleteLineTarget  = ref(null)

const sortedScenes = computed(() =>
  [...(script.value?.scenes ?? [])].sort((a, b) => a.order - b.order)
)

const activeScene = computed(() =>
  script.value?.scenes?.find(s => s.id === activeSceneId.value) ?? null
)

const sortedLines = computed(() =>
  [...(activeScene.value?.lines ?? [])].sort((a, b) => a.order - b.order)
)

const characterItems = computed(() =>
  characters.value.map(c => ({ id: c.id, name: c.name }))
)

function msToSec(ms) {
  if (!ms) return ''
  return (ms / 1000).toFixed(1) + 's'
}

async function load() {
  const [scriptRes, charRes] = await Promise.all([
    scriptsApi.get(scriptId),
    charactersApi.list(),
  ])
  script.value = scriptRes.data
  characters.value = charRes.data
  if (sortedScenes.value.length) {
    activeSceneId.value = sortedScenes.value[0].id
  }
}

async function addScene() {
  const order = sortedScenes.value.length
  const { data } = await scriptsApi.createScene(scriptId, { title: `Scene ${order + 1}`, order })
  script.value.scenes.push({ ...data, lines: [] })
  activeSceneId.value = data.id
}

async function saveSceneTitle(scene) {
  await scriptsApi.updateScene(scriptId, scene.id, { title: scene.title })
}

function confirmDeleteScene(scene) {
  deleteSceneTarget.value = scene
  showDeleteScene.value = true
}

async function deleteScene() {
  await scriptsApi.deleteScene(scriptId, deleteSceneTarget.value.id)
  script.value.scenes = script.value.scenes.filter(s => s.id !== deleteSceneTarget.value.id)
  if (activeSceneId.value === deleteSceneTarget.value.id) {
    activeSceneId.value = sortedScenes.value[0]?.id ?? null
  }
  showDeleteScene.value = false
}

async function addLine() {
  if (!activeScene.value) return
  const order = sortedLines.value.length
  const { data } = await scriptsApi.createLine(scriptId, activeScene.value.id, { text: '', order })
  activeScene.value.lines.push(data)
}

async function updateLine(line, patch) {
  const { data } = await scriptsApi.updateLine(scriptId, activeScene.value.id, line.id, patch)
  Object.assign(line, data)
}

function confirmDeleteLine(line) {
  deleteLineTarget.value = line
  showDeleteLine.value = true
}

async function deleteLine() {
  await scriptsApi.deleteLine(scriptId, activeScene.value.id, deleteLineTarget.value.id)
  activeScene.value.lines = activeScene.value.lines.filter(l => l.id !== deleteLineTarget.value.id)
  showDeleteLine.value = false
}

async function synthesizeLine(line) {
  synthLine.value = line.id
  try {
    const { data } = await scriptsApi.synthesizeLine(scriptId, activeScene.value.id, line.id)
    Object.assign(line, data)
  } finally {
    synthLine.value = null
  }
}

async function synthesizeAll() {
  synthesizing.value = true
  try {
    await scriptsApi.synthesizeAll(scriptId)
    await load()
  } finally {
    synthesizing.value = false
  }
}

async function exportZip() {
  exporting.value = true
  try {
    const { data } = await scriptsApi.exportZip(scriptId)
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = `script_${scriptId}.zip`
    a.click()
    URL.revokeObjectURL(url)
  } finally {
    exporting.value = false
  }
}

onMounted(load)
</script>
