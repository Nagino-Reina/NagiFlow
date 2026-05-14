<template>
  <v-row>
    <!-- Assigned skills -->
    <v-col cols="12" md="6">
      <v-card class="glass" rounded="xl">
        <v-card-title class="d-flex align-center pa-5 pb-3 ga-2">
          <v-icon color="primary" size="18">mdi-check-circle-outline</v-icon>
          <span class="font-display text-subtitle-1">Assigned Skills</span>
          <v-spacer />
          <v-btn icon="mdi-refresh" size="x-small" variant="text" @click="loadAssigned" :loading="loadingAssigned" />
        </v-card-title>
        <v-card-text class="pa-4 pt-0">
          <div v-if="loadingAssigned" class="text-center py-6">
            <v-progress-circular indeterminate color="primary" size="24" />
          </div>
          <div v-else-if="assigned.length === 0" class="text-center py-8 text-medium-emphasis">
            <v-icon size="40" class="mb-2 opacity-30">mdi-lightning-bolt-outline</v-icon>
            <div class="text-body-2">No skills assigned yet.</div>
          </div>
          <div v-else class="d-flex flex-column ga-2">
            <div
              v-for="cs in assigned"
              :key="cs.id"
              class="skill-row d-flex align-center ga-3 pa-3 rounded-xl"
            >
              <div class="skill-icon d-flex align-center justify-center rounded-lg">
                <v-icon size="18" color="primary">mdi-lightning-bolt</v-icon>
              </div>
              <div class="flex-1 overflow-hidden">
                <div class="text-body-2 font-weight-medium text-truncate">{{ cs.skill_display_name }}</div>
                <div class="text-caption font-mono text-medium-emphasis">{{ cs.skill_name }}</div>
              </div>
              <v-switch
                :model-value="cs.is_enabled"
                color="primary"
                density="compact"
                hide-details
                inset
                @update:model-value="toggleSkill(cs)"
              />
              <v-btn icon="mdi-delete-outline" size="x-small" variant="text" color="error"
                @click="removeSkill(cs)" />
            </div>
          </div>
        </v-card-text>
      </v-card>
    </v-col>

    <!-- Available skills -->
    <v-col cols="12" md="6">
      <v-card class="glass" rounded="xl">
        <v-card-title class="d-flex align-center pa-5 pb-3 ga-2">
          <v-icon color="secondary" size="18">mdi-view-grid-plus-outline</v-icon>
          <span class="font-display text-subtitle-1">Available Skills</span>
        </v-card-title>
        <v-card-text class="pa-4 pt-0">
          <div v-if="loadingAll" class="text-center py-6">
            <v-progress-circular indeterminate color="primary" size="24" />
          </div>
          <div v-else class="d-flex flex-column ga-2">
            <div
              v-for="skill in unassigned"
              :key="skill.id"
              class="skill-row d-flex align-center ga-3 pa-3 rounded-xl"
            >
              <div class="skill-icon skill-icon--secondary d-flex align-center justify-center rounded-lg">
                <v-icon size="18" color="secondary">mdi-lightning-bolt-outline</v-icon>
              </div>
              <div class="flex-1 overflow-hidden">
                <div class="text-body-2 font-weight-medium text-truncate">{{ skill.display_name }}</div>
                <div class="text-caption text-medium-emphasis text-truncate">{{ skill.description }}</div>
              </div>
              <v-chip v-if="skill.is_builtin" size="x-small" class="chip-cyan">builtin</v-chip>
              <v-btn
                icon="mdi-plus"
                size="x-small"
                variant="tonal"
                color="primary"
                @click="assign(skill)"
                :loading="assigning === skill.id"
              />
            </div>
            <div v-if="unassigned.length === 0" class="text-center py-4 text-medium-emphasis text-body-2">
              All available skills are assigned.
            </div>
          </div>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { charactersApi, skillsApi } from '@/api'
import { useAppStore } from '@/stores/app'

const props = defineProps({ characterId: { type: String, required: true } })
const app   = useAppStore()

const assigned        = ref([])
const allSkills       = ref([])
const loadingAssigned = ref(false)
const loadingAll      = ref(false)
const assigning       = ref(null)

const assignedIds = computed(() => new Set(assigned.value.map(cs => cs.skill_id)))
const unassigned  = computed(() => allSkills.value.filter(s => !assignedIds.value.has(s.id) && s.is_active))

async function loadAssigned() {
  loadingAssigned.value = true
  try {
    const { data } = await charactersApi.listSkills(props.characterId)
    assigned.value = data
  } finally { loadingAssigned.value = false }
}

async function loadAll() {
  loadingAll.value = true
  try {
    const { data } = await skillsApi.list()
    allSkills.value = data
  } finally { loadingAll.value = false }
}

async function assign(skill) {
  assigning.value = skill.id
  try {
    await charactersApi.assignSkill(props.characterId, { skill_id: skill.id, is_enabled: true })
    await loadAssigned()
    app.notify(`Skill "${skill.display_name}" assigned.`)
  } catch (err) { app.notifyError(err) }
  finally { assigning.value = null }
}

async function removeSkill(cs) {
  try {
    await charactersApi.removeSkill(props.characterId, cs.skill_id)
    await loadAssigned()
    app.notify('Skill removed.')
  } catch (err) { app.notifyError(err) }
}

async function toggleSkill(cs) {
  try {
    await charactersApi.assignSkill(props.characterId, {
      skill_id: cs.skill_id,
      is_enabled: !cs.is_enabled,
      config: cs.config,
    })
    await loadAssigned()
  } catch (err) { app.notifyError(err) }
}

onMounted(() => Promise.all([loadAssigned(), loadAll()]))
</script>

<style scoped>
.skill-row {
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.05);
  transition: background 0.15s;
  &:hover { background: rgba(6,182,212,0.05); }
}
.skill-icon {
  width: 36px; height: 36px;
  background: rgba(6,182,212,0.1);
  flex-shrink: 0;
}
.skill-icon--secondary { background: rgba(236,72,153,0.1); }
</style>