<template>
  <v-container class="py-12">
    <div class="mx-auto text-center" style="max-width: 640px;">
      <v-icon class="mb-4 text-primary" icon="mdi-robot-happy-outline" size="56" />
      <h1 class="text-h4 font-weight-bold mb-2">{{ t('landing.title') }}</h1>
      <p class="text-body-1 text-medium-emphasis mb-8">{{ t('landing.subtitle') }}</p>

      <v-card class="pa-8" color="surface-container" variant="flat">
        <v-icon class="mb-3 text-medium-emphasis" icon="mdi-chat-processing-outline" size="40" />
        <div class="text-body-1 text-medium-emphasis mb-1">{{ t('landing.empty') }}</div>
        <div class="text-body-2 text-medium-emphasis">{{ t('landing.chatPlaceholder') }}</div>
      </v-card>
    </div>
  </v-container>
</template>

<script lang="ts" setup>
  import { useI18n } from 'vue-i18n'

  const { t } = useI18n()
</script>
