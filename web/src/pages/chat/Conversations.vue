<template>
  <div>
    <div class="d-flex align-center ga-3 mb-6 flex-wrap">
      <v-text-field
        v-model="search"
        placeholder="Search conversations…"
        prepend-inner-icon="mdi-magnify"
        clearable hide-details density="comfortable"
        style="max-width:300px;"
      />
      <v-spacer />
      <v-chip class="font-mono" size="small" variant="outlined">
        {{ filtered.length }} conversation{{ filtered.length !== 1 ? 's' : '' }}
      </v-chip>
    </div>

    <div v-if="loading" class="text-center py-16">
      <v-progress-circular indeterminate color="primary" size="40" />
    </div>

    <div v-else-if="filtered.length === 0" class="d-flex flex-column align-center py-20 text-center">
      <v-icon size="56" style="opacity:.2;color:#06B6D4;" class="mb-4">mdi-chat-outline</v-icon>
      <div class="font-display text-h6 mb-2" style="opacity:.5;">No conversations found</div>
      <div class="text-medium-emphasis text-body-2">Start chatting with a character to see your history here.</div>
    </div>

    <!-- Conversation cards grid -->
    <v-row v-else dense>
      <v-col
        v-for="conv in filtered"
        :key="conv.id"
        cols="12" sm="6" lg="4"
      >
        <v-card class="glass conv-card" rounded="xl" @click="openConv(conv)">
          <v-card-text class="pa-4">
            <div class="d-flex align-start ga-3">
              <div class="conv-icon d-flex align-center justify-center rounded-lg flex-shrink-0">
                <v-icon size="20" color="primary">mdi-chat-outline</v-icon>
              </div>
              <div class="flex-1 overflow-hidden">
                <div class="text-body-1 font-weight-semibold text-truncate">
                  {{ conv.title ?? 'Untitled Chat' }}
                </div>
                <div class="text-caption text-medium-emphasis mt-0.5">
                  {{ formatDate(conv.updated_at) }}
                </div>
              </div>
              <v-btn
                icon="mdi-delete-outline"
                size="x-small"
                variant="text"
                color="error"
                @click.stop="deleteConv(conv)"
              />
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { conversationsApi } from '@/api'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const app    = useAppStore()

const conversations = ref([])
const loading       = ref(false)
const search        = ref('')

const filtered = computed(() => {
  const q = search.value?.toLowerCase() ?? ''
  if (!q) return conversations.value
  return conversations.value.filter(c =>
    (c.title ?? '').toLowerCase().includes(q)
  )
})

async function load() {
  loading.value = true
  try { const { data } = await conversationsApi.list(); conversations.value = data }
  catch (err) { app.notifyError(err) }
  finally { loading.value = false }
}

async function openConv(conv) {
  router.push({ name: 'character-chat', params: { id: conv.character_id }, query: { conv: conv.id } })
}

async function deleteConv(conv) {
  const ok = await app.showConfirm('Delete Conversation', 'This cannot be undone.')
  if (!ok) return
  try {
    await conversationsApi.delete(conv.id)
    conversations.value = conversations.value.filter(c => c.id !== conv.id)
    app.notify('Conversation deleted.')
  } catch (err) { app.notifyError(err) }
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

onMounted(load)
</script>

<style scoped>
.conv-card {
  cursor: pointer;
  transition: transform 0.18s, box-shadow 0.18s;
  &:hover { transform: translateY(-2px); box-shadow: 0 6px 24px rgba(6,182,212,0.1) !important; }
}
.conv-icon { width:40px;height:40px;background:rgba(6,182,212,0.1); }
</style>