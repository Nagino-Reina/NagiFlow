<template>
  <div>
    <div class="d-flex align-center ga-3 mb-4 flex-wrap">
      <span class="text-body-2 text-medium-emphasis">
        {{ docs.length }} document{{ docs.length !== 1 ? 's' : '' }} linked to this character
      </span>
      <v-spacer />
      <v-btn color="primary" variant="tonal" prepend-icon="mdi-link-plus" size="small"
        @click="$router.push({ name: 'knowledge' })">
        Manage in Knowledge Base
      </v-btn>
    </div>

    <div v-if="loading" class="text-center py-8">
      <v-progress-circular indeterminate color="primary" size="28" />
    </div>
    <div v-else-if="docs.length === 0" class="text-center py-10 text-medium-emphasis">
      <v-icon size="48" class="mb-3 opacity-30">mdi-book-open-outline</v-icon>
      <div class="text-body-2">No documents linked yet.</div>
      <div class="text-caption mt-1">Upload documents in the Knowledge Base and link them to this character.</div>
    </div>
    <v-row v-else dense>
      <v-col v-for="doc in docs" :key="doc.id" cols="12" sm="6">
        <v-card class="glass pa-4" rounded="xl">
          <div class="d-flex align-center ga-3">
            <div class="doc-icon d-flex align-center justify-center rounded-lg flex-shrink-0">
              <v-icon size="18" color="tertiary">mdi-file-document-outline</v-icon>
            </div>
            <div class="flex-1 overflow-hidden">
              <div class="text-body-2 font-weight-medium text-truncate">{{ doc.title }}</div>
              <div class="d-flex align-center ga-1 mt-1">
                <v-chip size="x-small" class="chip-emerald font-mono">{{ doc.chunk_count }} chunks</v-chip>
                <v-chip v-if="doc.source" size="x-small" variant="outlined" density="compact" class="text-truncate" style="max-width:120px;">
                  {{ doc.source }}
                </v-chip>
              </div>
            </div>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { knowledgeApi } from '@/api'
import { useAppStore } from '@/stores/app'

const props = defineProps({ characterId: { type: String, required: true } })
const app   = useAppStore()

const docs    = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const { data } = await knowledgeApi.list({ character_id: props.characterId })
    docs.value = data
  } catch (err) { app.notifyError(err) }
  finally { loading.value = false }
}

onMounted(load)
</script>

<style scoped>
.doc-icon { width:38px;height:38px;background:rgba(16,185,129,0.10);flex-shrink:0; }
</style>