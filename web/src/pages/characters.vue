<template>
  <v-container class="py-8">
    <div class="d-flex align-center mb-6">
      <div>
        <h1 class="text-h5 font-weight-medium">{{ t('characters.title') }}</h1>
        <p class="text-body-2 text-medium-emphasis mb-0">{{ t('characters.description') }}</p>
      </div>

      <v-spacer />

      <v-btn color="primary" prepend-icon="mdi-plus" :to="'/characters/new'">
        {{ t('characters.new') }}
      </v-btn>
    </div>

    <v-skeleton-loader v-if="store.status === 'loading'" type="card, card, card" />

    <v-card
      v-else-if="store.items.length === 0"
      class="pa-8 text-center"
      color="surface-container"
      variant="flat"
    >
      <v-icon class="mb-3 text-medium-emphasis" icon="mdi-account-plus-outline" size="40" />
      <div class="text-body-1 mb-1">{{ t('characters.empty') }}</div>
      <div class="text-body-2 text-medium-emphasis">{{ t('characters.emptyHint') }}</div>
    </v-card>

    <v-row v-else>
      <v-col
        v-for="c in store.items"
        :key="c.id"
        cols="12"
        md="4"
        sm="6"
      >
        <v-card class="h-100" :elevation="1" :to="`/characters/${c.id}`">
          <v-card-item>
            <template #prepend>
              <v-avatar color="primary-container" icon="mdi-robot-outline" />
            </template>

            <v-card-title>{{ c.name || t('characters.untitled') }}</v-card-title>

            <v-card-subtitle class="d-flex align-center ga-1">
              <v-chip :color="statusColor(c.status)" size="x-small" variant="tonal">
                {{ t(`characters.status.${c.status}`) }}
              </v-chip>

              <v-chip v-if="c.guest_visible" color="secondary" size="x-small" variant="tonal">
                {{ t('characters.guestVisible') }}
              </v-chip>
            </v-card-subtitle>
          </v-card-item>

          <v-card-text v-if="c.description" class="text-body-2 text-medium-emphasis text-truncate">
            {{ c.description }}
          </v-card-text>

          <v-card-actions @click.prevent.stop>
            <v-btn size="small" :to="`/characters/${c.id}`" variant="text">
              {{ t('characters.edit') }}
            </v-btn>

            <v-spacer />

            <v-btn
              :aria-label="t('characters.duplicate')"
              icon="mdi-content-copy"
              size="small"
              variant="text"
              @click="duplicate(c.id)"
            />

            <v-btn
              :aria-label="t('characters.archive')"
              icon="mdi-archive-outline"
              size="small"
              variant="text"
              @click="pendingArchive = c"
            />
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog max-width="420" :model-value="pendingArchive !== null" @update:model-value="pendingArchive = null">
      <v-card>
        <v-card-title class="text-h6">{{ t('characters.archive') }}</v-card-title>

        <v-card-text>
          {{ t('characters.archiveConfirm') }}
          <strong v-if="pendingArchive"> {{ pendingArchive.name || t('characters.untitled') }}</strong>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="pendingArchive = null">{{ t('common.action.cancel') }}</v-btn>
          <v-btn color="error" variant="flat" @click="confirmArchive">{{ t('characters.archive') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script lang="ts" setup>
  import type { Character, CharacterStatus } from '@/api/types'
  import { onMounted, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useCharactersStore } from '@/stores/characters'

  const { t } = useI18n()
  const store = useCharactersStore()
  const pendingArchive = ref<Character | null>(null)

  function statusColor (s: CharacterStatus) {
    return s === 'active' ? 'success' : (s === 'archived' ? 'on-surface-variant' : 'warning')
  }

  async function duplicate (id: string) {
    await store.duplicate(id)
  }

  async function confirmArchive () {
    if (pendingArchive.value) {
      await store.archive(pendingArchive.value.id)
      pendingArchive.value = null
    }
  }

  onMounted(() => {
    store.load()
  })
</script>
