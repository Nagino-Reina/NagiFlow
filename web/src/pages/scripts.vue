<template>
  <PagePlaceholder
    :description="t('scripts.description')"
    icon="mdi-script-text-outline"
    :title="t('scripts.title')"
  />
</template>

<script lang="ts" setup>
  import { useI18n } from 'vue-i18n'
  import PagePlaceholder from '@/components/PagePlaceholder.vue'

  const { t } = useI18n()
</script>
