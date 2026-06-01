<template>
  <v-container class="py-6" style="max-width: 960px;">
    <div class="d-flex align-center mb-4">
      <div>
        <h1 class="text-h5 font-weight-medium">{{ t('dashboard.title') }}</h1>
        <p class="text-body-2 text-medium-emphasis mb-0">{{ t('dashboard.description') }}</p>
      </div>
      <v-spacer />
      <v-btn
        variant="text"
        size="small"
        prepend-icon="mdi-refresh"
        :loading="loading"
        @click="load"
      >
        {{ t('dashboard.refresh') }}
      </v-btn>
    </div>

    <v-row>
      <!-- System resources -->
      <v-col cols="12" md="6">
        <v-card variant="outlined" class="h-100">
          <v-card-title class="text-subtitle-1">{{ t('dashboard.system') }}</v-card-title>
          <v-card-text v-if="resources">
            <div v-for="bar in resourceBars" :key="bar.label" class="mb-3">
              <div class="d-flex justify-space-between text-body-2 mb-1">
                <span>{{ bar.label }}</span>
                <span class="text-medium-emphasis">{{ bar.caption }}</span>
              </div>
              <v-progress-linear :model-value="bar.percent" height="8" rounded color="primary" />
            </div>
            <div
              v-for="gpu in resources.gpus"
              :key="gpu.name"
              class="d-flex justify-space-between text-body-2 mt-2"
            >
              <span>{{ gpu.name }}</span>
              <span class="text-medium-emphasis">
                {{ Math.round(gpu.utilization_percent) }}% ·
                {{ fmtBytes(gpu.memory_used) }} / {{ fmtBytes(gpu.memory_total) }}
              </span>
            </div>
          </v-card-text>
          <v-card-text v-else class="text-medium-emphasis">{{ t('dashboard.empty') }}</v-card-text>
        </v-card>
      </v-col>

      <!-- Service health -->
      <v-col cols="12" md="6">
        <v-card variant="outlined" class="h-100">
          <v-card-title class="text-subtitle-1">{{ t('dashboard.services') }}</v-card-title>
          <v-card-text>
            <div
              v-for="s in services"
              :key="s.capability"
              class="d-flex align-center justify-space-between mb-2"
            >
              <span class="text-body-2">{{ s.capability.toUpperCase() }} · {{ s.name }}</span>
              <v-chip
                size="small"
                variant="tonal"
                :color="s.status === 'up' ? 'success' : 'error'"
              >
                {{ s.status }}
              </v-chip>
            </div>
            <div v-if="services.length === 0" class="text-medium-emphasis">
              {{ t('dashboard.empty') }}
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Token usage -->
      <v-col cols="12">
        <v-card variant="outlined">
          <v-card-title class="text-subtitle-1">{{ t('dashboard.usage') }}</v-card-title>
          <v-card-text v-if="usage">
            <v-row class="mb-2">
              <v-col cols="6" sm="3">
                <div class="text-h6">{{ usage.totals.total_tokens.toLocaleString() }}</div>
                <div class="text-caption text-medium-emphasis">{{ t('dashboard.tokens') }}</div>
              </v-col>
              <v-col cols="6" sm="3">
                <div class="text-h6">{{ usage.totals.calls.toLocaleString() }}</div>
                <div class="text-caption text-medium-emphasis">{{ t('dashboard.calls') }}</div>
              </v-col>
              <v-col cols="6" sm="3">
                <div class="text-h6">{{ usage.totals.audio_seconds.toFixed(1) }}s</div>
                <div class="text-caption text-medium-emphasis">{{ t('dashboard.audio') }}</div>
              </v-col>
            </v-row>

            <div class="text-body-2 font-weight-medium mt-2 mb-1">{{ t('dashboard.byProvider') }}</div>
            <div
              v-for="g in usage.by_provider"
              :key="g.key ?? 'unknown'"
              class="d-flex justify-space-between text-body-2"
            >
              <span>{{ g.key || '—' }}</span>
              <span class="text-medium-emphasis">{{ g.total_tokens.toLocaleString() }} · {{ g.calls }}</span>
            </div>
          </v-card-text>
          <v-card-text v-else class="text-medium-emphasis">{{ t('dashboard.empty') }}</v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-snackbar :model-value="!!error" color="error" :timeout="6000" @update:model-value="error = ''">
      {{ error }}
    </v-snackbar>
  </v-container>
</template>

<script lang="ts" setup>
  import { computed, onMounted, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { observabilityApi } from '@/api/observability'
  import type { ServiceStatus, SystemResources, UsageSummary } from '@/api/types'

  const { t } = useI18n()

  const resources = ref<SystemResources | null>(null)
  const services = ref<ServiceStatus[]>([])
  const usage = ref<UsageSummary | null>(null)
  const loading = ref(false)
  const error = ref('')

  function fmtBytes (n: number): string {
    if (n >= 1024 ** 3) return `${(n / 1024 ** 3).toFixed(1)} GB`
    if (n >= 1024 ** 2) return `${(n / 1024 ** 2).toFixed(0)} MB`
    return `${(n / 1024).toFixed(0)} KB`
  }

  const resourceBars = computed(() => {
    const r = resources.value
    if (!r) return []
    return [
      { label: t('dashboard.cpu'), percent: r.cpu_percent, caption: `${Math.round(r.cpu_percent)}%` },
      {
        label: t('dashboard.memory'),
        percent: r.memory.percent,
        caption: `${fmtBytes(r.memory.used)} / ${fmtBytes(r.memory.total)}`,
      },
      {
        label: t('dashboard.disk'),
        percent: r.disk.percent,
        caption: `${fmtBytes(r.disk.free)} ${t('dashboard.free')}`,
      },
    ]
  })

  async function load () {
    loading.value = true
    try {
      const [res, svc, use] = await Promise.all([
        observabilityApi.resources(),
        observabilityApi.services(),
        observabilityApi.usageSummary(),
      ])
      resources.value = res
      services.value = svc.services
      usage.value = use
    } catch (e) {
      error.value = (e as Error).message || t('error.generic')
    } finally {
      loading.value = false
    }
  }

  onMounted(load)
</script>
