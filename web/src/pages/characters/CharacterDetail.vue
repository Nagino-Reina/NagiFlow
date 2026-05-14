<template>
  <div v-if="charStore.loading" class="d-flex justify-center py-20">
    <v-progress-circular indeterminate color="primary" size="40" />
  </div>

  <div v-else-if="char">
    <!-- Character hero header -->
    <v-card class="glass-bright mb-6 pa-6" rounded="xl">
      <div class="d-flex align-start ga-5 flex-wrap">
        <v-avatar size="80" color="surface-2" class="avatar-ring flex-shrink-0">
          <span class="font-display font-weight-bold text-h4" style="color:#06B6D4;">
            {{ char.name.charAt(0) }}
          </span>
        </v-avatar>
        <div class="flex-1">
          <div class="d-flex align-center ga-3 flex-wrap mb-1">
            <h1 class="font-display text-h4 font-weight-bold" style="letter-spacing:-.03em;">
              {{ char.name }}
            </h1>
            <v-chip v-if="char.model_type" size="small"
              :class="char.model_type === 'live2d' ? 'chip-cyan' : 'chip-violet'">
              {{ char.model_type === 'live2d' ? 'Live2D' : '3D' }}
            </v-chip>
            <v-chip v-if="char.is_public" size="small" class="chip-emerald">public</v-chip>
          </div>
          <p class="text-body-1 text-medium-emphasis mb-3" style="max-width:580px;">
            {{ char.description ?? 'No description provided.' }}
          </p>
          <div class="d-flex flex-wrap ga-2">
            <v-chip v-if="char.llm_model"     size="small" prepend-icon="mdi-brain"      variant="outlined">{{ char.llm_model }}</v-chip>
            <v-chip v-if="char.tts_provider"  size="small" prepend-icon="mdi-microphone" variant="outlined">{{ char.tts_provider }}</v-chip>
          </div>
        </div>
        <div class="d-flex ga-2 flex-shrink-0">
          <v-btn color="primary" prepend-icon="mdi-chat-outline" class="glow-cyan"
            :to="{ name: 'character-chat', params: { id: char.id } }">
            Start Chat
          </v-btn>
          <v-btn icon="mdi-pencil-outline" variant="tonal"
            :to="{ name: 'character-edit', params: { id: char.id } }" />
        </div>
      </div>
    </v-card>

    <!-- Tabs -->
    <v-tabs v-model="tab" color="primary" class="mb-4" density="comfortable">
      <v-tab value="overview"  prepend-icon="mdi-view-dashboard-outline">Overview</v-tab>
      <v-tab value="skills"    prepend-icon="mdi-lightning-bolt-outline">Skills</v-tab>
      <v-tab value="memory"    prepend-icon="mdi-brain">Memory</v-tab>
      <v-tab value="knowledge" prepend-icon="mdi-book-open-outline">Knowledge</v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <!-- ── Overview ── -->
      <v-window-item value="overview">
        <v-row>
          <v-col cols="12" md="6">
            <v-card class="glass" rounded="xl">
              <v-card-title class="d-flex align-center pa-5 pb-3 ga-2">
                <v-icon color="secondary" size="18">mdi-head-cog-outline</v-icon>
                <span class="font-display text-subtitle-1">Big Five Personality</span>
              </v-card-title>
              <v-card-text class="pa-5 pt-2">
                <div class="d-flex justify-center mb-4">
                  <PersonalityRadar :scores="bigFive" :size="200" />
                </div>
                <div v-for="(score, trait) in bigFive" :key="trait" class="mb-3">
                  <div class="d-flex justify-space-between mb-1">
                    <span class="text-body-2 text-capitalize">{{ trait }}</span>
                    <span class="text-caption font-mono" :style="{ color: traitColor(trait) }">{{ score }}/100</span>
                  </div>
                  <v-progress-linear :model-value="score" max="100" height="6"
                    :color="traitColor(trait)" bg-color="rgba(255,255,255,0.06)" rounded />
                </div>
              </v-card-text>
            </v-card>
          </v-col>

          <v-col cols="12" md="6">
            <v-card class="glass mb-4" rounded="xl">
              <v-card-title class="d-flex align-center pa-5 pb-3 ga-2">
                <v-icon color="primary" size="18">mdi-robot-outline</v-icon>
                <span class="font-display text-subtitle-1">System Prompt</span>
              </v-card-title>
              <v-card-text class="pa-5 pt-2">
                <div v-if="char.system_prompt" class="system-prompt-box rounded-lg pa-3 font-mono text-caption">
                  {{ char.system_prompt }}
                </div>
                <div v-else class="text-medium-emphasis text-caption text-center py-4">
                  Auto-generated from personality settings.
                </div>
              </v-card-text>
            </v-card>

            <v-card v-if="customConfig && Object.keys(customConfig).length" class="glass" rounded="xl">
              <v-card-title class="d-flex align-center pa-5 pb-3 ga-2">
                <v-icon color="accent" size="18">mdi-tune</v-icon>
                <span class="font-display text-subtitle-1">Custom Config</span>
              </v-card-title>
              <v-card-text class="pa-5 pt-2">
                <div v-for="(val, key) in customConfig" :key="key" class="d-flex ga-2 mb-2">
                  <v-chip size="x-small" class="chip-violet font-mono">{{ key }}</v-chip>
                  <span class="text-body-2 text-medium-emphasis">{{ val }}</span>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-window-item>

      <!-- ── Skills ── -->
      <v-window-item value="skills">
        <SkillAssignPanel :character-id="char.id" />
      </v-window-item>

      <!-- ── Memory ── -->
      <v-window-item value="memory">
        <MemoryPanel :character-id="char.id" />
      </v-window-item>

      <!-- ── Knowledge ── -->
      <v-window-item value="knowledge">
        <KnowledgePanel :character-id="char.id" />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useCharactersStore } from '@/stores/characters'
import PersonalityRadar from '@/components/character/PersonalityRadar.vue'
import SkillAssignPanel from '@/components/character/SkillAssignPanel.vue'
import MemoryPanel      from '@/components/memory/MemoryPanel.vue'
import KnowledgePanel   from '@/components/knowledge/KnowledgePanel.vue'

const route     = useRoute()
const charStore = useCharactersStore()
const tab       = ref('overview')

const char = computed(() => charStore.current)

const bigFive = computed(() =>
  char.value?.personality?.big_five ?? {
    openness: 50, conscientiousness: 50, extraversion: 50,
    agreeableness: 50, neuroticism: 50,
  }
)
const customConfig = computed(() => char.value?.personality?.custom ?? {})

const traitColors = {
  openness: '#06B6D4', conscientiousness: '#8B5CF6',
  extraversion: '#EC4899', agreeableness: '#10B981', neuroticism: '#F59E0B',
}
const traitColor = (t) => traitColors[t] ?? '#06B6D4'

onMounted(() => charStore.fetchOne(route.params.id))
</script>

<style scoped>
.avatar-ring { outline: 3px solid rgba(6,182,212,0.3); outline-offset: 3px; }
.system-prompt-box {
  background: rgba(0,0,0,0.25);
  border: 1px solid rgba(255,255,255,0.07);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 220px;
  overflow-y: auto;
  line-height: 1.7;
}
</style>