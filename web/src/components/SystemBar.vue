<template>
  <v-footer app order="2" height="34" color="surface-container-low" class="pa-0 system-bar">
    <!-- Expandable detail panel (overlays upward; does not shift page layout) -->
    <v-expand-transition>
      <v-sheet v-if="expanded" class="system-bar__panel" color="surface-container-low" elevation="6">
        <v-container class="py-3" style="max-width: 1100px;">
          <v-row dense>
            <v-col cols="12" md="4">
              <div class="text-subtitle-2 mb-2">{{ t('dashboard.system') }}</div>
              <div v-if="resources">
                <div v-for="bar in resourceBars" :key="bar.label" class="mb-2">
                  <div class="d-flex justify-space-between text-caption mb-1">
                    <span>{{ bar.label }}</span>
                    <span class="text-medium-emphasis">{{ bar.caption }}</span>
                  </div>
                  <v-progress-linear :model-value="bar.percent" height="6" rounded color="primary" />
                </div>
                <div
                  v-for="gpu in resources.gpus"
                  :key="gpu.name"
                  class="d-flex justify-space-between text-caption mt-1"
                >
                  <span>{{ gpu.name }}</span>
                  <span class="text-medium-emphasis">
                    {{ Math.round(gpu.utilization_percent) }}% ·
                    {{ fmtBytes(gpu.memory_used) }} / {{ fmtBytes(gpu.memory_total) }}
                  </span>
                </div>
              </div>
              <div v-else class="text-caption text-medium-emphasis">{{ t('dashboard.empty') }}</div>
            </v-col>

            <v-col cols="12" md="4">
              <div class="text-subtitle-2 mb-2">{{ t('dashboard.services') }}</div>
              <div
                v-for="s in services"
                :key="s.capability"
                class="d-flex align-center justify-space-between mb-1"
              >
                <span class="text-caption">{{ s.capability.toUpperCase() }} · {{ s.name }}{{ s.model ? ` (${s.model})` : '' }}</span>
                <v-chip size="x-small" variant="tonal" :color="s.status === 'up' ? 'success' : 'error'">
                  {{ s.status }}
                </v-chip>
              </div>
              <div v-if="services.length === 0" class="text-caption text-medium-emphasis">
                {{ t('dashboard.empty') }}
              </div>
            </v-col>

            <v-col cols="12" md="4">
              <div class="text-subtitle-2 mb-2">{{ t('dashboard.usage') }}</div>
              <div v-if="usage">
                <div class="d-flex justify-space-between text-caption">
                  <span>{{ t('dashboard.tokens') }}</span>
                  <span class="text-medium-emphasis">{{ usage.totals.total_tokens.toLocaleString() }}</span>
                </div>
                <div class="d-flex justify-space-between text-caption">
                  <span>{{ t('dashboard.calls') }}</span>
                  <span class="text-medium-emphasis">{{ usage.totals.calls.toLocaleString() }}</span>
                </div>
                <div class="d-flex justify-space-between text-caption mb-1">
                  <span>{{ t('dashboard.audio') }}</span>
                  <span class="text-medium-emphasis">{{ usage.totals.audio_seconds.toFixed(1) }}s</span>
                </div>
                <div class="text-caption font-weight-medium mt-1">{{ t('dashboard.byProvider') }}</div>
                <div
                  v-for="g in usage.by_provider"
                  :key="g.key ?? 'unknown'"
                  class="d-flex justify-space-between text-caption"
                >
                  <span>{{ g.key || '—' }}</span>
                  <span class="text-medium-emphasis">{{ g.total_tokens.toLocaleString() }} · {{ g.calls }}</span>
                </div>
              </div>
              <div v-else class="text-caption text-medium-emphasis">{{ t('dashboard.empty') }}</div>
            </v-col>
          </v-row>
        </v-container>
      </v-sheet>
    </v-expand-transition>

    <!-- Collapsed always-on bar -->
    <div
      class="d-flex align-center w-100 px-3 text-caption system-bar__strip"
      role="button"
      :aria-label="t('systemBar.toggle')"
      @click="expanded = !expanded"
    >
      <span v-for="s in services" :key="s.capability" class="d-flex align-center mr-3">
        <v-icon :color="s.status === 'up' ? 'success' : 'error'" icon="mdi-circle" size="8" class="mr-1" />
        {{ s.capability.toUpperCase() }}
      </span>

      <v-divider vertical class="mx-2 my-1" />
      <span class="mr-3">{{ t('dashboard.cpu') }} {{ cpuPct }}%</span>
      <span :class="gpu ? 'mr-3' : ''">{{ t('dashboard.memory') }} {{ memPct }}%</span>
      <span v-if="gpu">{{ t('dashboard.gpu') }} {{ gpuPct }}%</span>

      <v-spacer />
      <v-icon icon="mdi-database-outline" size="13" class="mr-1" />
      <span class="mr-2">{{ tokenTotal }}</span>
      <v-icon :icon="expanded ? 'mdi-chevron-down' : 'mdi-chevron-up'" size="16" />
    </div>
  </v-footer>
</template>

<script lang="ts" setup>
  import { computed, onMounted, onUnmounted, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { observabilityApi } from '@/api/observability'
  import type { ServiceStatus, SystemResources, UsageSummary } from '@/api/types'

  const POLL_MS = 5000

  const { t } = useI18n()

  const resources = ref<SystemResources | null>(null)
  const services = ref<ServiceStatus[]>([])
  const usage = ref<UsageSummary | null>(null)
  const expanded = ref(false)
  let timer: number | undefined

  function fmtBytes (n: number): string {
    if (n >= 1024 ** 3) return `${(n / 1024 ** 3).toFixed(1)} GB`
    if (n >= 1024 ** 2) return `${(n / 1024 ** 2).toFixed(0)} MB`
    return `${(n / 1024).toFixed(0)} KB`
  }
  function fmtTokens (n: number): string {
    if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
    return String(n)
  }

  const cpuPct = computed(() => Math.round(resources.value?.cpu_percent ?? 0))
  const memPct = computed(() => Math.round(resources.value?.memory.percent ?? 0))
  const gpu = computed(() => resources.value?.gpus[0] ?? null)
  const gpuPct = computed(() => Math.round(gpu.value?.utilization_percent ?? 0))
  const tokenTotal = computed(() => fmtTokens(usage.value?.totals.total_tokens ?? 0))

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
    // Silent poll: keep the last good values on a transient error rather than flashing the bar.
    try {
      const [res, svc, use] = await Promise.all([
        observabilityApi.resources(),
        observabilityApi.services(),
        observabilityApi.usageSummary(),
      ])
      resources.value = res
      services.value = svc.services
      usage.value = use
    } catch {
      // ignore — next tick retries
    }
  }

  onMounted(() => {
    load()
    timer = window.setInterval(load, POLL_MS)
  })
  onUnmounted(() => {
    if (timer) clearInterval(timer)
  })
</script>

<style scoped>
  .system-bar {
    flex-direction: column;
    align-items: stretch;
    padding: 0;
  }
  .system-bar__strip {
    height: 34px;
    cursor: pointer;
  }
  .system-bar__panel {
    position: absolute;
    bottom: 100%;
    left: 0;
    right: 0;
    max-height: 50vh;
    overflow-y: auto;
    border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  }
</style>
