<template>
  <PagePlaceholder
    :title="t('characters.title')"
    :description="t('characters.description')"
    icon="mdi-account-multiple-outline"
  />
</template>

<script lang="ts" setup>
  import { useI18n } from 'vue-i18n'
  import PagePlaceholder from '@/components/PagePlaceholder.vue'

  const { t } = useI18n()
</script>
