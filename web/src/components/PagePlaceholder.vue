<template>
  <v-container class="py-8">
    <div class="d-flex align-center mb-2">
      <v-icon :icon="icon" size="28" class="me-3 text-primary" />
      <h1 class="text-h5 font-weight-medium">{{ title }}</h1>
    </div>
    <p class="text-body-2 text-medium-emphasis mb-6">{{ description }}</p>

    <v-card variant="flat" color="surface-container" class="pa-8 text-center">
      <v-icon icon="mdi-progress-wrench" size="40" class="mb-3 text-medium-emphasis" />
      <div class="text-body-1 text-medium-emphasis">{{ t('common.state.comingSoon') }}</div>
    </v-card>
  </v-container>
</template>

<script lang="ts" setup>
  import { useI18n } from 'vue-i18n'

  defineProps<{
    title: string
    description: string
    icon: string
  }>()

  const { t } = useI18n()
</script>
