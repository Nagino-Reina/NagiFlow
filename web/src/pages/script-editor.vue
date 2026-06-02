<template>
  <v-container class="py-6" style="max-width: 960px;">
    <div class="d-flex align-center mb-4 ga-2">
      <v-btn :aria-label="t('common.action.back')" icon="mdi-arrow-left" :to="'/scripts'" variant="text" />
      <h1 class="text-h6 font-weight-medium flex-grow-1">{{ form.title || t('scripts.untitled') }}</h1>

      <v-btn :loading="validating" prepend-icon="mdi-check-decagram" variant="tonal" @click="runValidate">
        {{ t('scripts.editor.validate') }}
      </v-btn>
    </div>

    <!-- Script meta -->
    <v-card class="pa-4 mb-4" color="surface-container" variant="flat">
      <v-row dense>
        <v-col cols="12" sm="8">
          <v-text-field v-model="form.title" density="comfortable" :label="t('scripts.editor.fields.title')" @change="saveMeta" />
        </v-col>

        <v-col cols="12" sm="4">
          <v-select
            v-model="form.status"
            density="comfortable"
            :items="STATUSES"
            :label="t('scripts.editor.fields.status')"
            @update:model-value="saveMeta"
          />
        </v-col>

        <v-col cols="12" sm="8">
          <v-text-field v-model="form.description" density="comfortable" :label="t('scripts.editor.fields.description')" @change="saveMeta" />
        </v-col>

        <v-col cols="12" sm="4">
          <v-select
            v-model="form.language"
            density="comfortable"
            :items="LANGUAGES"
            :label="t('scripts.editor.fields.language')"
            @update:model-value="saveMeta"
          />
        </v-col>
      </v-row>
    </v-card>

    <!-- Validation issues -->
    <v-alert
      v-if="issues.length > 0"
      class="mb-4"
      density="comfortable"
      :type="issues.some(i => i.severity === 'error') ? 'error' : 'warning'"
      variant="tonal"
    >
      <ul class="ms-2">
        <li v-for="(i, idx) in issues" :key="idx" class="text-body-2">{{ i.message }}</li>
      </ul>
    </v-alert>

    <v-alert
      v-else-if="validated"
      class="mb-4"
      density="comfortable"
      type="success"
      variant="tonal"
    >
      {{ t('scripts.editor.noIssues') }}
    </v-alert>

    <!-- Lines -->
    <v-card v-for="(line, idx) in lines" :key="line.id" class="mb-2 pa-3" variant="outlined">
      <div class="d-flex ga-2">
        <div class="d-flex flex-column">
          <v-btn
            :aria-label="t('scripts.editor.moveUp')"
            :disabled="idx === 0"
            icon="mdi-chevron-up"
            size="x-small"
            variant="text"
            @click="move(idx, -1)"
          />

          <span class="text-caption text-center text-medium-emphasis">{{ idx + 1 }}</span>

          <v-btn
            :aria-label="t('scripts.editor.moveDown')"
            :disabled="idx === lines.length - 1"
            icon="mdi-chevron-down"
            size="x-small"
            variant="text"
            @click="move(idx, 1)"
          />
        </div>

        <div class="flex-grow-1">
          <!-- Row 1: speaker · style · rate · pause -->
          <div class="d-flex ga-2 mb-2 align-center flex-wrap">
            <v-select
              v-model="line.character_id"
              density="compact"
              hide-details
              :items="speakerItems"
              :label="t('scripts.editor.speaker')"
              style="min-width: 160px;"
              @update:model-value="saveLine(line, { character_id: line.character_id })"
            />

            <v-text-field
              v-model.number="line.speech_rate"
              density="compact"
              hide-details
              :label="t('scripts.editor.speechRate')"
              max="2"
              min="0.5"
              step="0.1"
              style="max-width: 96px;"
              type="number"
              @change="saveLine(line, { speech_rate: line.speech_rate })"
            />

            <v-text-field
              v-model.number="pauseSec[line.id]"
              density="compact"
              hide-details
              :label="t('scripts.editor.pause')"
              min="0"
              step="0.1"
              style="max-width: 120px;"
              type="number"
              @change="savePause(line)"
            />

            <v-spacer />

            <v-btn
              :aria-label="t('scripts.editor.delete')"
              icon="mdi-delete-outline"
              size="small"
              variant="text"
              @click="removeLine(idx)"
            />
          </div>

          <!-- Row 2: style -->
          <v-text-field
            v-model="line.style"
            class="mb-2"
            density="compact"
            hide-details
            :label="t('scripts.editor.style')"
            :placeholder="t('scripts.editor.styleHint')"
            @change="saveLine(line, { style: line.style })"
          />

          <!-- Row 3: line text -->
          <v-textarea
            v-model="line.text"
            auto-grow
            class="mb-2"
            density="compact"
            hide-details
            :placeholder="t('scripts.editor.textPlaceholder')"
            rows="2"
            @change="saveLine(line, { text: line.text })"
          />

          <!-- Row 4: per-line audio -->
          <div class="d-flex ga-1 align-center">
            <v-btn
              :disabled="!line.character_id || !line.text.trim()"
              :loading="generating[line.id]"
              prepend-icon="mdi-waveform"
              size="small"
              variant="tonal"
              @click="generateAudio(line)"
            >
              {{ t('scripts.editor.generate') }}
            </v-btn>

            <LineWaveform v-if="audioUrl[line.id]" :url="audioUrl[line.id]" />

            <span v-else-if="!line.character_id" class="text-caption text-medium-emphasis ms-1">
              {{ t('scripts.editor.assignSpeaker') }}
            </span>
          </div>
        </div>
      </div>
    </v-card>

    <v-btn
      class="mt-2"
      :loading="addingLine"
      prepend-icon="mdi-plus"
      variant="tonal"
      @click="addLine"
    >
      {{ t('scripts.editor.addLine') }}
    </v-btn>

    <v-snackbar color="error" :model-value="!!error" :timeout="6000" @update:model-value="error = ''">
      {{ error }}
    </v-snackbar>
  </v-container>
</template>

<script lang="ts" setup>
  import type { ScriptLine, ScriptStatus, ValidationIssue } from '@/api/types'
  import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useRoute } from 'vue-router'
  import { ApiError } from '@/api/http'
  import { scriptsApi } from '@/api/scripts'
  import LineWaveform from '@/components/LineWaveform.vue'
  import { useCharactersStore } from '@/stores/characters'

  const { t } = useI18n()
  const route = useRoute()
  const characters = useCharactersStore()

  const scriptId = route.params.id as string
  const lines = ref<ScriptLine[]>([])
  const error = ref('')
  const addingLine = ref(false)
  const validating = ref(false)
  const validated = ref(false)
  const issues = ref<ValidationIssue[]>([])

  // Pause is edited in seconds but stored as milliseconds, keyed by line id.
  const pauseSec = reactive<Record<string, number | null>>({})
  // Per-line synthesized audio: object URLs, players, and play/generate state.
  const audioUrl = reactive<Record<string, string>>({})
  const generating = reactive<Record<string, boolean>>({})

  const form = reactive({
    title: '',
    description: '',
    language: 'en',
    status: 'draft' as ScriptStatus,
  })

  const STATUSES = computed(() =>
    (['draft', 'review', 'ready', 'archived'] as const).map(v => ({ title: t(`scripts.status.${v}`), value: v })))
  const LANGUAGES = [
    { title: 'English', value: 'en' },
    { title: '繁體中文', value: 'zh-Hant' },
    { title: '日本語', value: 'ja' },
  ]
  const speakerItems = computed(() =>
    characters.items.filter(c => c.status !== 'archived').map(c => ({ title: c.name, value: c.id })))

  function fail (e: unknown) {
    error.value = e instanceof ApiError ? e.message : t('error.generic')
  }

  async function saveMeta () {
    try {
      await scriptsApi.update(scriptId, {
        title: form.title,
        description: form.description,
        language: form.language,
        status: form.status,
      })
    } catch (error_) {
      fail(error_)
    }
  }

  async function saveLine (line: ScriptLine, patch: Record<string, unknown>) {
    try {
      await scriptsApi.updateLine(scriptId, line.id, patch)
    } catch (error_) {
      fail(error_)
    }
  }

  function setPauseSec (lineId: string, ms: number | null) {
    pauseSec[lineId] = ms == null ? null : Math.round(ms / 100) / 10
  }

  async function savePause (line: ScriptLine) {
    const sec = pauseSec[line.id]
    const ms = sec == null || Number.isNaN(sec) ? null : Math.round(sec * 1000)
    await saveLine(line, { pause_after_ms: ms })
  }

  async function generateAudio (line: ScriptLine) {
    if (!line.character_id || !line.text.trim()) return
    generating[line.id] = true
    try {
      // Synthesized server-side from the line's speaker (voice + personality) + its direction.
      const url = await scriptsApi.previewLine(scriptId, line.id)
      if (audioUrl[line.id]) URL.revokeObjectURL(audioUrl[line.id])
      audioUrl[line.id] = url
    } catch (error_) {
      fail(error_)
    } finally {
      generating[line.id] = false
    }
  }

  async function addLine () {
    addingLine.value = true
    try {
      const line = await scriptsApi.addLine(scriptId, {})
      setPauseSec(line.id, line.pause_after_ms)
      lines.value.push(line)
    } catch (error_) {
      fail(error_)
    } finally {
      addingLine.value = false
    }
  }

  async function removeLine (idx: number) {
    const line = lines.value[idx]
    try {
      await scriptsApi.deleteLine(scriptId, line.id)
      if (audioUrl[line.id]) URL.revokeObjectURL(audioUrl[line.id])
      lines.value.splice(idx, 1)
    } catch (error_) {
      fail(error_)
    }
  }

  async function move (idx: number, delta: number) {
    const target = idx + delta
    if (target < 0 || target >= lines.value.length) return
    const next = [...lines.value]
    ;[next[idx], next[target]] = [next[target], next[idx]]
    lines.value = next
    try {
      await scriptsApi.reorder(scriptId, next.map(l => l.id))
    } catch (error_) {
      fail(error_)
    }
  }

  async function runValidate () {
    validating.value = true
    try {
      issues.value = (await scriptsApi.validate(scriptId)).issues
      validated.value = true
    } catch (error_) {
      fail(error_)
    } finally {
      validating.value = false
    }
  }

  onMounted(async () => {
    if (characters.items.length === 0) characters.load()
    try {
      const script = await scriptsApi.get(scriptId)
      form.title = script.title
      form.description = script.description
      form.language = script.language
      form.status = script.status
      lines.value = await scriptsApi.lines(scriptId)
      for (const line of lines.value) setPauseSec(line.id, line.pause_after_ms)
    } catch (error_) {
      fail(error_)
    }
  })

  onUnmounted(() => {
    for (const url of Object.values(audioUrl)) URL.revokeObjectURL(url)
  })
</script>
