<template>
  <v-container class="py-8">
    <div class="d-flex align-center mb-6">
      <div>
        <h1 class="text-h5 font-weight-medium">{{ t('scripts.title') }}</h1>
        <p class="text-body-2 text-medium-emphasis mb-0">{{ t('scripts.description') }}</p>
      </div>

      <v-spacer />

      <v-btn color="primary" :loading="creating" prepend-icon="mdi-plus" @click="createScript">
        {{ t('scripts.new') }}
      </v-btn>
    </div>

    <v-skeleton-loader v-if="loading" type="card, card" />

    <v-card
      v-else-if="scripts.length === 0"
      class="pa-8 text-center"
      color="surface-container"
      variant="flat"
    >
      <v-icon class="mb-3 text-medium-emphasis" icon="mdi-script-text-outline" size="40" />
      <div class="text-body-1 mb-1">{{ t('scripts.empty') }}</div>
      <div class="text-body-2 text-medium-emphasis">{{ t('scripts.emptyHint') }}</div>
    </v-card>

    <v-row v-else>
      <v-col
        v-for="s in scripts"
        :key="s.id"
        cols="12"
        md="4"
        sm="6"
      >
        <v-card class="h-100" :elevation="1" :to="`/scripts/${s.id}`">
          <v-card-item>
            <v-card-title>{{ s.title }}</v-card-title>

            <v-card-subtitle class="d-flex align-center ga-1">
              <v-chip :color="statusColor(s.status)" size="x-small" variant="tonal">
                {{ t(`scripts.status.${s.status}`) }}
              </v-chip>

              <span class="text-caption text-medium-emphasis">
                {{ t('scripts.lineCount', { n: s.line_count }) }}
              </span>
            </v-card-subtitle>
          </v-card-item>

          <v-card-text v-if="s.description" class="text-body-2 text-medium-emphasis text-truncate">
            {{ s.description }}
          </v-card-text>

          <v-card-actions @click.prevent.stop>
            <v-btn size="small" :to="`/scripts/${s.id}`" variant="text">{{ t('scripts.edit') }}</v-btn>
            <v-spacer />

            <v-btn
              :aria-label="t('scripts.duplicate')"
              icon="mdi-content-copy"
              size="small"
              variant="text"
              @click="duplicate(s.id)"
            />

            <v-btn
              :aria-label="t('scripts.archive')"
              icon="mdi-archive-outline"
              size="small"
              variant="text"
              @click="pendingArchive = s"
            />
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog max-width="420" :model-value="pendingArchive !== null" @update:model-value="pendingArchive = null">
      <v-card>
        <v-card-title class="text-h6">{{ t('scripts.archive') }}</v-card-title>

        <v-card-text>
          {{ t('scripts.archiveConfirm') }}
          <strong v-if="pendingArchive"> {{ pendingArchive.title }}</strong>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="pendingArchive = null">{{ t('common.action.cancel') }}</v-btn>
          <v-btn color="error" variant="flat" @click="confirmArchive">{{ t('scripts.archive') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar color="error" :model-value="!!error" :timeout="6000" @update:model-value="error = ''">
      {{ error }}
    </v-snackbar>
  </v-container>
</template>

<script lang="ts" setup>
  import type { Script, ScriptStatus } from '@/api/types'
  import { onMounted, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useRouter } from 'vue-router'
  import { ApiError } from '@/api/http'
  import { scriptsApi } from '@/api/scripts'

  const { t } = useI18n()
  const router = useRouter()

  const scripts = ref<Script[]>([])
  const loading = ref(true)
  const creating = ref(false)
  const error = ref('')
  const pendingArchive = ref<Script | null>(null)

  function statusColor (s: ScriptStatus) {
    if (s === 'ready') return 'success'
    if (s === 'archived') return 'on-surface-variant'
    return s === 'review' ? 'info' : 'warning'
  }

  function fail (e: unknown) {
    error.value = e instanceof ApiError ? e.message : t('error.generic')
  }

  async function load () {
    loading.value = true
    try {
      scripts.value = await scriptsApi.list()
    } catch (error_) {
      fail(error_)
    } finally {
      loading.value = false
    }
  }

  async function createScript () {
    creating.value = true
    try {
      const s = await scriptsApi.create({ title: t('scripts.untitled') })
      router.push(`/scripts/${s.id}`)
    } catch (error_) {
      fail(error_)
    } finally {
      creating.value = false
    }
  }

  async function duplicate (id: string) {
    try {
      await scriptsApi.duplicate(id)
      await load()
    } catch (error_) {
      fail(error_)
    }
  }

  async function confirmArchive () {
    if (!pendingArchive.value) return
    try {
      await scriptsApi.archive(pendingArchive.value.id)
      pendingArchive.value = null
      await load()
    } catch (error_) {
      fail(error_)
    }
  }

  onMounted(load)
</script>
