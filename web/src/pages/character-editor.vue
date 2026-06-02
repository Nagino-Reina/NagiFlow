<template>
  <v-container class="py-6" style="max-width: 1100px;">
    <div class="d-flex align-center mb-4 ga-2">
      <v-btn prepend-icon="mdi-arrow-left" :to="'/characters'" variant="text">
        {{ t('characters.back') }}
      </v-btn>

      <v-spacer />

      <v-btn
        color="primary"
        :disabled="!nameValid"
        :loading="saving"
        prepend-icon="mdi-content-save"
        @click="save"
      >
        {{ isNew ? t('characters.create') : t('common.action.save') }}
      </v-btn>
    </div>

    <v-alert
      v-if="errorCode"
      class="mb-4"
      closable
      density="compact"
      :text="te(`error.${errorCode}`) ? t(`error.${errorCode}`) : t('error.generic')"
      type="error"
      variant="tonal"
      @click:close="errorCode = null"
    />

    <v-tabs v-model="tab" class="mb-4" color="primary">
      <v-tab value="profile">{{ t('characters.tabs.profile') }}</v-tab>
      <v-tab value="personality">{{ t('characters.tabs.personality') }}</v-tab>
      <v-tab value="voice">{{ t('characters.tabs.voice') }}</v-tab>
      <v-tab value="memory">{{ t('characters.tabs.memory') }}</v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <!-- Profile -->
      <v-window-item value="profile">
        <v-row>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="form.name"
              :label="t('characters.fields.name')"
              :rules="[v => !!(v && v.trim()) || t('common.validation.required')]"
            />

            <v-text-field
              v-model="aliasesText"
              :hint="t('characters.fields.aliasesHint')"
              :label="t('characters.fields.aliases')"
              persistent-hint
            />

            <v-text-field
              v-model="tagsText"
              class="mt-3"
              :hint="t('characters.fields.tagsHint')"
              :label="t('characters.fields.tags')"
              persistent-hint
            />

            <v-select
              v-model="form.default_language"
              class="mt-3"
              :items="LANGUAGES"
              :label="t('characters.fields.language')"
            />
          </v-col>

          <v-col cols="12" md="6">
            <div class="d-flex align-center ga-4 mb-3">
              <v-avatar color="surface-container" size="80">
                <v-img v-if="portraitUrl" alt="" cover :src="portraitUrl" />
                <v-icon v-else icon="mdi-account" size="40" />
              </v-avatar>

              <div class="flex-grow-1">
                <v-file-input
                  v-model="portraitFile"
                  accept="image/png,image/jpeg,image/webp"
                  density="compact"
                  :disabled="isNew || portraitBusy"
                  :hint="isNew ? t('characters.portrait.saveFirst') : t('characters.portrait.hint')"
                  :label="t('characters.portrait.label')"
                  :loading="portraitBusy"
                  persistent-hint
                  prepend-icon="mdi-image"
                  @update:model-value="onPortraitPick"
                />

                <v-btn
                  v-if="portraitUrl"
                  color="error"
                  :loading="portraitBusy"
                  size="x-small"
                  variant="text"
                  @click="removePortrait"
                >
                  {{ t('characters.portrait.remove') }}
                </v-btn>
              </div>
            </div>

            <v-textarea v-model="form.description" auto-grow :label="t('characters.fields.description')" rows="2" />

            <v-textarea
              v-model="form.persona"
              auto-grow
              :hint="t('characters.fields.personaHint')"
              :label="t('characters.fields.persona')"
              persistent-hint
              rows="6"
            />
          </v-col>

          <v-col class="d-flex align-center ga-4" cols="12">
            <v-switch
              v-model="form.guest_visible"
              color="primary"
              hide-details
              inset
              :label="t('characters.guestVisible')"
            />

            <v-select
              v-if="!isNew"
              v-model="form.status"
              hide-details
              :items="STATUSES"
              :label="t('characters.fields.status')"
              style="max-width: 220px;"
            />
          </v-col>
        </v-row>
      </v-window-item>

      <!-- Personality -->
      <v-window-item value="personality">
        <v-row>
          <v-col cols="12" md="7">
            <div class="text-subtitle-1 mb-1">{{ t('characters.personality.title') }}</div>
            <p class="text-body-2 text-medium-emphasis mb-4">{{ t('characters.personality.hint') }}</p>

            <div v-for="trait in TRAITS" :key="trait" class="mb-3">
              <div class="d-flex justify-space-between align-center text-body-2">
                <span class="font-weight-medium">{{ t(`characters.personality.traits.${trait}`) }}</span>

                <span class="d-flex align-center ga-1 text-medium-emphasis">
                  <v-tooltip
                    :disabled="!directiveFor(trait)"
                    location="top"
                    max-width="280"
                    :text="directiveFor(trait)"
                  >
                    <template #activator="{ props }">
                      <span v-bind="props" class="trait-score">{{ form.big_five[trait] }}</span>
                    </template>
                  </v-tooltip>

                  <v-chip color="primary" size="x-small" variant="tonal">
                    {{ t(`characters.personality.bands.${bandKey(form.big_five[trait])}`) }}
                  </v-chip>
                </span>
              </div>

              <v-slider
                v-model="form.big_five[trait]"
                :aria-label="t(`characters.personality.traits.${trait}`)"
                color="primary"
                hide-details
                :max="100"
                :min="0"
                :step="1"
              />

              <div class="text-caption text-medium-emphasis">
                {{ t(`characters.personality.traitDesc.${trait}`) }}
              </div>
            </div>
          </v-col>

          <v-col cols="12" md="5">
            <v-card class="pa-4" color="surface-container" variant="flat">
              <div class="text-subtitle-2 mb-2">{{ t('characters.personality.resulting') }}</div>

              <BigFiveRadar :aria-label="t('characters.personality.title')" :data="radarData" />

              <p class="text-caption text-medium-emphasis text-center mt-1 mb-0">
                {{ t('characters.personality.radarHint') }}
              </p>

              <v-divider class="my-3" />

              <div class="text-caption text-medium-emphasis mb-2">
                {{ t('characters.personality.params') }}
              </div>

              <div v-if="mapping" class="d-flex flex-column ga-1 text-body-2">
                <div class="d-flex justify-space-between">
                  <span>{{ t('characters.personality.temperature') }}</span><span>{{ mapping.temperature }}</span>
                </div>

                <div class="d-flex justify-space-between">
                  <span>{{ t('characters.personality.topP') }}</span><span>{{ mapping.top_p }}</span>
                </div>

                <div class="d-flex justify-space-between">
                  <span>{{ t('characters.personality.verbosity') }}</span><span>{{ mapping.verbosity }}</span>
                </div>

                <div class="d-flex justify-space-between">
                  <span>{{ t('characters.personality.speechRate') }}</span><span>{{ mapping.speech_rate }}</span>
                </div>

                <div class="d-flex justify-space-between">
                  <span>{{ t('characters.personality.expressiveness') }}</span><span>{{ mapping.expressiveness }}</span>
                </div>

                <div class="d-flex justify-space-between">
                  <span>{{ t('characters.personality.voiceStyle') }}</span>
                  <span>{{ mapping.voice_style.length > 0 ? mapping.voice_style.join(', ') : t('characters.personality.none') }}</span>
                </div>
              </div>
            </v-card>
          </v-col>
        </v-row>
      </v-window-item>

      <v-window-item value="voice">
        <v-card v-if="isNew" class="pa-6 text-center" color="surface-container" variant="flat">
          <v-icon class="mb-2 text-medium-emphasis" icon="mdi-content-save-outline" size="36" />
          <div class="text-body-2 text-medium-emphasis">{{ t('characters.voice.saveFirst') }}</div>
        </v-card>

        <template v-else>
          <v-card class="mb-4" color="surface-container" variant="flat">
            <v-list v-if="voice.models.length > 0" bg-color="transparent">
              <v-list-item v-for="vm in voice.models" :key="vm.id">
                <template #prepend>
                  <v-icon :icon="vm.kind === 'zero_shot' ? 'mdi-account-voice' : 'mdi-waveform'" />
                </template>

                <v-list-item-title class="d-flex align-center ga-2">
                  {{ t(`characters.voice.kinds.${vm.kind}`) }}
                  <v-chip v-if="vm.is_default" color="success" size="x-small" variant="tonal">
                    {{ t('characters.voice.active') }}
                  </v-chip>
                </v-list-item-title>

                <v-list-item-subtitle>
                  {{ vm.design_description || `${t('characters.voice.provider')}: ${vm.provider}` }}
                </v-list-item-subtitle>

                <template #append>
                  <v-btn
                    :aria-label="t('characters.voice.preview')"
                    icon="mdi-play"
                    :loading="previewingId === vm.id"
                    size="small"
                    variant="text"
                    @click="playPreview(vm.id)"
                  />

                  <v-btn
                    v-if="!vm.is_default"
                    size="small"
                    :text="t('characters.voice.setDefault')"
                    variant="text"
                    @click="makeDefault(vm.id)"
                  />

                  <v-btn
                    :aria-label="t('characters.voice.delete')"
                    icon="mdi-delete-outline"
                    size="small"
                    variant="text"
                    @click="pendingDeleteVoice = vm"
                  />
                </template>
              </v-list-item>
            </v-list>

            <div v-else class="pa-6 text-center text-body-2 text-medium-emphasis">
              {{ t('characters.voice.empty') }}
            </div>
          </v-card>

          <v-row>
            <v-col v-if="voice.caps?.voice_design" cols="12" md="6">
              <v-card class="pa-4 h-100" color="surface-container" variant="flat">
                <div class="text-subtitle-2 mb-1">{{ t('characters.voice.design.title') }}</div>
                <p class="text-caption text-medium-emphasis mb-2">{{ t('characters.voice.design.hint') }}</p>

                <v-textarea
                  v-model="designText"
                  auto-grow
                  :placeholder="t('characters.voice.design.placeholder')"
                  rows="2"
                />

                <v-btn
                  color="primary"
                  :disabled="!designText.trim()"
                  :loading="voiceBusy"
                  @click="addDesign"
                >{{ t('characters.voice.design.create') }}</v-btn>
              </v-card>
            </v-col>

            <v-col v-if="voice.caps?.voice_clone" cols="12" md="6">
              <v-card class="pa-4 h-100" color="surface-container" variant="flat">
                <div class="text-subtitle-2 mb-1">{{ t('characters.voice.clone.title') }}</div>
                <p class="text-caption text-medium-emphasis mb-2">{{ t('characters.voice.clone.hint') }}</p>

                <v-file-input
                  v-model="cloneFile"
                  accept="audio/*"
                  :label="t('characters.voice.clone.file')"
                  prepend-icon="mdi-microphone"
                />

                <v-textarea
                  v-model="cloneText"
                  auto-grow
                  class="mb-2"
                  :hint="t('characters.voice.clone.transcriptHint')"
                  :label="t('characters.voice.clone.transcript')"
                  persistent-hint
                  rows="2"
                />

                <v-btn
                  color="primary"
                  :disabled="!hasCloneFile || !cloneText.trim()"
                  :loading="voiceBusy"
                  @click="addClone"
                >{{ t('characters.voice.clone.create') }}</v-btn>
              </v-card>
            </v-col>

            <v-col v-if="voice.caps && !voice.caps.voice_design && !voice.caps.voice_clone" cols="12">
              <v-alert :text="t('characters.voice.unsupported')" type="info" variant="tonal" />
            </v-col>
          </v-row>
        </template>
      </v-window-item>

      <v-window-item value="memory">
        <v-card class="pa-8 text-center" color="surface-container" variant="flat">
          <v-icon class="mb-3 text-medium-emphasis" icon="mdi-brain" size="40" />
          <div class="text-body-2 text-medium-emphasis">{{ t('characters.memory.comingSoon') }}</div>
        </v-card>
      </v-window-item>
    </v-window>

    <v-snackbar v-model="savedSnack" color="success" timeout="2000">
      {{ t('characters.saved') }}
    </v-snackbar>

    <v-dialog
      max-width="420"
      :model-value="pendingDeleteVoice !== null"
      @update:model-value="pendingDeleteVoice = null"
    >
      <v-card>
        <v-card-title class="text-h6">{{ t('characters.voice.delete') }}</v-card-title>
        <v-card-text>{{ t('characters.voice.deleteConfirm') }}</v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="pendingDeleteVoice = null">{{ t('common.action.cancel') }}</v-btn>

          <v-btn color="error" :loading="voiceBusy" variant="flat" @click="confirmDeleteVoice">
            {{ t('characters.voice.delete') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script lang="ts" setup>
  import type { BigFive, CharacterCreate, CharacterStatus, VoiceModel } from '@/api/types'
  import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useRoute, useRouter } from 'vue-router'
  import { charactersApi } from '@/api/characters'
  import { ApiError } from '@/api/http'
  import { voiceApi } from '@/api/voice'
  import BigFiveRadar from '@/components/BigFiveRadar.vue'
  import { bandIndexOf, resolvePersonality } from '@/personality/mapping'
  import { useCharactersStore } from '@/stores/characters'
  import { useVoiceStore } from '@/stores/voice'

  const { t, te } = useI18n()
  const route = useRoute()
  const router = useRouter()
  const store = useCharactersStore()
  const voice = useVoiceStore()

  const TRAITS = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'] as const
  const LANGUAGES = [
    { title: 'English', value: 'en' },
    { title: '繁體中文', value: 'zh-Hant' },
    { title: '日本語', value: 'ja' },
  ]
  const STATUSES = computed(() =>
    ['draft', 'active', 'archived'].map(v => ({ title: t(`characters.status.${v}`), value: v })))

  function bandKey (s: number) {
    const schema = store.personalitySchema
    return schema ? schema.bands[bandIndexOf(s, schema.thresholds)] : 'moderate'
  }

  function defaultBigFive (): BigFive {
    return {
      openness: 50, conscientiousness: 50, extraversion: 50, agreeableness: 50, neuroticism: 50,
    }
  }

  // Reactive id so a successful create flips this editor from create- to update-mode
  // in place (the component is reused on param change, not remounted).
  const currentId = ref(route.params.id as string)
  const isNew = computed(() => currentId.value === 'new')
  const tab = ref('profile')
  const saving = ref(false)
  const savedSnack = ref(false)
  const errorCode = ref<string | null>(null)

  const form = reactive({
    name: '',
    description: '',
    persona: '',
    default_language: 'en',
    guest_visible: false,
    status: 'draft' as string,
    big_five: defaultBigFive(),
  })
  const aliasesText = ref('')
  const tagsText = ref('')

  // --- Portrait (FR-CM-2) ---
  const portraitUrl = ref<string | null>(null)
  const portraitFile = ref<File | File[] | null>(null)
  const portraitBusy = ref(false)

  async function loadPortrait () {
    if (portraitUrl.value) {
      URL.revokeObjectURL(portraitUrl.value)
      portraitUrl.value = null
    }
    if (isNew.value) return
    portraitUrl.value = await charactersApi.portraitObjectUrl(currentId.value)
  }

  async function onPortraitPick (val: File | File[] | null) {
    const file = Array.isArray(val) ? val[0] : val
    if (!file) return
    portraitBusy.value = true
    errorCode.value = null
    try {
      await charactersApi.uploadPortrait(currentId.value, file)
      portraitFile.value = null
      await loadPortrait()
    } catch (error) {
      errorCode.value = error instanceof ApiError ? error.code : 'generic'
    } finally {
      portraitBusy.value = false
    }
  }

  async function removePortrait () {
    portraitBusy.value = true
    errorCode.value = null
    try {
      await charactersApi.deletePortrait(currentId.value)
      portraitFile.value = null
      await loadPortrait()
    } catch (error) {
      errorCode.value = error instanceof ApiError ? error.code : 'generic'
    } finally {
      portraitBusy.value = false
    }
  }

  const nameValid = computed(() => form.name.trim().length > 0)
  const splitCsv = (s: string) => s.split(',').map(x => x.trim()).filter(Boolean)

  // Computed locally from the cached spec — no request per slider move (docs/08 §3.2).
  const mapping = computed(() =>
    store.personalitySchema ? resolvePersonality(store.personalitySchema, form.big_five) : null)

  function directiveFor (trait: string) {
    return mapping.value?.traits.find(e => e.trait === trait)?.directive ?? ''
  }

  const radarData = computed(() =>
    TRAITS.map(k => ({ label: t(`characters.personality.traits.${k}`), value: form.big_five[k] })))

  // --- Voice tab ---
  const designText = ref('')
  const cloneFile = ref<File | File[] | null>(null)
  const cloneText = ref('')
  const voiceBusy = ref(false)
  const previewingId = ref<string | null>(null)
  const pendingDeleteVoice = ref<VoiceModel | null>(null)
  let audio: HTMLAudioElement | null = null
  let lastPreviewUrl: string | null = null

  function fileOf (): File | null {
    const f = cloneFile.value
    return Array.isArray(f) ? (f[0] ?? null) : f
  }
  const hasCloneFile = computed(() => fileOf() !== null)

  async function voiceAction (fn: () => Promise<unknown>) {
    voiceBusy.value = true
    errorCode.value = null
    try {
      await fn()
    } catch (error) {
      errorCode.value = error instanceof ApiError ? error.code : 'generic'
    } finally {
      voiceBusy.value = false
    }
  }

  function addDesign () {
    return voiceAction(async () => {
      await voice.createDesign(currentId.value, designText.value.trim())
      designText.value = ''
    })
  }

  function addClone () {
    return voiceAction(async () => {
      const file = fileOf()
      if (!file) return
      await voice.clone(currentId.value, file, cloneText.value.trim())
      cloneFile.value = null
      cloneText.value = ''
    })
  }

  const makeDefault = (vid: string) => voiceAction(() => voice.setDefault(currentId.value, vid))

  function confirmDeleteVoice () {
    return voiceAction(async () => {
      if (pendingDeleteVoice.value) {
        await voice.remove(currentId.value, pendingDeleteVoice.value.id)
        pendingDeleteVoice.value = null
      }
    })
  }

  async function playPreview (vid: string) {
    previewingId.value = vid
    errorCode.value = null
    try {
      const url = await voiceApi.preview(currentId.value, { voice_model_id: vid })
      audio?.pause()
      if (lastPreviewUrl) URL.revokeObjectURL(lastPreviewUrl) // free the previous clip
      lastPreviewUrl = url
      audio = new Audio(url)
      await audio.play()
    } catch (error) {
      errorCode.value = error instanceof ApiError ? error.code : 'generic'
    } finally {
      previewingId.value = null
    }
  }

  onUnmounted(() => {
    audio?.pause()
    if (lastPreviewUrl) URL.revokeObjectURL(lastPreviewUrl)
    if (portraitUrl.value) URL.revokeObjectURL(portraitUrl.value)
  })

  async function save () {
    if (saving.value) return // guard against double-submit (rapid clicks)
    saving.value = true
    errorCode.value = null
    try {
      const payload: CharacterCreate = {
        name: form.name,
        description: form.description,
        persona: form.persona,
        big_five: form.big_five,
        default_language: form.default_language,
        aliases: splitCsv(aliasesText.value),
        tags: splitCsv(tagsText.value),
        guest_visible: form.guest_visible,
      }
      if (isNew.value) {
        const created = await store.create(payload)
        currentId.value = created.id // flip to update-mode before any further save
        savedSnack.value = true
        voice.load(created.id).catch(() => { /* voice list is non-critical */ })
        router.replace(`/characters/${created.id}`)
      } else {
        await store.update(currentId.value, { ...payload, status: form.status as CharacterStatus })
        savedSnack.value = true
      }
    } catch (error) {
      errorCode.value = error instanceof ApiError ? error.code : 'generic'
    } finally {
      saving.value = false
    }
  }

  onMounted(async () => {
    store.loadPersonalitySchema().catch(() => { /* explainability panel is non-critical */ })
    voice.loadCaps().catch(() => { /* capability-gated UI degrades gracefully */ })
    if (!isNew.value) {
      voice.load(currentId.value).catch(() => { /* voice list is non-critical */ })
      loadPortrait().catch(() => { /* portrait is non-critical */ })
      try {
        const c = await store.get(currentId.value)
        form.name = c.name
        form.description = c.description
        form.persona = c.persona
        form.default_language = c.default_language
        form.guest_visible = c.guest_visible
        form.status = c.status
        form.big_five = { ...defaultBigFive(), ...c.big_five }
        aliasesText.value = c.aliases.join(', ')
        tagsText.value = c.tags.join(', ')
      } catch (error) {
        errorCode.value = error instanceof ApiError ? error.code : 'generic'
      }
    }
  })
</script>

<style scoped>
.trait-score {
  cursor: help;
  border-bottom: 1px dotted currentColor;
}
</style>
