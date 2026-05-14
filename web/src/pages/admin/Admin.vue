<template>
  <div>
    <v-tabs v-model="tab" color="primary" class="mb-5" density="comfortable">
      <v-tab value="system" prepend-icon="mdi-server">System</v-tab>
      <v-tab value="users"  prepend-icon="mdi-account-group">Users</v-tab>
      <v-tab value="plugins" prepend-icon="mdi-puzzle-outline">Plugins & Skills</v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <!-- ── System health ── -->
      <v-window-item value="system">
        <v-row>
          <v-col
            v-for="stat in systemStats"
            :key="stat.label"
            cols="12" sm="6" md="3"
          >
            <v-card class="glass stat-card pa-5" rounded="xl">
              <div class="d-flex align-center justify-space-between mb-3">
                <div class="stat-icon d-flex align-center justify-center rounded-lg"
                  :style="{ background: stat.iconBg }">
                  <v-icon :icon="stat.icon" :color="stat.color" size="20" />
                </div>
                <div v-if="stat.healthy !== undefined" class="d-flex align-center ga-1">
                  <div :class="stat.healthy ? 'status-online' : ''" :style="!stat.healthy ? 'width:8px;height:8px;border-radius:50%;background:#F43F5E;' : ''" />
                  <span class="text-caption" :class="stat.healthy ? 'text-success' : 'text-error'">
                    {{ stat.healthy ? 'Online' : 'Offline' }}
                  </span>
                </div>
              </div>
              <div class="text-h5 font-display font-weight-bold mb-1">{{ stat.value }}</div>
              <div class="text-caption text-medium-emphasis">{{ stat.label }}</div>
              <div v-if="stat.detail" class="text-caption font-mono text-medium-emphasis mt-1">{{ stat.detail }}</div>
            </v-card>
          </v-col>

          <!-- Plugin list -->
          <v-col cols="12" md="6">
            <v-card class="glass" rounded="xl">
              <v-card-title class="d-flex align-center pa-5 pb-3 ga-2">
                <v-icon color="accent" size="18">mdi-puzzle-outline</v-icon>
                <span class="font-display text-subtitle-1">Loaded Plugins</span>
              </v-card-title>
              <v-card-text class="pa-4 pt-0">
                <div v-if="!health?.loaded_plugins?.length" class="text-medium-emphasis text-body-2 text-center py-4">
                  No plugins loaded.
                </div>
                <v-chip
                  v-for="plugin in health?.loaded_plugins"
                  :key="plugin"
                  class="chip-violet ma-1"
                  size="small"
                  prepend-icon="mdi-puzzle"
                >
                  {{ plugin }}
                </v-chip>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- Registered skills -->
          <v-col cols="12" md="6">
            <v-card class="glass" rounded="xl">
              <v-card-title class="d-flex align-center pa-5 pb-3 ga-2">
                <v-icon color="primary" size="18">mdi-lightning-bolt-outline</v-icon>
                <span class="font-display text-subtitle-1">Registered Skills</span>
              </v-card-title>
              <v-card-text class="pa-4 pt-0">
                <v-chip
                  v-for="name in health?.registered_skills"
                  :key="name"
                  class="chip-cyan ma-1"
                  size="small"
                  prepend-icon="mdi-lightning-bolt"
                >
                  {{ name }}
                </v-chip>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-window-item>

      <!-- ── Users ── -->
      <v-window-item value="users">
        <v-card class="glass" rounded="xl">
          <v-card-title class="d-flex align-center pa-5 pb-3 ga-2">
            <v-icon color="primary" size="18">mdi-account-group-outline</v-icon>
            <span class="font-display text-subtitle-1">All Users</span>
            <v-spacer />
            <v-btn icon="mdi-refresh" size="x-small" variant="text" @click="loadUsers" :loading="loadingUsers" />
          </v-card-title>
          <v-card-text class="pa-4 pt-0">
            <v-data-table
              :headers="userHeaders"
              :items="users"
              :loading="loadingUsers"
              density="comfortable"
              class="transparent-table"
            >
              <template #item.role="{ item }">
                <v-chip size="x-small" :class="roleClass(item.role)">{{ item.role }}</v-chip>
              </template>
              <template #item.is_active="{ item }">
                <v-chip size="x-small" :color="item.is_active ? 'success' : 'error'" variant="tonal">
                  {{ item.is_active ? 'Active' : 'Inactive' }}
                </v-chip>
              </template>
              <template #item.created_at="{ item }">
                <span class="text-caption font-mono">{{ formatDate(item.created_at) }}</span>
              </template>
              <template #item.actions="{ item }">
                <div class="d-flex ga-1">
                  <v-select
                    :model-value="item.role"
                    :items="['user','moderator','admin']"
                    density="compact"
                    hide-details
                    variant="outlined"
                    style="max-width:120px;font-size:12px;"
                    @update:model-value="setRole(item, $event)"
                  />
                  <v-btn
                    v-if="item.is_active && item.id !== auth.user?.id"
                    icon="mdi-account-off"
                    size="x-small"
                    variant="text"
                    color="error"
                    @click="deactivate(item)"
                  >
                    <v-tooltip activator="parent">Deactivate</v-tooltip>
                  </v-btn>
                </div>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-window-item>

      <!-- ── Plugins & Skills tab ── -->
      <v-window-item value="plugins">
        <v-alert color="info" variant="tonal" class="mb-5" prepend-icon="mdi-information-outline">
          Place plugin packages in <code class="font-mono">workspace/plugins/</code> and restart the server to load them.
          Skill toggles are available in the <router-link :to="{ name: 'skills' }" class="text-primary">Skills Library</router-link>.
        </v-alert>
        <v-row>
          <v-col cols="12" md="6">
            <v-card class="glass" rounded="xl">
              <v-card-title class="pa-5 pb-3 font-display text-subtitle-1">Plugin Directory</v-card-title>
              <v-card-text class="pa-4 pt-0">
                <div class="system-prompt-box rounded-lg pa-3 font-mono text-caption">
                  workspace/<br/>
                  └── plugins/<br/>
                  &nbsp;&nbsp;&nbsp;&nbsp;└── my_plugin/<br/>
                  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── __init__.py
                </div>
                <p class="text-caption text-medium-emphasis mt-3">
                  Each plugin folder must contain <code>__init__.py</code> exposing a <code>BasePlugin</code> subclass.
                  See the <code>examples/plugins/weather_plugin/</code> in the backend repo for a template.
                </p>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { healthApi, usersApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'

const auth = useAuthStore()
const app  = useAppStore()
const tab  = ref('system')

const health       = ref(null)
const users        = ref([])
const loadingUsers = ref(false)

const systemStats = computed(() => health.value ? [
  { label: 'Database',    value: health.value.database,           color: 'primary',   icon: 'mdi-database',         iconBg: 'rgba(6,182,212,0.12)',  healthy: health.value.db_healthy  },
  { label: 'LLM Model',   value: health.value.default_llm_model,  color: 'secondary', icon: 'mdi-brain',            iconBg: 'rgba(236,72,153,0.12)', healthy: health.value.llm_healthy },
  { label: 'TTS Provider',value: health.value.default_tts_provider,color:'tertiary',  icon: 'mdi-microphone',       iconBg: 'rgba(16,185,129,0.12)', healthy: health.value.tts_healthy },
  { label: 'Version',     value: health.value.version,            color: 'accent',    icon: 'mdi-tag-outline',      iconBg: 'rgba(139,92,246,0.12)', healthy: undefined },
] : [])

const userHeaders = [
  { title: 'Username', key: 'username',   sortable: true },
  { title: 'Email',    key: 'email',      sortable: true },
  { title: 'Role',     key: 'role',       sortable: true },
  { title: 'Status',   key: 'is_active',  sortable: true },
  { title: 'Joined',   key: 'created_at', sortable: true },
  { title: 'Actions',  key: 'actions',    sortable: false },
]

function roleClass(r) { return { admin: 'chip-pink', moderator: 'chip-violet', user: 'chip-cyan' }[r] ?? 'chip-cyan' }
function formatDate(iso) { return iso ? new Date(iso).toLocaleDateString() : '' }

async function loadUsers() {
  loadingUsers.value = true
  try { const { data } = await usersApi.list(); users.value = data }
  finally { loadingUsers.value = false }
}

async function setRole(user, role) {
  try { await usersApi.setRole(user.id, role); await loadUsers(); app.notify(`Role updated to "${role}".`) }
  catch (err) { app.notifyError(err) }
}

async function deactivate(user) {
  const ok = await app.showConfirm('Deactivate User', `Deactivate "${user.username}"?`)
  if (!ok) return
  try { await usersApi.deactivate(user.id); await loadUsers(); app.notify('User deactivated.') }
  catch (err) { app.notifyError(err) }
}

onMounted(async () => {
  try { const { data } = await healthApi.system(); health.value = data } catch { /**/ }
  await loadUsers()
})
</script>

<style scoped>
.stat-card { position: relative; overflow: hidden; }
.stat-card::before {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(135deg, rgba(6,182,212,0.04) 0%, transparent 60%);
  pointer-events: none; border-radius: inherit;
}
.stat-icon { width:40px;height:40px;flex-shrink:0; }
.system-prompt-box {
  background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.07);
  white-space: pre-wrap; line-height: 1.7;
}
:deep(.v-data-table) { background: transparent !important; }
:deep(.v-data-table-header__content) { font-weight: 600; color: rgba(255,255,255,0.5); }
</style>