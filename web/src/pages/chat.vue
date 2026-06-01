<template>
  <v-container class="py-6" style="max-width: 860px;">
    <div class="d-flex align-center mb-4">
      <div>
        <h1 class="text-h5 font-weight-medium">{{ t('chat.title') }}</h1>
        <p class="text-body-2 text-medium-emphasis mb-0">{{ t('chat.description') }}</p>
      </div>
      <v-spacer />
      <v-btn
        v-if="store.conversation"
        variant="text"
        size="small"
        prepend-icon="mdi-account-switch"
        @click="leave"
      >
        {{ t('chat.switch') }}
      </v-btn>
    </div>

    <!-- Character picker -->
    <template v-if="!store.conversation">
      <v-skeleton-loader v-if="characters.status === 'loading'" type="card, card" />
      <v-card
        v-else-if="visible.length === 0"
        variant="flat"
        color="surface-container"
        class="pa-8 text-center"
      >
        <v-icon icon="mdi-account-off-outline" size="40" class="mb-3 text-medium-emphasis" />
        <div class="text-body-1">{{ t('chat.noCharacters') }}</div>
      </v-card>
      <v-row v-else>
        <v-col v-for="c in visible" :key="c.id" cols="12" sm="6">
          <v-card :elevation="1" class="h-100" @click="begin(c.id)">
            <v-card-item>
              <template #prepend>
                <v-avatar color="primary-container" icon="mdi-robot-outline" />
              </template>
              <v-card-title>{{ c.name || t('characters.untitled') }}</v-card-title>
              <v-card-subtitle class="text-truncate">{{ c.description }}</v-card-subtitle>
            </v-card-item>
          </v-card>
        </v-col>
      </v-row>
    </template>

    <!-- Chat -->
    <template v-else>
      <v-card variant="flat" color="surface-container" class="mb-3 d-flex align-center pa-3">
        <v-avatar color="primary-container" icon="mdi-robot-outline" size="36" class="mr-3" />
        <div class="font-weight-medium">{{ activeName }}</div>
        <v-spacer />
        <v-chip
          v-if="store.lastAffect"
          size="small"
          variant="tonal"
          :color="emotionColor(store.lastAffect.label)"
          :prepend-icon="emotionIcon(store.lastAffect.label)"
        >
          {{ emotionLabel(store.lastAffect.label) }}
          <span class="ml-1 text-medium-emphasis">{{ Math.round(store.lastAffect.intensity * 100) }}%</span>
        </v-chip>
      </v-card>

      <v-card variant="outlined" class="mb-3">
        <div ref="scrollEl" class="pa-4 overflow-y-auto" style="height: 52vh;">
          <div v-if="store.messages.length === 0" class="text-center text-medium-emphasis py-12">
            {{ t('chat.empty') }}
          </div>
          <div
            v-for="m in store.messages"
            :key="m.id"
            class="d-flex mb-3"
            :class="m.role === 'user' ? 'justify-end' : 'justify-start'"
          >
            <div
              class="pa-3 rounded-lg"
              style="max-width: 78%; white-space: pre-wrap;"
              :class="m.role === 'user' ? 'bg-primary text-on-primary' : 'bg-surface'"
            >
              <div>{{ m.content }}</div>
              <div
                v-if="m.role === 'character' && m.meta?.affect && m.meta.affect.label !== 'neutral'"
                class="text-caption text-medium-emphasis mt-1"
              >
                <v-icon :icon="emotionIcon(m.meta.affect.label)" size="x-small" />
                {{ emotionLabel(m.meta.affect.label) }}
              </div>
            </div>
          </div>
        </div>
      </v-card>

      <v-form @submit.prevent="submit">
        <div class="d-flex ga-2">
          <v-text-field
            v-model="draft"
            :placeholder="t('chat.placeholder')"
            variant="outlined"
            density="comfortable"
            hide-details
            :disabled="store.sending"
            autofocus
          />
          <v-btn
            type="submit"
            color="primary"
            icon="mdi-send"
            :loading="store.sending"
            :disabled="!draft.trim()"
            :aria-label="t('chat.send')"
          />
        </div>
      </v-form>
    </template>

    <v-snackbar
      :model-value="!!error"
      color="error"
      :timeout="6000"
      @update:model-value="error = ''"
    >
      {{ error }}
    </v-snackbar>
  </v-container>
</template>

<script lang="ts" setup>
  import { computed, nextTick, onMounted, ref, watch } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useCharactersStore } from '@/stores/characters'
  import { useConversationStore } from '@/stores/conversation'

  const { t } = useI18n()
  const characters = useCharactersStore()
  const store = useConversationStore()

  const draft = ref('')
  const error = ref('')
  const scrollEl = ref<HTMLElement | null>(null)

  const visible = computed(() => characters.items.filter(c => c.status !== 'archived'))
  const activeName = computed(() => {
    const id = store.conversation?.character_id
    return characters.items.find(c => c.id === id)?.name || t('characters.untitled')
  })

  // Hex values: Vuetify 4's `color` prop takes theme tokens or CSS colors, not Material names.
  const EMOTION_COLOR: Record<string, string> = {
    joy: '#F59E0B', affection: '#EC4899', curiosity: '#06B6D4', surprise: '#8B5CF6',
    sadness: '#3B82F6', anger: '#EF4444', fear: '#6366F1', disgust: '#10B981', neutral: '#9E9E9E',
  }
  const EMOTION_ICON: Record<string, string> = {
    joy: 'mdi-emoticon-happy-outline', affection: 'mdi-heart-outline',
    curiosity: 'mdi-lightbulb-on-outline', surprise: 'mdi-emoticon-surprised-outline',
    sadness: 'mdi-emoticon-sad-outline', anger: 'mdi-emoticon-angry-outline',
    fear: 'mdi-emoticon-frown-outline', disgust: 'mdi-emoticon-neutral-outline',
    neutral: 'mdi-emoticon-neutral-outline',
  }
  const emotionColor = (l: string) => EMOTION_COLOR[l] ?? 'grey'
  const emotionIcon = (l: string) => EMOTION_ICON[l] ?? 'mdi-emoticon-neutral-outline'
  const emotionLabel = (l: string) => t(`chat.emotion.${l}`)

  async function begin (id: string) {
    try {
      await store.start(id)
      scrollToBottom()
    } catch (e) {
      error.value = (e as Error).message || t('error.generic')
    }
  }
  function leave () {
    store.reset()
  }
  async function submit () {
    const text = draft.value.trim()
    if (!text) return
    draft.value = ''
    try {
      await store.send(text)
      scrollToBottom()
    } catch (e) {
      draft.value = text // restore so the user doesn't lose their message
      error.value = (e as Error).message || t('error.generic')
    }
  }
  function scrollToBottom () {
    nextTick(() => {
      if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
    })
  }

  watch(() => store.messages.length, scrollToBottom)

  onMounted(() => {
    if (characters.items.length === 0) characters.load()
  })
</script>
