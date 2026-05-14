<template>
  <div>
    <!-- Toolbar -->
    <div class="d-flex align-center ga-3 mb-4 flex-wrap">
      <v-text-field
        v-model="searchQuery"
        placeholder="Semantic search memories…"
        prepend-inner-icon="mdi-magnify"
        clearable hide-details density="comfortable"
        style="max-width:320px;"
        @keydown.enter="doSearch"
      />
      <v-btn
        color="primary" variant="tonal" prepend-icon="mdi-database-search-outline"
        :loading="searching" @click="doSearch" size="small">
        Search
      </v-btn>
      <v-spacer />
      <v-btn color="secondary" variant="tonal" prepend-icon="mdi-plus" size="small" @click="showAdd = true">
        Add Memory
      </v-btn>
      <v-btn color="error" variant="text" prepend-icon="mdi-delete-sweep" size="small" @click="clearAll">
        Clear All
      </v-btn>
    </div>

    <!-- Results / list -->
    <div v-if="loading" class="text-center py-10">
      <v-progress-circular indeterminate color="primary" size="32" />
    </div>
    <div v-else-if="displayList.length === 0" class="text-center py-12 text-medium-emphasis">
      <v-icon size="48" class="mb-3 opacity-30">mdi-brain</v-icon>
      <div>{{ searchQuery ? 'No memories found for this query.' : 'No memories yet. Add some manually or start chatting.' }}</div>
    </div>

    <v-row v-else dense>
      <v-col v-for="mem in displayList" :key="mem.id" cols="12" sm="6">
        <v-card class="glass pa-4" rounded="xl">
          <div class="d-flex align-start ga-3">
            <div class="mem-icon d-flex align-center justify-center rounded-lg flex-shrink-0">
              <v-icon size="16" color="accent">mdi-lightbulb-outline</v-icon>
            </div>
            <div class="flex-1 text-body-2" style="line-height:1.6;">{{ mem.content }}</div>
          </div>
          <div class="d-flex align-center mt-3 ga-2">
            <v-chip size="x-small" class="chip-violet font-mono">
              importance {{ mem.importance.toFixed(1) }}
            </v-chip>
            <v-chip v-if="mem.source" size="x-small" variant="outlined" density="compact">{{ mem.source }}</v-chip>
            <v-spacer />
            <v-btn icon="mdi-delete-outline" size="x-small" variant="text" color="error" @click="deleteMemory(mem.id)" />
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Add memory dialog -->
    <v-dialog v-model="showAdd" max-width="480">
      <v-card class="glass pa-2" rounded="xl">
        <v-card-title class="font-display pa-5 pb-3">Add Memory</v-card-title>
        <v-card-text class="px-5 pb-4 d-flex flex-column ga-4">
          <v-textarea
            v-model="newMem.content"
            label="Memory content"
            rows="4"
            auto-grow
          />
          <div>
            <div class="d-flex justify-space-between mb-1">
              <span class="text-body-2">Importance</span>
              <span class="text-caption font-mono text-primary">{{ newMem.importance.toFixed(1) }}</span>
            </div>
            <v-slider v-model="newMem.importance" :min="0" :max="10" :step="0.5" color="accent" />
          </div>
          <v-text-field v-model="newMem.source" label="Source (optional)" density="compact" />
        </v-card-text>
        <v-card-actions class="px-5 pb-5 ga-2">
          <v-spacer />
          <v-btn variant="text" @click="showAdd = false">Cancel</v-btn>
          <v-btn color="primary" variant="tonal" :loading="adding" @click="addMemory">Add</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { memoryApi } from '@/api'
import { useAppStore } from '@/stores/app'

const props = defineProps({ characterId: { type: String, required: true } })
const app   = useAppStore()

const memories    = ref([])
const searchResults = ref(null)
const searchQuery = ref('')
const loading     = ref(false)
const searching   = ref(false)
const adding      = ref(false)
const showAdd     = ref(false)

const newMem = reactive({ content: '', importance: 5, source: '' })

const displayList = computed(() => searchResults.value ?? memories.value)

async function load() {
  loading.value = true
  try { const { data } = await memoryApi.list(props.characterId); memories.value = data }
  finally { loading.value = false }
}

async function doSearch() {
  if (!searchQuery.value?.trim()) { searchResults.value = null; return }
  searching.value = true
  try {
    const { data } = await memoryApi.search(props.characterId, { query: searchQuery.value, top_k: 10 })
    searchResults.value = data
  } finally { searching.value = false }
}

async function addMemory() {
  if (!newMem.content.trim()) return
  adding.value = true
  try {
    await memoryApi.create(props.characterId, {
      content: newMem.content,
      importance: newMem.importance,
      source: newMem.source || 'manual',
    })
    await load()
    showAdd.value = false
    Object.assign(newMem, { content: '', importance: 5, source: '' })
    app.notify('Memory added.')
  } catch (err) { app.notifyError(err) }
  finally { adding.value = false }
}

async function deleteMemory(id) {
  try { await memoryApi.delete(props.characterId, id); memories.value = memories.value.filter(m => m.id !== id) }
  catch (err) { app.notifyError(err) }
}

async function clearAll() {
  const ok = await app.showConfirm('Clear All Memories', 'This permanently deletes all memories for this character.')
  if (!ok) return
  try { await memoryApi.clear(props.characterId); memories.value = []; app.notify('Memories cleared.') }
  catch (err) { app.notifyError(err) }
}

onMounted(load)
</script>

<style scoped>
.mem-icon { width:32px;height:32px;background:rgba(139,92,246,0.12);flex-shrink:0; }
</style>