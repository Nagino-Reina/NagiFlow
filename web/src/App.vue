<template>
  <v-app>
    <router-view v-slot="{ Component, route }">
      <transition name="page" mode="out-in">
        <component :is="Component" :key="route.path" />
      </transition>
    </router-view>

    <!-- Global snackbar -->
    <v-snackbar
      v-model="app.snackbar.show"
      :color="app.snackbar.color"
      :timeout="app.snackbar.timeout"
      location="bottom right"
      rounded="xl"
    >
      <div class="d-flex align-center ga-2">
        <v-icon :icon="snackbarIcon" size="18" />
        <span>{{ app.snackbar.text }}</span>
      </div>
      <template #actions>
        <v-btn icon="mdi-close" size="small" variant="text" @click="app.snackbar.show = false" />
      </template>
    </v-snackbar>

    <!-- Global confirm dialog -->
    <v-dialog v-model="app.confirm.show" max-width="400" persistent>
      <v-card class="glass pa-2" rounded="xl">
        <v-card-title class="font-display text-h6 pa-4 pb-2">
          {{ app.confirm.title }}
        </v-card-title>
        <v-card-text class="text-medium-emphasis px-4 pb-4">
          {{ app.confirm.message }}
        </v-card-text>
        <v-card-actions class="px-4 pb-4 ga-2">
          <v-spacer />
          <v-btn variant="text" rounded="lg" @click="app.resolveConfirm(false)">Cancel</v-btn>
          <v-btn color="error" variant="tonal" rounded="lg" @click="app.resolveConfirm(true)">
            Confirm
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'

const app = useAppStore()

const snackbarIcon = computed(() => ({
  success: 'mdi-check-circle',
  error:   'mdi-alert-circle',
  warning: 'mdi-alert',
  info:    'mdi-information',
}[app.snackbar.color] ?? 'mdi-information'))
</script>