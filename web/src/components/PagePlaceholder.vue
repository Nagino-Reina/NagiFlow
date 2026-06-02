<template>
  <v-container class="py-8">
    <div class="d-flex align-center mb-2">
      <v-icon class="me-3 text-primary" :icon="icon" size="28" />
      <h1 class="text-h5 font-weight-medium">{{ title }}</h1>
    </div>

    <p class="text-body-2 text-medium-emphasis mb-6">{{ description }}</p>

    <v-card class="pa-8 text-center" color="surface-container" variant="flat">
      <v-icon class="mb-3 text-medium-emphasis" icon="mdi-progress-wrench" size="40" />
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
