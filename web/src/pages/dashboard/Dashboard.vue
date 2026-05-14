<template>
  <div>
    <!-- Welcome banner -->
    <div class="welcome-banner glass-bright rounded-xl pa-6 mb-6 d-flex align-center ga-4">
      <div class="hero-avatar d-flex align-center justify-center">
        <v-icon size="36" color="primary">mdi-star-four-points</v-icon>
      </div>
      <div>
        <div class="font-display text-h5 font-weight-bold">
          Welcome back, <span class="gradient-text">{{ auth.user?.username }}</span> 👋
        </div>
        <div class="text-body-2 text-medium-emphasis mt-1">
          Your AI Vtuber studio is ready. Start a conversation or build a new character.
        </div>
      </div>
      <v-spacer />
      <v-btn color="primary" prepend-icon="mdi-plus" :to="{ name: 'character-create' }" class="glow-cyan d-none d-md-flex">
        New Character
      </v-btn>
    </div>

    <!-- Stat cards -->
    <v-row class="mb-6" dense>
      <v-col v-for="stat in stats" :key="stat.label" cols="6" md="3">
        <v-card class="glass stat-card pa-4" rounded="xl" height="110">
          <div class="d-flex align-center justify-space-between mb-3">
            <div
              class="stat-icon d-flex align-center justify-center rounded-lg"
              :style="{ background: stat.iconBg }"
            >
              <v-icon :icon="stat.icon" :color="stat.iconColor" size="20" />
            </div>
            <v-chip
              size="x-small"
              variant="flat"
              :color="stat.trend > 0 ? 'success' : 'error'"
              class="font-mono"
            >
              {{ stat.trend > 0 ? '+' : '' }}{{ stat.trend }}
            </v-chip>
          </div>
          <div class="text-h5 font-display font-weight-bold">{{ stat.value }}</div>
          <div class="text-caption text-medium-emphasis">{{ stat.label }}</div>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <!-- Characters quick-access -->
      <v-col cols="12" md="7">
        <v-card class="glass" rounded="xl">
          <v-card-title class="d-flex align-center pa-5 pb-3 ga-2">
            <v-icon color="primary" size="20">mdi-account-star-outline</v-icon>
            <span class="font-display text-h6">Your Characters</span>
            <v-spacer />
            <v-btn variant="text" size="small" :to="{ name: 'characters' }" append-icon="mdi-arrow-right">
              View all
            </v-btn>
          </v-card-title>

          <v-card-text class="pa-4 pt-0">
            <div v-if="charStore.loading" class="d-flex ga-3">
              <v-skeleton-loader
                v-for="n in 3" :key="n"
                type="list-item-avatar"
                class="flex-1"
                color="transparent"
              />
            </div>
            <div v-else-if="charStore.list.length === 0" class="text-center py-8 text-medium-emphasis">
              <v-icon size="48" class="mb-3 opacity-30">mdi-account-star-outline</v-icon>
              <div>No characters yet.</div>
              <v-btn class="mt-3" color="primary" variant="tonal" size="small" :to="{ name: 'character-create' }">
                Create your first
              </v-btn>
            </div>
            <div v-else class="d-flex flex-column ga-2">
              <div
                v-for="char in charStore.list.slice(0,5)"
                :key="char.id"
                class="char-row d-flex align-center ga-3 pa-3 rounded-xl"
                @click="$router.push({ name: 'character-detail', params: { id: char.id } })"
              >
                <v-avatar size="40" color="surface-2">
                  <v-img v-if="char.avatar_path" :src="`/api/v1/audio/${char.avatar_path}`" />
                  <span v-else class="font-display font-weight-bold text-primary" style="font-size:16px;">
                    {{ char.name.charAt(0) }}
                  </span>
                </v-avatar>
                <div class="flex-1 overflow-hidden">
                  <div class="text-body-1 font-weight-medium text-truncate">{{ char.name }}</div>
                  <div class="text-caption text-medium-emphasis text-truncate">{{ char.description ?? 'No description' }}</div>
                </div>
                <v-chip
                  v-if="char.model_type"
                  size="x-small"
                  :class="char.model_type === 'live2d' ? 'chip-cyan' : 'chip-violet'"
                >
                  {{ char.model_type }}
                </v-chip>
                <v-btn
                  icon="mdi-chat-outline"
                  size="x-small"
                  variant="tonal"
                  color="primary"
                  @click.stop="$router.push({ name: 'character-chat', params: { id: char.id } })"
                />
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Quick actions + Health -->
      <v-col cols="12" md="5">
        <v-card class="glass mb-4" rounded="xl">
          <v-card-title class="d-flex align-center pa-5 pb-3 ga-2">
            <v-icon color="secondary" size="20">mdi-lightning-bolt</v-icon>
            <span class="font-display text-h6">Quick Actions</span>
          </v-card-title>
          <v-card-text class="pa-4 pt-0 d-flex flex-column ga-2">
            <v-btn
              v-for="action in quickActions"
              :key="action.label"
              :to="action.to"
              :color="action.color"
              variant="tonal"
              class="justify-start"
              :prepend-icon="action.icon"
              rounded="lg"
            >
              {{ action.label }}
            </v-btn>
          </v-card-text>
        </v-card>

        <!-- System health -->
        <v-card class="glass" rounded="xl">
          <v-card-title class="d-flex align-center pa-5 pb-3 ga-2">
            <v-icon color="success" size="20">mdi-heart-pulse</v-icon>
            <span class="font-display text-h6">System Health</span>
          </v-card-title>
          <v-card-text class="pa-4 pt-0">
            <div v-if="healthLoading" class="text-center py-4">
              <v-progress-circular indeterminate color="primary" size="24" />
            </div>
            <div v-else-if="auth.isAdmin && health" class="d-flex flex-column ga-3">
              <HealthRow
                v-for="row in healthRows"
                :key="row.label"
                :label="row.label"
                :ok="row.ok"
                :detail="row.detail"
              />
            </div>
            <div v-else class="text-caption text-medium-emphasis text-center py-4">
              Health details available to admins.
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, defineComponent, h } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useCharactersStore } from '@/stores/characters'
import { healthApi } from '@/api'

const auth      = useAuthStore()
const charStore = useCharactersStore()

// ── Health ────────────────────────────────────────────────────────────────
const health        = ref(null)
const healthLoading = ref(false)

const healthRows = computed(() => health.value ? [
  { label: 'Database', ok: health.value.db_healthy,  detail: health.value.database },
  { label: 'LLM',      ok: health.value.llm_healthy, detail: health.value.default_llm_model },
  { label: 'TTS',      ok: health.value.tts_healthy, detail: health.value.default_tts_provider },
] : [])

// ── Stats ─────────────────────────────────────────────────────────────────
const stats = computed(() => [
  {
    label: 'Characters', value: charStore.list.length, trend: 0,
    icon: 'mdi-account-star-outline', iconColor: 'primary',
    iconBg: 'rgba(6,182,212,0.12)',
  },
  {
    label: 'Skills Active', value: '2', trend: 0,
    icon: 'mdi-lightning-bolt-outline', iconColor: 'secondary',
    iconBg: 'rgba(236,72,153,0.12)',
  },
  {
    label: 'Knowledge Docs', value: '—', trend: 0,
    icon: 'mdi-book-open-outline', iconColor: 'accent',
    iconBg: 'rgba(139,92,246,0.12)',
  },
  {
    label: 'Total Sessions', value: '—', trend: 0,
    icon: 'mdi-chat-outline', iconColor: 'tertiary',
    iconBg: 'rgba(16,185,129,0.12)',
  },
])

const quickActions = [
  { label: 'Create Character',   to: { name: 'character-create' }, icon: 'mdi-account-plus-outline',  color: 'primary'   },
  { label: 'Upload Knowledge',   to: { name: 'knowledge'        }, icon: 'mdi-file-plus-outline',     color: 'accent'    },
  { label: 'Browse Skills',      to: { name: 'skills'           }, icon: 'mdi-lightning-bolt-outline', color: 'secondary' },
  { label: 'View Conversations', to: { name: 'conversations'    }, icon: 'mdi-chat-outline',           color: 'tertiary'  },
]

// ── Inline HealthRow component ─────────────────────────────────────────────
const HealthRow = defineComponent({
  props: ['label', 'ok', 'detail'],
  setup(props) {
    return () => h('div', { class: 'd-flex align-center ga-3' }, [
      h('div', {
        class: props.ok ? 'status-online' : '',
        style: props.ok ? '' : 'width:8px;height:8px;border-radius:50%;background:#F43F5E;',
      }),
      h('div', { class: 'flex-1 text-body-2' }, props.label),
      h('div', { class: 'text-caption font-mono text-medium-emphasis' }, props.detail ?? ''),
    ])
  },
})

onMounted(async () => {
  await charStore.fetchList()
  if (auth.isAdmin) {
    healthLoading.value = true
    try { const { data } = await healthApi.system(); health.value = data }
    catch { /* non-critical */ }
    finally { healthLoading.value = false }
  }
})
</script>

<style scoped>
.welcome-banner { position: relative; overflow: hidden; }
.welcome-banner::before {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(120deg, rgba(6,182,212,0.06) 0%, rgba(139,92,246,0.04) 50%, transparent 100%);
  pointer-events: none;
}
.hero-avatar {
  width: 60px; height: 60px;
  background: rgba(6,182,212,0.12);
  border: 1px solid rgba(6,182,212,0.25);
  border-radius: 16px;
  flex-shrink: 0;
}
.char-row {
  cursor: pointer;
  transition: background 0.15s;
  &:hover { background: rgba(6,182,212,0.06); }
}
.stat-card::before {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(135deg, rgba(6,182,212,0.04) 0%, transparent 60%);
  pointer-events: none;
  border-radius: inherit;
}
</style>