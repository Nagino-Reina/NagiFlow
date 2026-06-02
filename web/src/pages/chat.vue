<template>
  <v-container class="pa-0 fill-height align-stretch" fluid>
    <v-row class="fill-height" no-gutters>
      <!-- Sidebar -->
      <v-col class="d-flex flex-column border-e" cols="12" md="3" style="min-height: 0;">
        <!-- Active conversation info + actions -->
        <div class="pa-3">
          <template v-if="store.conversation">
            <div class="d-flex align-center mb-2">
              <v-avatar class="mr-2" color="primary-container" icon="mdi-robot-outline" size="32" />
              <div class="font-weight-medium text-truncate">{{ activeName }}</div>
            </div>

            <v-chip
              v-if="store.lastAffect"
              class="mb-3"
              :color="emotionColor(store.lastAffect.label)"
              :prepend-icon="emotionIcon(store.lastAffect.label)"
              size="small"
              variant="tonal"
            >
              {{ emotionLabel(store.lastAffect.label) }}
              <span class="ml-1 text-medium-emphasis">{{ Math.round(store.lastAffect.intensity * 100) }}%</span>
            </v-chip>
          </template>

          <div v-else class="text-subtitle-2 mb-2">{{ t('chat.title') }}</div>

          <v-btn
            block
            class="mb-2"
            prepend-icon="mdi-account-switch"
            size="small"
            variant="tonal"
            @click="switchCharacter"
          >
            {{ store.conversation ? t('chat.switch') : t('chat.newConversation') }}
          </v-btn>

          <div class="d-flex align-center">
            <v-switch
              color="primary"
              density="compact"
              hide-details
              :label="t('chat.autoplay')"
              :model-value="ui.autoplayVoice"
              @update:model-value="ui.setAutoplayVoice(!!$event)"
            />
          </div>

          <v-tooltip location="bottom" :text="t('chat.liveSoon')">
            <template #activator="{ props }">
              <div v-bind="props" class="d-inline-block">
                <v-switch
                  color="primary"
                  density="compact"
                  disabled
                  hide-details
                  :label="t('chat.liveMode')"
                  :model-value="false"
                />
              </div>
            </template>
          </v-tooltip>
        </div>

        <v-divider />

        <!-- History -->
        <div class="text-overline px-3 pt-2 text-medium-emphasis">{{ t('chat.history') }}</div>

        <v-list class="overflow-y-auto flex-grow-1" density="compact" style="min-height: 0;">
          <v-list-item
            v-for="conv in store.history"
            :key="conv.id"
            :active="conv.id === store.conversation?.id"
            prepend-icon="mdi-message-outline"
            :subtitle="formatDate(conv.created_at)"
            :title="charName(conv.character_id)"
            @click="selectHistory(conv)"
          >
            <template #append>
              <v-btn
                :aria-label="t('chat.deleteConversation')"
                icon="mdi-delete-outline"
                size="x-small"
                variant="text"
                @click.stop="confirmDeleteId = conv.id"
              />
            </template>
          </v-list-item>

          <v-list-item v-if="store.history.length === 0" class="text-medium-emphasis text-caption">
            {{ t('chat.noHistory') }}
          </v-list-item>
        </v-list>
      </v-col>

      <!-- Main: stage + thread, or picker -->
      <v-col class="d-flex flex-column" cols="12" md="9" style="min-height: 0; height: calc(100vh - 64px - 34px);">
        <!-- Character picker -->
        <template v-if="showPicker">
          <div class="pa-6 overflow-y-auto">
            <h2 class="text-h6 mb-4">{{ t('chat.pickCharacter') }}</h2>
            <v-skeleton-loader v-if="characters.status === 'loading'" type="card, card" />

            <v-card
              v-else-if="visible.length === 0"
              class="pa-8 text-center"
              color="surface-container"
              variant="flat"
            >
              <v-icon class="mb-3 text-medium-emphasis" icon="mdi-account-off-outline" size="40" />
              <div class="text-body-1">{{ t('chat.noCharacters') }}</div>
            </v-card>

            <v-row v-else>
              <v-col
                v-for="c in visible"
                :key="c.id"
                cols="12"
                lg="4"
                sm="6"
              >
                <v-card class="h-100" :elevation="1" @click="begin(c.id)">
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
          </div>
        </template>

        <!-- Stage + message thread -->
        <template v-else>
          <!-- Character stage (P1: portrait / audio-only fallback) -->
          <div class="d-flex flex-column align-center justify-center bg-surface-container" style="height: 38%;">
            <v-avatar color="primary-container" size="96">
              <v-img v-if="stagePortraitUrl" alt="" cover :src="stagePortraitUrl" />
              <v-icon v-else icon="mdi-robot-outline" />
            </v-avatar>

            <div class="text-body-2 text-medium-emphasis mt-2">{{ activeName }}</div>
          </div>

          <div ref="scrollEl" class="pa-4 overflow-y-auto flex-grow-1" style="min-height: 0;">
            <div v-if="store.messages.length === 0" class="text-center text-medium-emphasis py-8">
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
                :class="m.role === 'user' ? 'bg-primary text-on-primary' : 'bg-surface-container'"
                style="max-width: 78%; white-space: pre-wrap;"
              >
                <div>{{ m.content }}</div>

                <div
                  v-if="m.role === 'character' && m.meta?.affect && m.meta.affect.label !== 'neutral'"
                  class="text-caption text-medium-emphasis mt-1"
                >
                  <v-icon :icon="emotionIcon(m.meta.affect.label)" size="x-small" />
                  {{ emotionLabel(m.meta.affect.label) }}
                </div>

                <v-btn
                  v-if="m.role === 'character' && m.media_asset_id"
                  class="mt-1"
                  density="comfortable"
                  prepend-icon="mdi-volume-high"
                  size="x-small"
                  variant="text"
                  @click="playAudio(m.media_asset_id)"
                >
                  {{ t('chat.play') }}
                </v-btn>
              </div>
            </div>
          </div>

          <v-form class="pa-3" @submit.prevent="submit">
            <div class="d-flex ga-2">
              <v-text-field
                v-model="draft"
                autofocus
                density="comfortable"
                :disabled="store.sending"
                hide-details
                :placeholder="t('chat.placeholder')"
                variant="outlined"
              />

              <v-btn
                :aria-label="t('chat.send')"
                color="primary"
                :disabled="!draft.trim()"
                icon="mdi-send"
                :loading="store.sending"
                type="submit"
              />
            </div>
          </v-form>
        </template>
      </v-col>
    </v-row>

    <v-dialog max-width="360" :model-value="!!confirmDeleteId" @update:model-value="confirmDeleteId = null">
      <v-card>
        <v-card-title class="text-subtitle-1">{{ t('chat.deleteConversation') }}</v-card-title>
        <v-card-text class="text-body-2">{{ t('chat.deleteConfirm') }}</v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="confirmDeleteId = null">{{ t('common.action.cancel') }}</v-btn>
          <v-btn color="error" variant="text" @click="doDelete">{{ t('chat.deleteConversation') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar color="error" :model-value="!!error" :timeout="6000" @update:model-value="error = ''">
      {{ error }}
    </v-snackbar>
  </v-container>
</template>

<script lang="ts" setup>
  import type { Conversation } from '@/api/types'
  import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { charactersApi } from '@/api/characters'
  import { mediaApi } from '@/api/media'
  import { useCharactersStore } from '@/stores/characters'
  import { useConversationStore } from '@/stores/conversation'
  import { useUiStore } from '@/stores/ui'

  const { t } = useI18n()
  const characters = useCharactersStore()
  const store = useConversationStore()
  const ui = useUiStore()

  const draft = ref('')
  const error = ref('')
  const pickingManual = ref(false)
  const confirmDeleteId = ref<string | null>(null)
  const scrollEl = ref<HTMLElement | null>(null)

  const visible = computed(() => characters.items.filter(c => c.status !== 'archived'))
  const showPicker = computed(() => (!store.conversation && !store.pendingCharacterId) || pickingManual.value)
  function charName (id: string | null) {
    return characters.items.find(c => c.id === id)?.name || t('characters.untitled')
  }
  const activeName = computed(() => charName(store.activeCharacterId ?? null))

  // Stage portrait: fetched with the session token (a native <img src> can't carry it).
  const stagePortraitUrl = ref<string | null>(null)
  async function loadStagePortrait (id: string | null | undefined) {
    if (stagePortraitUrl.value) {
      URL.revokeObjectURL(stagePortraitUrl.value)
      stagePortraitUrl.value = null
    }
    if (id) stagePortraitUrl.value = await charactersApi.portraitObjectUrl(id)
  }
  watch(() => store.activeCharacterId, loadStagePortrait, { immediate: true })

  function formatDate (iso: string) {
    return new Date(iso).toLocaleDateString()
  }

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

  function switchCharacter () {
    pickingManual.value = true
  }
  function begin (id: string) {
    // Select only — the conversation is created on the first message (store.send).
    store.selectCharacter(id)
    pickingManual.value = false
  }
  async function selectHistory (conv: Conversation) {
    try {
      await store.open(conv)
      pickingManual.value = false
      scrollToBottom()
    } catch (error_) {
      error.value = (error_ as Error).message || t('error.generic')
    }
  }
  async function doDelete () {
    const id = confirmDeleteId.value
    confirmDeleteId.value = null
    if (!id) return
    try {
      await store.remove(id)
    } catch (error_) {
      error.value = (error_ as Error).message || t('error.generic')
    }
  }

  let currentAudio: HTMLAudioElement | null = null
  let currentAudioUrl: string | null = null
  async function playAudio (id: string) {
    if (currentAudio) currentAudio.pause()
    if (currentAudioUrl) {
      URL.revokeObjectURL(currentAudioUrl)
      currentAudioUrl = null
    }
    try {
      currentAudioUrl = await mediaApi.fetchObjectUrl(id)
      currentAudio = new Audio(currentAudioUrl)
      // Autoplay may be blocked without a gesture; ignore — the play button still works.
      currentAudio.play().catch(() => {})
    } catch {
      // playback is best-effort; a failed fetch shouldn't surface an error
    }
  }
  async function submit () {
    const text = draft.value.trim()
    if (!text) return
    draft.value = ''
    try {
      await store.send(text)
      scrollToBottom()
      const last = store.messages.at(-1)
      if (ui.autoplayVoice && last?.role === 'character' && last.media_asset_id) {
        playAudio(last.media_asset_id)
      }
    } catch (error_) {
      draft.value = text // restore so the user doesn't lose their message
      error.value = (error_ as Error).message || t('error.generic')
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
    store.loadHistory().catch(() => {})
  })
  onUnmounted(() => {
    currentAudio?.pause()
    if (currentAudioUrl) URL.revokeObjectURL(currentAudioUrl)
    if (stagePortraitUrl.value) URL.revokeObjectURL(stagePortraitUrl.value)
  })
</script>
