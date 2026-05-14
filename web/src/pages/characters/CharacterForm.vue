<template>
  <div>
    <v-form ref="formRef" @submit.prevent="submit" validate-on="submit">
      <v-row>
        <!-- Left column: Identity + Assets -->
        <v-col cols="12" md="7">

          <!-- Identity card -->
          <v-card class="glass mb-4" rounded="xl">
            <v-card-title class="d-flex align-center pa-5 pb-3 ga-2">
              <v-icon color="primary" size="20">mdi-account-circle-outline</v-icon>
              <span class="font-display text-h6">Identity</span>
            </v-card-title>
            <v-card-text class="pa-5 pt-2 d-flex flex-column ga-4">
              <v-text-field
                v-model="form.name"
                label="Character Name *"
                :rules="[rules.required]"
                prepend-inner-icon="mdi-account-outline"
              />
              <v-textarea
                v-model="form.description"
                label="Description"
                rows="3"
                auto-grow
                prepend-inner-icon="mdi-text"
                placeholder="A friendly Vtuber who loves games and anime…"
              />
              <v-textarea
                v-model="form.system_prompt"
                label="System Prompt"
                rows="4"
                auto-grow
                prepend-inner-icon="mdi-robot-outline"
                placeholder="You are {name}. Respond in a casual, upbeat tone…"
                hint="Overrides the auto-generated personality prompt."
                persistent-hint
              />
            </v-card-text>
          </v-card>

          <!-- LLM / TTS overrides -->
          <v-card class="glass mb-4" rounded="xl">
            <v-card-title class="d-flex align-center pa-5 pb-3 ga-2">
              <v-icon color="accent" size="20">mdi-tune</v-icon>
              <span class="font-display text-h6">Provider Overrides</span>
              <v-chip size="x-small" variant="tonal" class="ml-2">optional</v-chip>
            </v-card-title>
            <v-card-text class="pa-5 pt-2">
              <v-row dense>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="form.llm_provider"
                    :items="llmProviders"
                    label="LLM Provider"
                    clearable
                    prepend-inner-icon="mdi-brain"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.llm_model"
                    label="LLM Model"
                    clearable
                    prepend-inner-icon="mdi-chip"
                    placeholder="gpt-oss:20b"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="form.tts_provider"
                    :items="ttsProviders"
                    label="TTS Provider"
                    clearable
                    prepend-inner-icon="mdi-microphone"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model.number="form.tts_speaker_id"
                    label="TTS Speaker ID"
                    type="number"
                    clearable
                    prepend-inner-icon="mdi-account-voice"
                    placeholder="1"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="form.model_type"
                    :items="modelTypeOptions"
                    label="Avatar Model Type"
                    clearable
                    prepend-inner-icon="mdi-cube-outline"
                  />
                </v-col>
                <v-col cols="12" sm="6" class="d-flex align-center">
                  <v-switch
                    v-model="form.is_public"
                    color="primary"
                    label="Public character"
                    hide-details
                    inset
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- Asset uploads (edit mode only) -->
          <v-card v-if="isEdit" class="glass" rounded="xl">
            <v-card-title class="d-flex align-center pa-5 pb-3 ga-2">
              <v-icon color="secondary" size="20">mdi-file-upload-outline</v-icon>
              <span class="font-display text-h6">Assets</span>
            </v-card-title>
            <v-card-text class="pa-5 pt-2 d-flex flex-column ga-4">
              <AssetUpload
                label="Avatar Image"
                icon="mdi-image"
                accept="image/png,image/jpeg,image/webp,image/gif"
                color="primary"
                :current="charStore.current?.avatar_path"
                @upload="uploadAvatar"
              />
              <AssetUpload
                label="Voice Sample"
                icon="mdi-waveform"
                accept="audio/wav,audio/mpeg,audio/ogg"
                color="secondary"
                :current="charStore.current?.voice_sample_path"
                @upload="uploadVoice"
              />
              <div>
                <AssetUpload
                  label="Character Model (Live2D / 3D)"
                  icon="mdi-cube-scan"
                  accept=".zip,.model3.json,.vrm,.glb,.gltf"
                  color="accent"
                  :current="charStore.current?.model_path"
                  @upload="uploadModel"
                />
                <v-select
                  v-model="uploadModelType"
                  :items="modelTypeOptions"
                  label="Model Type"
                  density="compact"
                  class="mt-2"
                  style="max-width:200px;"
                />
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Right column: Big Five personality -->
        <v-col cols="12" md="5">
          <v-card class="glass" rounded="xl" style="position:sticky;top:80px;">
            <v-card-title class="d-flex align-center pa-5 pb-3 ga-2">
              <v-icon color="secondary" size="20">mdi-head-cog-outline</v-icon>
              <span class="font-display text-h6">Big Five Personality</span>
            </v-card-title>
            <v-card-text class="pa-5 pt-2">
              <!-- Radar preview -->
              <div class="radar-preview d-flex align-center justify-center mb-5">
                <PersonalityRadar :scores="form.personality.big_five" />
              </div>

              <!-- Sliders -->
              <div
                v-for="trait in big5Traits"
                :key="trait.key"
                class="mb-5"
              >
                <div class="d-flex align-center justify-space-between mb-2">
                  <div class="d-flex align-center ga-2">
                    <div class="trait-dot" :style="{ background: trait.color }" />
                    <span class="text-body-2 font-weight-medium">{{ trait.label }}</span>
                  </div>
                  <span class="text-caption font-mono" :style="{ color: trait.color }">
                    {{ form.personality.big_five[trait.key] }}
                  </span>
                </div>
                <v-slider
                  v-model="form.personality.big_five[trait.key]"
                  :min="0" :max="100" :step="1"
                  :color="trait.color"
                  track-color="rgba(255,255,255,0.08)"
                  thumb-size="16"
                  hide-details
                />
                <div class="d-flex justify-space-between mt-1">
                  <span class="text-caption text-medium-emphasis" style="font-size:10px;">{{ trait.low }}</span>
                  <span class="text-caption text-medium-emphasis" style="font-size:10px;">{{ trait.high }}</span>
                </div>
              </div>

              <!-- Custom JSON -->
              <v-expand-transition>
                <div>
                  <v-divider class="my-4" />
                  <div class="text-caption text-medium-emphasis mb-2">
                    Custom config (JSON key-value)
                  </div>
                  <v-textarea
                    v-model="customJson"
                    :rules="[rules.validJson]"
                    rows="3"
                    auto-grow
                    placeholder='{ "catchphrase": "Lets go~!" }'
                    style="font-family:var(--font-mono);font-size:12px;"
                  />
                </div>
              </v-expand-transition>
            </v-card-text>

            <v-card-actions class="pa-5 pt-0 ga-2">
              <v-btn variant="text" :to="{ name: 'characters' }">Cancel</v-btn>
              <v-spacer />
              <v-btn
                type="submit"
                color="primary"
                :loading="saving"
                class="glow-cyan px-6"
                prepend-icon="mdi-content-save-outline"
              >
                {{ isEdit ? 'Save Changes' : 'Create Character' }}
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>
    </v-form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, defineComponent, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCharactersStore } from '@/stores/characters'
import { useAppStore } from '@/stores/app'
import { charactersApi } from '@/api'
import PersonalityRadar from '@/components/character/PersonalityRadar.vue'
import AssetUpload from '@/components/character/AssetUpload.vue'

const route     = useRoute()
const router    = useRouter()
const charStore = useCharactersStore()
const app       = useAppStore()

const formRef       = ref(null)
const saving        = ref(false)
const customJson    = ref('{}')
const uploadModelType = ref('live2d')

const isEdit = computed(() => !!route.params.id)

const form = reactive({
  name:          '',
  description:   '',
  system_prompt: '',
  llm_provider:  null,
  llm_model:     null,
  tts_provider:  null,
  tts_speaker_id: null,
  model_type:    null,
  is_public:     false,
  personality: {
    big_five: {
      openness:          50,
      conscientiousness: 50,
      extraversion:      50,
      agreeableness:     50,
      neuroticism:       50,
    },
    custom: {},
  },
})

const big5Traits = [
  { key: 'openness',          label: 'Openness',          color: '#06B6D4', low: 'Conventional', high: 'Curious'    },
  { key: 'conscientiousness', label: 'Conscientiousness', color: '#8B5CF6', low: 'Spontaneous',  high: 'Organised'  },
  { key: 'extraversion',      label: 'Extraversion',      color: '#EC4899', low: 'Reserved',     high: 'Energetic'  },
  { key: 'agreeableness',     label: 'Agreeableness',     color: '#10B981', low: 'Direct',       high: 'Warm'       },
  { key: 'neuroticism',       label: 'Neuroticism',       color: '#F59E0B', low: 'Stable',       high: 'Sensitive'  },
]

const llmProviders   = ['ollama', 'openai_compat']
const ttsProviders   = ['voicevox']
const modelTypeOptions = [
  { title: 'Live2D', value: 'live2d' },
  { title: '3D',     value: '3d'     },
]

const rules = {
  required:  v => !!v || 'Required.',
  validJson: v => { try { JSON.parse(v || '{}'); return true } catch { return 'Invalid JSON.' } },
}

onMounted(async () => {
  if (isEdit.value) {
    await charStore.fetchOne(route.params.id)
    const c = charStore.current
    Object.assign(form, {
      name:           c.name,
      description:    c.description ?? '',
      system_prompt:  c.system_prompt ?? '',
      llm_provider:   c.llm_provider,
      llm_model:      c.llm_model,
      tts_provider:   c.tts_provider,
      tts_speaker_id: c.tts_speaker_id,
      model_type:     c.model_type,
      is_public:      c.is_public,
    })
    if (c.personality?.big_five) {
      Object.assign(form.personality.big_five, c.personality.big_five)
    }
    if (c.personality?.custom) {
      customJson.value = JSON.stringify(c.personality.custom, null, 2)
    }
  }
})

async function submit() {
  const { valid } = await formRef.value.validate()
  if (!valid) return
  saving.value = true
  try {
    let custom = {}
    try { custom = JSON.parse(customJson.value || '{}') } catch { /**/ }
    const payload = {
      ...form,
      personality: { big_five: form.personality.big_five, custom },
    }
    if (isEdit.value) {
      await charStore.update(route.params.id, payload)
      app.notify('Character updated!')
    } else {
      const created = await charStore.create(payload)
      app.notify('Character created!')
      router.push({ name: 'character-detail', params: { id: created.id } })
    }
  } catch (err) { app.notifyError(err) }
  finally { saving.value = false }
}

async function uploadAvatar(file) {
  try {
    await charactersApi.uploadAvatar(route.params.id, file)
    await charStore.fetchOne(route.params.id)
    app.notify('Avatar updated.')
  } catch (err) { app.notifyError(err) }
}

async function uploadVoice(file) {
  try {
    await charactersApi.uploadVoice(route.params.id, file)
    await charStore.fetchOne(route.params.id)
    app.notify('Voice sample updated.')
  } catch (err) { app.notifyError(err) }
}

async function uploadModel(file) {
  try {
    await charactersApi.uploadModel(route.params.id, file, uploadModelType.value)
    await charStore.fetchOne(route.params.id)
    app.notify('Model uploaded.')
  } catch (err) { app.notifyError(err) }
}
</script>

<style scoped>
.trait-dot { width:8px;height:8px;border-radius:50%;flex-shrink:0; }
.radar-preview { height: 180px; }
</style>