<template>
  <v-layout style="height:100vh; background:#070B16;">

    <!-- ── Sidebar ───────────────────────────────────────────────────── -->
    <v-navigation-drawer
      v-model="app.drawerOpen"
      :rail="rail"
      permanent
      color="surface-dim"
      width="240"
      style="border-right: 1px solid rgba(255,255,255,0.06);"
    >
      <!-- Logo -->
      <div class="d-flex align-center ga-3 px-4 py-5" style="min-height:64px;">
        <div class="logo-gem flex-shrink-0" />
        <transition name="fade">
          <div v-if="!rail">
            <div class="font-display gradient-text" style="font-size:1.15rem;font-weight:700;line-height:1.1;">
              NagiFlow
            </div>
            <div class="text-caption text-medium-emphasis" style="font-size:10px;letter-spacing:.06em;margin-top:1px;">
              AI VTUBER FRAMEWORK
            </div>
          </div>
        </transition>
        <v-spacer />
        <v-btn
          v-if="!rail"
          icon
          variant="text"
          size="small"
          @click="rail = true"
        >
          <v-icon size="18">mdi-chevron-left</v-icon>
        </v-btn>
      </div>

      <v-divider />

      <!-- Nav items -->
      <v-list nav density="compact" class="px-1 mt-2">
        <!-- Expand rail button -->
        <v-list-item v-if="rail" @click="rail = false" class="nav-item mb-1">
          <template #prepend>
            <v-icon size="20">mdi-chevron-right</v-icon>
          </template>
        </v-list-item>

        <template v-for="item in navItems" :key="item.name">
          <v-list-item
            :to="{ name: item.name }"
            :prepend-icon="item.icon"
            :title="item.label"
            class="nav-item"
            :class="{ 'nav-active': isActive(item) }"
            active-class=""
            :ripple="false"
          >
            <template #append v-if="!rail && item.badge">
              <v-chip size="x-small" color="secondary" class="chip-pink" density="compact">
                {{ item.badge }}
              </v-chip>
            </template>
          </v-list-item>
        </template>

        <v-divider class="my-2" />

        <!-- Admin section -->
        <v-list-item
          v-if="auth.isAdmin"
          :to="{ name: 'admin' }"
          prepend-icon="mdi-shield-crown"
          title="Admin"
          class="nav-item"
          :class="{ 'nav-active': route.name === 'admin' }"
          active-class=""
          :ripple="false"
        />
      </v-list>

      <template #append>
        <v-divider />
        <!-- User card -->
        <v-menu location="top end" :offset="8">
          <template #activator="{ props }">
            <div
              v-bind="props"
              class="d-flex align-center ga-3 px-3 py-3 cursor-pointer user-card"
            >
              <v-avatar size="34" color="primary" style="font-family:var(--font-display);font-weight:600;font-size:14px;">
                {{ userInitial }}
              </v-avatar>
              <transition name="fade">
                <div v-if="!rail" class="overflow-hidden">
                  <div class="text-body-2 font-weight-medium text-truncate" style="max-width:130px;">
                    {{ auth.user?.username }}
                  </div>
                  <div class="text-caption text-medium-emphasis text-truncate" style="max-width:130px;">
                    {{ auth.user?.role }}
                  </div>
                </div>
              </transition>
            </div>
          </template>
          <v-list rounded="xl" class="glass-bright" min-width="180" elevation="0">
            <v-list-item :to="{ name: 'settings' }" prepend-icon="mdi-cog" title="Settings" />
            <v-divider />
            <v-list-item
              prepend-icon="mdi-logout"
              title="Sign Out"
              base-color="error"
              @click="auth.logout"
            />
          </v-list>
        </v-menu>
      </template>
    </v-navigation-drawer>

    <!-- ── Main content ───────────────────────────────────────────────── -->
    <v-main style="overflow-y:auto; background:#070B16;">
      <!-- Top bar -->
      <div
        class="d-flex align-center px-6 py-3"
        style="
          height:64px;
          background:rgba(7,11,22,0.85);
          backdrop-filter:blur(12px);
          border-bottom:1px solid rgba(255,255,255,0.05);
          position:sticky; top:0; z-index:10;
        "
      >
        <div>
          <div class="font-display text-h6 font-weight-semibold" style="letter-spacing:-.02em;">
            {{ pageTitle }}
          </div>
          <div v-if="pageSubtitle" class="text-caption text-medium-emphasis">
            {{ pageSubtitle }}
          </div>
        </div>

        <v-spacer />

        <!-- Quick actions -->
        <div class="d-flex align-center ga-2">
          <v-btn
            v-if="route.name !== 'character-create'"
            :to="{ name: 'character-create' }"
            color="primary"
            size="small"
            prepend-icon="mdi-plus"
            variant="tonal"
            class="glow-cyan"
          >
            New Character
          </v-btn>

          <v-btn icon variant="text" size="small">
            <v-icon size="20">mdi-bell-outline</v-icon>
          </v-btn>
        </div>
      </div>

      <!-- Page content -->
      <div class="pa-6">
        <router-view v-slot="{ Component, route: r }">
          <transition name="page" mode="out-in">
            <component :is="Component" :key="r.path" />
          </transition>
        </router-view>
      </div>
    </v-main>
  </v-layout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const auth  = useAuthStore()
const app   = useAppStore()

const rail  = ref(false)

const userInitial = computed(() =>
  (auth.user?.username ?? 'U').charAt(0).toUpperCase()
)

const navItems = [
  { name: 'dashboard',   icon: 'mdi-view-dashboard-outline', label: 'Dashboard' },
  { name: 'characters',  icon: 'mdi-account-star-outline',   label: 'Characters' },
  { name: 'conversations', icon: 'mdi-chat-outline',         label: 'Conversations' },
  { name: 'knowledge',   icon: 'mdi-book-open-outline',      label: 'Knowledge' },
  { name: 'skills',      icon: 'mdi-lightning-bolt-outline',  label: 'Skills' },
]

function isActive(item) {
  return route.name === item.name ||
    route.matched.some(r => r.name === item.name)
}

const pageMeta = {
  dashboard:         { title: 'Dashboard',       sub: 'Overview of your AI Vtuber setup' },
  characters:        { title: 'Characters',      sub: 'Manage your AI Vtuber personas' },
  'character-create':{ title: 'Create Character',sub: 'Design a new AI Vtuber' },
  'character-detail':{ title: 'Character Detail',sub: '' },
  'character-edit':  { title: 'Edit Character',  sub: '' },
  'character-chat':  { title: 'Live Chat',       sub: 'Stream conversation' },
  conversations:     { title: 'Conversations',   sub: 'Your chat history' },
  knowledge:         { title: 'Knowledge Base',  sub: 'Documents and RAG sources' },
  skills:            { title: 'Skills Library',  sub: 'Agent tools and capabilities' },
  settings:          { title: 'Settings',        sub: 'Account & preferences' },
  admin:             { title: 'Admin Panel',     sub: 'System management' },
}

const pageTitle    = computed(() => pageMeta[route.name]?.title    ?? '')
const pageSubtitle = computed(() => pageMeta[route.name]?.sub      ?? '')
</script>

<style scoped>
.logo-gem {
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, #06B6D4 0%, #8B5CF6 50%, #EC4899 100%);
  border-radius: 10px;
  flex-shrink: 0;
  box-shadow: 0 0 16px rgba(6,182,212,0.45);
}

.user-card {
  border-radius: 12px;
  margin: 6px 6px 8px;
  transition: background 0.18s;
  &:hover { background: rgba(255,255,255,0.05); }
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.18s; }
.fade-enter-from, .fade-leave-to       { opacity: 0; }
</style>