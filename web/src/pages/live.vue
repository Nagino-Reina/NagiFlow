<template>
  <PagePlaceholder
    :title="t('live.title')"
    :description="t('live.description')"
    icon="mdi-broadcast"
  />
</template>

<script lang="ts" setup>
  import { useI18n } from 'vue-i18n'
  import PagePlaceholder from '@/components/PagePlaceholder.vue'

  const { t } = useI18n()
</script>
