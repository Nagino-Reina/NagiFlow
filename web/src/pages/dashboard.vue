<template>
  <PagePlaceholder
    :title="t('dashboard.title')"
    :description="t('dashboard.description')"
    icon="mdi-view-dashboard-outline"
  />
</template>

<script lang="ts" setup>
  import { useI18n } from 'vue-i18n'
  import PagePlaceholder from '@/components/PagePlaceholder.vue'

  const { t } = useI18n()
</script>
