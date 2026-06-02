<template>
  <v-container class="py-8" style="max-width: 820px;">
    <div class="d-flex align-center mb-2">
      <v-icon class="me-3 text-primary" icon="mdi-cog-outline" size="28" />
      <h1 class="text-h5 font-weight-medium">{{ t('settings.title') }}</h1>
    </div>

    <p class="text-body-2 text-medium-emphasis mb-4">{{ t('settings.description') }}</p>

    <v-tabs v-model="tab" class="mb-4" color="primary">
      <v-tab value="general">{{ t('settings.tabs.general') }}</v-tab>
      <v-tab value="providers">{{ t('settings.tabs.providers') }}</v-tab>
      <v-tab value="modules">{{ t('settings.tabs.modules') }}</v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <!-- General -->
      <v-window-item value="general">
        <v-card class="pa-4 mb-4" color="surface-container" variant="flat">
          <div class="text-subtitle-2 mb-3">{{ t('settings.theme') }}</div>

          <v-btn-toggle
            color="primary"
            density="comfortable"
            mandatory
            :model-value="ui.theme"
            @update:model-value="ui.setTheme($event)"
          >
            <v-btn prepend-icon="mdi-weather-sunny" value="light">{{ t('settings.themeLight') }}</v-btn>
            <v-btn prepend-icon="mdi-weather-night" value="dark">{{ t('settings.themeDark') }}</v-btn>
          </v-btn-toggle>
        </v-card>

        <v-card class="pa-4" color="surface-container" variant="flat">
          <div class="text-subtitle-2 mb-3">{{ t('settings.language') }}</div>

          <v-btn-toggle
            color="primary"
            density="comfortable"
            mandatory
            :model-value="ui.locale"
            @update:model-value="ui.setLocale($event)"
          >
            <v-btn v-for="loc in SUPPORTED_LOCALES" :key="loc" :value="loc">
              {{ loc === 'zh-Hant' ? '繁體中文' : 'English' }}
            </v-btn>
          </v-btn-toggle>
        </v-card>

        <v-card class="pa-4 mt-4" color="surface-container" variant="flat">
          <div class="text-subtitle-2 mb-1">{{ t('settings.roleplay.title') }}</div>
          <p class="text-caption text-medium-emphasis mb-3">{{ t('settings.roleplay.hint') }}</p>

          <v-textarea
            v-model="rolePrompt"
            auto-grow
            class="mb-3"
            :disabled="promptBusy"
            hide-details
            rows="8"
            variant="outlined"
          />

          <div class="d-flex ga-2">
            <v-btn
              color="primary"
              :disabled="!rolePrompt.trim()"
              :loading="promptBusy"
              @click="savePrompt"
            >{{ t('common.action.save') }}</v-btn>

            <v-btn
              :disabled="promptBusy || rolePrompt === rolePromptDefault"
              variant="text"
              @click="resetPrompt"
            >{{ t('settings.roleplay.reset') }}</v-btn>
          </div>
        </v-card>
      </v-window-item>

      <!-- Providers & Models -->
      <v-window-item value="providers">
        <v-card class="pa-4" color="surface-container" variant="flat">
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
                  <v-chip :color="s.status === 'up' ? 'success' : 'error'" size="small" variant="tonal">
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
        <v-card class="pa-8 text-center" color="surface-container" variant="flat">
          <v-icon class="mb-3 text-medium-emphasis" icon="mdi-puzzle-outline" size="40" />
          <div class="text-body-1 mb-1">{{ t('modules.description') }}</div>
          <div class="text-body-2 text-medium-emphasis">{{ t('settings.modulesComingSoon') }}</div>
        </v-card>
      </v-window-item>
    </v-window>

    <v-snackbar color="error" :model-value="!!error" :timeout="6000" @update:model-value="error = ''">
      {{ error }}
    </v-snackbar>

    <v-snackbar color="success" :model-value="saved" :timeout="2500" @update:model-value="saved = false">
      {{ t('settings.saved') }}
    </v-snackbar>
  </v-container>
</template>

<script lang="ts" setup>
  import type { ServiceStatus } from '@/api/types'
  import { onMounted, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { observabilityApi } from '@/api/observability'
  import { settingsApi } from '@/api/settings'
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
    } catch (error_) {
      error.value = (error_ as Error).message || t('error.generic')
    }
  }

  async function loadPrompt () {
    try {
      const r = await settingsApi.getRoleplayPrompt()
      rolePrompt.value = r.roleplay_prompt
      rolePromptDefault.value = r.default
    } catch (error_) {
      error.value = (error_ as Error).message || t('error.generic')
    }
  }

  async function savePrompt () {
    promptBusy.value = true
    try {
      const r = await settingsApi.setRoleplayPrompt(rolePrompt.value)
      rolePrompt.value = r.roleplay_prompt
      saved.value = true
    } catch (error_) {
      error.value = (error_ as Error).message || t('error.generic')
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
    } catch (error_) {
      error.value = (error_ as Error).message || t('error.generic')
    } finally {
      promptBusy.value = false
    }
  }

  onMounted(() => {
    loadProviders()
    loadPrompt()
  })
</script>
