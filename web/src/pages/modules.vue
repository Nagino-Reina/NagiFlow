<template>
  <PagePlaceholder
    :title="t('modules.title')"
    :description="t('modules.description')"
    icon="mdi-puzzle-outline"
  />
</template>

<script lang="ts" setup>
  import { useI18n } from 'vue-i18n'
  import PagePlaceholder from '@/components/PagePlaceholder.vue'

  const { t } = useI18n()
</script>
