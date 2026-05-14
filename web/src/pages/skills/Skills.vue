<template>
  <div>
    <div class="d-flex align-center ga-3 mb-6 flex-wrap">
      <v-text-field
        v-model="search"
        placeholder="Search skills…"
        prepend-inner-icon="mdi-magnify"
        clearable hide-details density="comfortable"
        style="max-width:280px;"
      />
      <v-chip-group v-model="filterType" color="primary" mandatory selected-class="chip-cyan">
        <v-chip value="all"     size="small">All</v-chip>
        <v-chip value="builtin" size="small">Built-in</v-chip>
        <v-chip value="plugin"  size="small">Plugin</v-chip>
        <v-chip value="custom"  size="small">Custom</v-chip>
      </v-chip-group>
      <v-spacer />
      <v-chip class="font-mono" size="small" variant="outlined">
        {{ filtered.length }} skill{{ filtered.length !== 1 ? 's' : '' }}
      </v-chip>
    </div>

    <div v-if="loading" class="text-center py-16">
      <v-progress-circular indeterminate color="primary" size="40" />
    </div>

    <v-row v-else dense>
      <v-col v-for="skill in filtered" :key="skill.id" cols="12" sm="6" lg="4">
        <v-card class="glass skill-card" rounded="xl" height="100%">
          <v-card-text class="pa-5 d-flex flex-column ga-3">
            <!-- Header -->
            <div class="d-flex align-start ga-3">
              <div
                class="skill-icon d-flex align-center justify-center rounded-lg flex-shrink-0"
                :style="{ background: typeColor(skill.skill_type) }"
              >
                <v-icon size="20" :color="typeIconColor(skill.skill_type)">
                  {{ typeIcon(skill.skill_type) }}
                </v-icon>
              </div>
              <div class="flex-1 overflow-hidden">
                <div class="text-body-1 font-weight-semibold">{{ skill.display_name }}</div>
                <div class="font-mono text-caption text-medium-emphasis">{{ skill.name }}</div>
              </div>
              <!-- Admin toggle -->
              <v-switch
                v-if="auth.isAdmin"
                :model-value="skill.is_active"
                color="primary"
                density="compact"
                hide-details
                inset
                :loading="toggling === skill.id"
                @update:model-value="toggleSkill(skill)"
              />
              <v-chip v-else size="x-small" :color="skill.is_active ? 'success' : 'error'" variant="tonal">
                {{ skill.is_active ? 'active' : 'disabled' }}
              </v-chip>
            </div>

            <!-- Description -->
            <p class="text-body-2 text-medium-emphasis" style="line-height:1.6;flex:1;">
              {{ skill.description }}
            </p>

            <!-- Badges -->
            <div class="d-flex flex-wrap ga-1">
              <v-chip size="x-small" :class="typeChipClass(skill.skill_type)">
                {{ skill.skill_type }}
              </v-chip>
              <v-chip v-if="skill.is_builtin" size="x-small" variant="outlined" density="compact">
                built-in
              </v-chip>
            </div>

            <!-- Parameter preview -->
            <div v-if="skill.config_schema?.properties" class="param-list rounded-lg pa-2">
              <div class="text-caption text-medium-emphasis mb-1">Parameters</div>
              <div
                v-for="(def, name) in skill.config_schema.properties"
                :key="name"
                class="d-flex align-center ga-2 mb-1"
              >
                <v-chip size="x-small" class="chip-violet font-mono">{{ name }}</v-chip>
                <span class="text-caption text-medium-emphasis">{{ def.type }}</span>
                <span v-if="def.description" class="text-caption text-medium-emphasis text-truncate">
                  — {{ def.description }}
                </span>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Empty state -->
      <v-col v-if="filtered.length === 0" cols="12">
        <div class="text-center py-16 text-medium-emphasis">
          <v-icon size="56" class="mb-4 opacity-30">mdi-lightning-bolt-outline</v-icon>
          <div>No skills match your filter.</div>
        </div>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { skillsApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'

const auth    = useAuthStore()
const app     = useAppStore()
const skills  = ref([])
const loading = ref(false)
const search  = ref('')
const filterType = ref('all')
const toggling = ref(null)

const filtered = computed(() => {
  let list = skills.value
  if (filterType.value !== 'all') list = list.filter(s => s.skill_type === filterType.value)
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(s =>
      s.name.includes(q) || s.display_name.toLowerCase().includes(q) ||
      s.description.toLowerCase().includes(q)
    )
  }
  return list
})

async function load() {
  loading.value = true
  try { const { data } = await skillsApi.list(); skills.value = data }
  finally { loading.value = false }
}

async function toggleSkill(skill) {
  toggling.value = skill.id
  try {
    const { data } = await skillsApi.toggle(skill.id)
    const idx = skills.value.findIndex(s => s.id === skill.id)
    if (idx !== -1) skills.value[idx] = data
    app.notify(`Skill "${skill.display_name}" ${data.is_active ? 'enabled' : 'disabled'}.`)
  } catch (err) { app.notifyError(err) }
  finally { toggling.value = null }
}

function typeIcon(type) {
  return { builtin: 'mdi-lightning-bolt', plugin: 'mdi-puzzle-outline', custom: 'mdi-code-braces' }[type] ?? 'mdi-lightning-bolt'
}
function typeColor(type) {
  return { builtin: 'rgba(6,182,212,0.12)', plugin: 'rgba(236,72,153,0.12)', custom: 'rgba(139,92,246,0.12)' }[type] ?? 'rgba(6,182,212,0.12)'
}
function typeIconColor(type) {
  return { builtin: 'primary', plugin: 'secondary', custom: 'accent' }[type] ?? 'primary'
}
function typeChipClass(type) {
  return { builtin: 'chip-cyan', plugin: 'chip-pink', custom: 'chip-violet' }[type] ?? 'chip-cyan'
}

onMounted(load)
</script>

<style scoped>
.skill-card { transition: transform 0.18s; &:hover { transform: translateY(-2px); } }
.skill-icon { width:44px;height:44px;flex-shrink:0; }
.param-list {
  background: rgba(0,0,0,0.2);
  border: 1px solid rgba(255,255,255,0.06);
}
</style>