<template>
  <v-container class="py-6" style="max-width: 1100px;">
    <div class="d-flex align-center mb-4 ga-2">
      <v-btn variant="text" prepend-icon="mdi-arrow-left" :to="'/characters'">
        {{ t('characters.back') }}
      </v-btn>
      <v-spacer />
      <v-btn
        color="primary"
        :loading="saving"
        :disabled="!nameValid"
        prepend-icon="mdi-content-save"
        @click="save"
      >
        {{ isNew ? t('characters.create') : t('common.action.save') }}
      </v-btn>
    </div>

    <v-alert
      v-if="errorCode"
      type="error"
      variant="tonal"
      density="compact"
      class="mb-4"
      closable
      :text="te(`error.${errorCode}`) ? t(`error.${errorCode}`) : t('error.generic')"
      @click:close="errorCode = null"
    />

    <v-tabs v-model="tab" color="primary" class="mb-4">
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
              :label="t('characters.fields.aliases')"
              :hint="t('characters.fields.aliasesHint')"
              persistent-hint
            />
            <v-text-field
              v-model="tagsText"
              :label="t('characters.fields.tags')"
              :hint="t('characters.fields.tagsHint')"
              persistent-hint
              class="mt-3"
            />
            <v-select
              v-model="form.default_language"
              :items="LANGUAGES"
              :label="t('characters.fields.language')"
              class="mt-3"
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-textarea v-model="form.description" :label="t('characters.fields.description')" rows="2" auto-grow />
            <v-textarea
              v-model="form.persona"
              :label="t('characters.fields.persona')"
              :hint="t('characters.fields.personaHint')"
              persistent-hint
              rows="6"
              auto-grow
            />
          </v-col>
          <v-col cols="12" class="d-flex align-center ga-4">
            <v-switch v-model="form.guest_visible" color="primary" :label="t('characters.guestVisible')" hide-details inset />
            <v-select
              v-if="!isNew"
              v-model="form.status"
              :items="STATUSES"
              :label="t('characters.fields.status')"
              style="max-width: 220px;"
              hide-details
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
                    location="top"
                    max-width="280"
                    :text="directiveFor(trait)"
                    :disabled="!directiveFor(trait)"
                  >
                    <template #activator="{ props }">
                      <span v-bind="props" class="trait-score">{{ form.big_five[trait] }}</span>
                    </template>
                  </v-tooltip>
                  <v-chip size="x-small" variant="tonal" color="primary">
                    {{ t(`characters.personality.bands.${bandKey(form.big_five[trait])}`) }}
                  </v-chip>
                </span>
              </div>
              <v-slider
                v-model="form.big_five[trait]"
                :min="0"
                :max="100"
                :step="1"
                color="primary"
                hide-details
                :aria-label="t(`characters.personality.traits.${trait}`)"
              />
              <div class="text-caption text-medium-emphasis">
                {{ t(`characters.personality.traitDesc.${trait}`) }}
              </div>
            </div>
          </v-col>

          <v-col cols="12" md="5">
            <v-card variant="flat" color="surface-container" class="pa-4">
              <div class="text-subtitle-2 mb-2">{{ t('characters.personality.resulting') }}</div>

              <BigFiveRadar :data="radarData" :aria-label="t('characters.personality.title')" />
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
                  <span>{{ mapping.voice_style.length ? mapping.voice_style.join(', ') : t('characters.personality.none') }}</span>
                </div>
              </div>
            </v-card>
          </v-col>
        </v-row>
      </v-window-item>

      <v-window-item value="voice">
        <v-card variant="flat" color="surface-container" class="pa-8 text-center">
          <v-icon icon="mdi-microphone-outline" size="40" class="mb-3 text-medium-emphasis" />
          <div class="text-body-2 text-medium-emphasis">{{ t('characters.voice.comingSoon') }}</div>
        </v-card>
      </v-window-item>

      <v-window-item value="memory">
        <v-card variant="flat" color="surface-container" class="pa-8 text-center">
          <v-icon icon="mdi-brain" size="40" class="mb-3 text-medium-emphasis" />
          <div class="text-body-2 text-medium-emphasis">{{ t('characters.memory.comingSoon') }}</div>
        </v-card>
      </v-window-item>
    </v-window>

    <v-snackbar v-model="savedSnack" color="success" timeout="2000">
      {{ t('characters.saved') }}
    </v-snackbar>
  </v-container>
</template>

<script lang="ts" setup>
  import { computed, onMounted, reactive, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useRoute, useRouter } from 'vue-router'
  import BigFiveRadar from '@/components/BigFiveRadar.vue'
  import { ApiError } from '@/api/http'
  import type { BigFive, CharacterCreate, CharacterStatus } from '@/api/types'
  import { bandIndexOf, resolvePersonality } from '@/personality/mapping'
  import { useCharactersStore } from '@/stores/characters'

  const { t, te } = useI18n()
  const route = useRoute()
  const router = useRouter()
  const store = useCharactersStore()

  const TRAITS = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'] as const
  const LANGUAGES = [
    { title: 'English', value: 'en' },
    { title: '繁體中文', value: 'zh-Hant' },
    { title: '日本語', value: 'ja' },
  ]
  const STATUSES = computed(() =>
    ['draft', 'active', 'archived'].map(v => ({ title: t(`characters.status.${v}`), value: v })))

  const bandKey = (s: number) => {
    const schema = store.personalitySchema
    return schema ? schema.bands[bandIndexOf(s, schema.thresholds)] : 'moderate'
  }

  const defaultBigFive = (): BigFive => ({
    openness: 50, conscientiousness: 50, extraversion: 50, agreeableness: 50, neuroticism: 50,
  })

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

  const nameValid = computed(() => form.name.trim().length > 0)
  const splitCsv = (s: string) => s.split(',').map(x => x.trim()).filter(Boolean)

  // Computed locally from the cached spec — no request per slider move (docs/08 §3.2).
  const mapping = computed(() =>
    store.personalitySchema ? resolvePersonality(store.personalitySchema, form.big_five) : null)

  const directiveFor = (trait: string) =>
    mapping.value?.traits.find(e => e.trait === trait)?.directive ?? ''

  const radarData = computed(() =>
    TRAITS.map(k => ({ label: t(`characters.personality.traits.${k}`), value: form.big_five[k] })))

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
    if (!isNew.value) {
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
