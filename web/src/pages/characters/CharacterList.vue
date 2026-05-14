<template>
  <div>
    <!-- Toolbar -->
    <div class="d-flex align-center ga-3 mb-6 flex-wrap">
      <v-text-field
        v-model="search"
        placeholder="Search characters…"
        prepend-inner-icon="mdi-magnify"
        clearable
        hide-details
        density="comfortable"
        style="max-width:320px;"
      />
      <v-select
        v-model="filterType"
        :items="typeOptions"
        placeholder="Model type"
        clearable
        hide-details
        density="comfortable"
        style="max-width:180px;"
      />
      <v-spacer />
      <v-btn-toggle v-model="viewMode" density="compact" color="primary" rounded="lg" variant="outlined" mandatory>
        <v-btn icon="mdi-view-grid" value="grid" />
        <v-btn icon="mdi-view-list" value="list" />
      </v-btn-toggle>
      <v-btn color="primary" prepend-icon="mdi-plus" :to="{ name: 'character-create' }" class="glow-cyan">
        New Character
      </v-btn>
    </div>

    <!-- Loading skeletons -->
    <v-row v-if="charStore.loading" dense>
      <v-col v-for="n in 6" :key="n" cols="12" sm="6" md="4">
        <v-skeleton-loader type="card" color="transparent" class="glass rounded-xl" />
      </v-col>
    </v-row>

    <!-- Empty state -->
    <div v-else-if="filtered.length === 0" class="d-flex flex-column align-center justify-center py-20 text-center">
      <div class="empty-icon d-flex align-center justify-center rounded-2xl mb-5">
        <v-icon size="52" color="primary" style="opacity:.5;">mdi-account-star-outline</v-icon>
      </div>
      <div class="font-display text-h5 mb-2">No characters yet</div>
      <div class="text-medium-emphasis mb-6" style="max-width:340px;">
        Create your first AI Vtuber character to get started with NagiFlow.
      </div>
      <v-btn color="primary" prepend-icon="mdi-plus" :to="{ name: 'character-create' }" class="glow-cyan" size="large">
        Create Character
      </v-btn>
    </div>

    <!-- Grid view -->
    <v-row v-else-if="viewMode === 'grid'" dense>
      <v-col
        v-for="char in filtered"
        :key="char.id"
        cols="12" sm="6" md="4"
      >
        <CharacterCard :character="char" @deleted="charStore.fetchList()" />
      </v-col>
    </v-row>

    <!-- List view -->
    <v-card v-else class="glass" rounded="xl">
      <v-list lines="two" bg-color="transparent">
        <v-list-item
          v-for="char in filtered"
          :key="char.id"
          :to="{ name: 'character-detail', params: { id: char.id } }"
          rounded="xl"
          class="my-1"
        >
          <template #prepend>
            <v-avatar size="44" color="surface-2" class="mr-3">
              <span class="font-display font-weight-bold text-primary" style="font-size:16px;">
                {{ char.name.charAt(0) }}
              </span>
            </v-avatar>
          </template>
          <v-list-item-title class="font-weight-medium">{{ char.name }}</v-list-item-title>
          <v-list-item-subtitle>{{ char.description ?? 'No description' }}</v-list-item-subtitle>
          <template #append>
            <div class="d-flex align-center ga-2">
              <v-chip v-if="char.model_type" size="x-small" :class="char.model_type === 'live2d' ? 'chip-cyan' : 'chip-violet'">
                {{ char.model_type }}
              </v-chip>
              <v-chip v-if="char.is_public" size="x-small" class="chip-emerald">public</v-chip>
              <v-btn icon="mdi-chat-outline" size="x-small" variant="text" @click.prevent="goChat(char.id)" />
            </div>
          </template>
        </v-list-item>
      </v-list>
    </v-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCharactersStore } from '@/stores/characters'
import CharacterCard from '@/components/character/CharacterCard.vue'

const router    = useRouter()
const charStore = useCharactersStore()

const search     = ref('')
const filterType = ref(null)
const viewMode   = ref('grid')
const typeOptions = [
  { title: 'Live2D', value: 'live2d' },
  { title: '3D',     value: '3d' },
]

const filtered = computed(() => {
  let list = charStore.list
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(c =>
      c.name.toLowerCase().includes(q) ||
      (c.description ?? '').toLowerCase().includes(q)
    )
  }
  if (filterType.value) {
    list = list.filter(c => c.model_type === filterType.value)
  }
  return list
})

function goChat(id) {
  router.push({ name: 'character-chat', params: { id } })
}

onMounted(() => charStore.fetchList())
</script>

<style scoped>
.empty-icon {
  width: 100px; height: 100px;
  background: rgba(6,182,212,0.07);
  border: 1px dashed rgba(6,182,212,0.3);
}
</style>