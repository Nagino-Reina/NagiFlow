<template>
  <v-card class="glass char-card" rounded="xl" height="100%">
    <!-- Header gradient strip -->
    <div class="card-strip" :style="{ background: stripGradient }" />

    <v-card-text class="pt-6 pb-4 px-4">
      <!-- Avatar + badges -->
      <div class="d-flex align-start ga-3 mb-4">
        <v-avatar size="52" color="surface-2" class="avatar-ring flex-shrink-0">
          <span class="font-display font-weight-bold text-h6" :style="{ color: primaryColor }">
            {{ character.name.charAt(0) }}
          </span>
        </v-avatar>
        <div class="flex-1 overflow-hidden pt-1">
          <div class="text-h6 font-display font-weight-semibold text-truncate" style="letter-spacing:-.02em;">
            {{ character.name }}
          </div>
          <div class="text-caption text-medium-emphasis text-truncate mt-0.5">
            {{ character.description ?? 'No description provided.' }}
          </div>
        </div>
      </div>

      <!-- Badges -->
      <div class="d-flex flex-wrap ga-1 mb-4">
        <v-chip v-if="character.model_type" size="x-small"
          :class="character.model_type === 'live2d' ? 'chip-cyan' : 'chip-violet'">
          {{ character.model_type === 'live2d' ? 'Live2D' : '3D' }}
        </v-chip>
        <v-chip v-if="character.tts_provider" size="x-small" class="chip-pink">
          {{ character.tts_provider }}
        </v-chip>
        <v-chip v-if="character.llm_model" size="x-small" variant="outlined" density="compact">
          {{ character.llm_model }}
        </v-chip>
        <v-chip v-if="character.is_public" size="x-small" class="chip-emerald">
          public
        </v-chip>
      </div>

      <!-- Mini Big Five bars -->
      <div v-if="bigFive" class="big5-mini mb-3">
        <div
          v-for="(score, trait) in bigFive"
          :key="trait"
          class="d-flex align-center ga-2 mb-1"
        >
          <div class="text-caption font-mono text-medium-emphasis" style="width:14px;text-align:center;">
            {{ trait.charAt(0).toUpperCase() }}
          </div>
          <v-progress-linear
            :model-value="score"
            max="100"
            height="4"
            :color="traitColor(trait)"
            bg-color="surface-3"
            rounded
          />
        </div>
      </div>
    </v-card-text>

    <v-divider style="opacity:.06;" />

    <v-card-actions class="pa-3 ga-1">
      <v-btn
        icon="mdi-chat-outline"
        size="small"
        variant="tonal"
        color="primary"
        @click="$router.push({ name: 'character-chat', params: { id: character.id } })"
      >
        <v-tooltip activator="parent">Chat</v-tooltip>
      </v-btn>
      <v-btn
        icon="mdi-pencil-outline"
        size="small"
        variant="text"
        @click="$router.push({ name: 'character-edit', params: { id: character.id } })"
      >
        <v-tooltip activator="parent">Edit</v-tooltip>
      </v-btn>
      <v-btn
        icon="mdi-book-open-outline"
        size="small"
        variant="text"
        @click="$router.push({ name: 'character-detail', params: { id: character.id } })"
      >
        <v-tooltip activator="parent">Detail</v-tooltip>
      </v-btn>
      <v-spacer />
      <v-btn
        icon="mdi-delete-outline"
        size="small"
        variant="text"
        color="error"
        @click="deleteChar"
      >
        <v-tooltip activator="parent">Delete</v-tooltip>
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { computed } from 'vue'
import { useCharactersStore } from '@/stores/characters'
import { useAppStore } from '@/stores/app'

const props = defineProps({ character: { type: Object, required: true } })
const emit  = defineEmits(['deleted'])

const charStore = useCharactersStore()
const app       = useAppStore()

const bigFive = computed(() => props.character.personality?.big_five ?? null)

const traitColors = {
  openness:          '#06B6D4',
  conscientiousness: '#8B5CF6',
  extraversion:      '#EC4899',
  agreeableness:     '#10B981',
  neuroticism:       '#F59E0B',
}
function traitColor(t) { return traitColors[t] ?? '#06B6D4' }

// Derive a strip gradient from Big Five averages
const primaryColor = computed(() => '#06B6D4')
const stripGradient = computed(() => {
  const e = bigFive.value?.extraversion ?? 50
  const o = bigFive.value?.openness ?? 50
  if (e > 65)  return 'linear-gradient(90deg,rgba(236,72,153,0.6),rgba(139,92,246,0.3))'
  if (o > 65)  return 'linear-gradient(90deg,rgba(6,182,212,0.6),rgba(16,185,129,0.3))'
  return       'linear-gradient(90deg,rgba(6,182,212,0.4),rgba(139,92,246,0.3))'
})

async function deleteChar() {
  const confirmed = await app.showConfirm(
    'Delete Character',
    `Are you sure you want to delete "${props.character.name}"? This cannot be undone.`
  )
  if (!confirmed) return
  try {
    await charStore.remove(props.character.id)
    app.notify('Character deleted.')
    emit('deleted')
  } catch (err) { app.notifyError(err) }
}
</script>

<style scoped>
.char-card { transition: transform 0.2s, box-shadow 0.2s; position: relative; }
.char-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(6,182,212,0.12) !important;
}
.card-strip {
  height: 4px;
  border-radius: 12px 12px 0 0;
}
.avatar-ring {
  outline: 2px solid rgba(6,182,212,0.25);
  outline-offset: 2px;
}
</style>