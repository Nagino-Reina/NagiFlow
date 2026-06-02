<template>
  <v-container class="py-8" style="max-width: 820px;">
    <div class="d-flex align-center mb-2">
      <v-icon icon="mdi-cog-outline" size="28" class="me-3 text-primary" />
      <h1 class="text-h5 font-weight-medium">{{ t('settings.title') }}</h1>
    </div>
    <p class="text-body-2 text-medium-emphasis mb-4">{{ t('settings.description') }}</p>

    <v-tabs v-model="tab" color="primary" class="mb-4">
      <v-tab value="general">{{ t('settings.tabs.general') }}</v-tab>
      <v-tab value="providers">{{ t('settings.tabs.providers') }}</v-tab>
      <v-tab value="modules">{{ t('settings.tabs.modules') }}</v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <!-- General -->
      <v-window-item value="general">
        <v-card variant="flat" color="surface-container" class="pa-4 mb-4">
          <div class="text-subtitle-2 mb-3">{{ t('settings.theme') }}</div>
          <v-btn-toggle
            :model-value="ui.theme"
            color="primary"
            density="comfortable"
            mandatory
            @update:model-value="ui.setTheme($event)"
          >
            <v-btn value="light" prepend-icon="mdi-weather-sunny">{{ t('settings.themeLight') }}</v-btn>
            <v-btn value="dark" prepend-icon="mdi-weather-night">{{ t('settings.themeDark') }}</v-btn>
          </v-btn-toggle>
        </v-card>

        <v-card variant="flat" color="surface-container" class="pa-4">
          <div class="text-subtitle-2 mb-3">{{ t('settings.language') }}</div>
          <v-btn-toggle
            :model-value="ui.locale"
            color="primary"
            density="comfortable"
            mandatory
            @update:model-value="ui.setLocale($event)"
          >
            <v-btn v-for="loc in SUPPORTED_LOCALES" :key="loc" :value="loc">
              {{ loc === 'zh-Hant' ? '繁體中文' : 'English' }}
            </v-btn>
          </v-btn-toggle>
        </v-card>

        <v-card variant="flat" color="surface-container" class="pa-4 mt-4">
          <div class="text-subtitle-2 mb-1">{{ t('settings.roleplay.title') }}</div>
          <p class="text-caption text-medium-emphasis mb-3">{{ t('settings.roleplay.hint') }}</p>
          <v-textarea
            v-model="rolePrompt"
            variant="outlined"
            rows="8"
            auto-grow
            :disabled="promptBusy"
            hide-details
            class="mb-3"
          />
          <div class="d-flex ga-2">
            <v-btn
              color="primary"
              :loading="promptBusy"
              :disabled="!rolePrompt.trim()"
              @click="savePrompt"
            >{{ t('common.action.save') }}</v-btn>
            <v-btn
              variant="text"
              :disabled="promptBusy || rolePrompt === rolePromptDefault"
              @click="resetPrompt"
            >{{ t('settings.roleplay.reset') }}</v-btn>
          </div>
        </v-card>
      </v-window-item>

      <!-- Providers & Models -->
      <v-window-item value="providers">
        <v-card variant="flat" color="surface-container" class="pa-4">
          <p class="text-body-2 text-medium-emphasis mb-4">{{ t('settings.providersNote') }}</p>
          <v-table density="comfortable">
            <thead>
              <tr>
                <th>{{ t('settings.capability') }}</th>
                <th>{{ t('settings.provider') }}</th>
                <th>{{ t('settings.model') }}</th>
                <th class="text-right">{{ t('settings.status') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in services" :key="s.capability">
                <td class="text-uppercase">{{ s.capability }}</td>
                <td>{{ s.name }}</td>
                <td class="text-medium-emphasis">{{ s.model || '—' }}</td>
                <td class="text-right">
                  <v-chip size="small" variant="tonal" :color="s.status === 'up' ? 'success' : 'error'">
                    {{ s.status }}
                  </v-chip>
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </v-window-item>

      <!-- Modules -->
      <v-window-item value="modules">
        <v-card variant="flat" color="surface-container" class="pa-8 text-center">
          <v-icon icon="mdi-puzzle-outline" size="40" class="mb-3 text-medium-emphasis" />
          <div class="text-body-1 mb-1">{{ t('modules.description') }}</div>
          <div class="text-body-2 text-medium-emphasis">{{ t('settings.modulesComingSoon') }}</div>
        </v-card>
      </v-window-item>
    </v-window>

    <v-snackbar :model-value="!!error" color="error" :timeout="6000" @update:model-value="error = ''">
      {{ error }}
    </v-snackbar>
    <v-snackbar :model-value="saved" color="success" :timeout="2500" @update:model-value="saved = false">
      {{ t('settings.saved') }}
    </v-snackbar>
  </v-container>
</template>

<script lang="ts" setup>
  import { onMounted, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { observabilityApi } from '@/api/observability'
  import { settingsApi } from '@/api/settings'
  import type { ServiceStatus } from '@/api/types'
  import { SUPPORTED_LOCALES } from '@/plugins/i18n'
  import { useUiStore } from '@/stores/ui'

  const { t } = useI18n()
  const ui = useUiStore()

  const tab = ref('general')
  const services = ref<ServiceStatus[]>([])
  const error = ref('')
  const saved = ref(false)

  const rolePrompt = ref('')
  const rolePromptDefault = ref('')
  const promptBusy = ref(false)

  async function loadProviders () {
    try {
      const res = await observabilityApi.services()
      services.value = res.services
    } catch (e) {
      error.value = (e as Error).message || t('error.generic')
    }
  }

  async function loadPrompt () {
    try {
      const r = await settingsApi.getRoleplayPrompt()
      rolePrompt.value = r.roleplay_prompt
      rolePromptDefault.value = r.default
    } catch (e) {
      error.value = (e as Error).message || t('error.generic')
    }
  }

  async function savePrompt () {
    promptBusy.value = true
    try {
      const r = await settingsApi.setRoleplayPrompt(rolePrompt.value)
      rolePrompt.value = r.roleplay_prompt
      saved.value = true
    } catch (e) {
      error.value = (e as Error).message || t('error.generic')
    } finally {
      promptBusy.value = false
    }
  }

  async function resetPrompt () {
    promptBusy.value = true
    try {
      const r = await settingsApi.resetRoleplayPrompt()
      rolePrompt.value = r.roleplay_prompt
      saved.value = true
    } catch (e) {
      error.value = (e as Error).message || t('error.generic')
    } finally {
      promptBusy.value = false
    }
  }

  onMounted(() => {
    loadProviders()
    loadPrompt()
  })
</script>
