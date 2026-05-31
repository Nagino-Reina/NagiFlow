<template>
  <v-container class="py-8" style="max-width: 720px;">
    <div class="d-flex align-center mb-2">
      <v-icon icon="mdi-cog-outline" size="28" class="me-3 text-primary" />
      <h1 class="text-h5 font-weight-medium">{{ t('settings.title') }}</h1>
    </div>
    <p class="text-body-2 text-medium-emphasis mb-6">{{ t('settings.description') }}</p>

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
  </v-container>
</template>

<script lang="ts" setup>
  import { useI18n } from 'vue-i18n'
  import { SUPPORTED_LOCALES } from '@/plugins/i18n'
  import { useUiStore } from '@/stores/ui'

  const { t } = useI18n()
  const ui = useUiStore()
</script>
