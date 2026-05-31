<template>
  <v-container class="py-12">
    <div class="mx-auto text-center" style="max-width: 640px;">
      <v-icon icon="mdi-robot-happy-outline" size="56" class="mb-4 text-primary" />
      <h1 class="text-h4 font-weight-bold mb-2">{{ t('landing.title') }}</h1>
      <p class="text-body-1 text-medium-emphasis mb-8">{{ t('landing.subtitle') }}</p>

      <v-card variant="tonal" color="surface-container" class="pa-8">
        <v-icon icon="mdi-chat-processing-outline" size="40" class="mb-3 text-medium-emphasis" />
        <div class="text-body-1 text-medium-emphasis mb-1">{{ t('landing.empty') }}</div>
        <div class="text-body-2 text-disabled">{{ t('landing.chatPlaceholder') }}</div>
      </v-card>
    </div>
  </v-container>
</template>

<script lang="ts" setup>
  import { useI18n } from 'vue-i18n'

  const { t } = useI18n()
</script>
