/**
 * router/index.js
 *
 * Route map:
 *
 *   /login                  – Login page (guest only)
 *   /register               – Register page (guest only)
 *   /                       – Dashboard
 *   /characters             – Character list
 *   /characters/new         – Create character
 *   /characters/:id         – Character detail / edit
 *   /characters/:id/chat    – Chat with character
 *   /conversations          – All conversations
 *   /knowledge              – Knowledge base
 *   /skills                 – Skills library
 *   /settings               – Account settings
 *   /admin                  – Admin panel (admin role)
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    // ── Guest-only ──────────────────────────────────────────────────────
    {
      path: '/login',
      name: 'login',
      component: () => import('@/pages/auth/Login.vue'),
      meta: { guest: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/pages/auth/Register.vue'),
      meta: { guest: true },
    },

    // ── App shell (authenticated) ────────────────────────────────────────
    {
      path: '/',
      component: () => import('@/components/layout/AppShell.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/pages/dashboard/Dashboard.vue'),
        },

        // Characters
        {
          path: 'characters',
          name: 'characters',
          component: () => import('@/pages/characters/CharacterList.vue'),
        },
        {
          path: 'characters/new',
          name: 'character-create',
          component: () => import('@/pages/characters/CharacterForm.vue'),
        },
        {
          path: 'characters/:id',
          name: 'character-detail',
          component: () => import('@/pages/characters/CharacterDetail.vue'),
        },
        {
          path: 'characters/:id/edit',
          name: 'character-edit',
          component: () => import('@/pages/characters/CharacterForm.vue'),
        },

        // Chat
        {
          path: 'characters/:id/chat',
          name: 'character-chat',
          component: () => import('@/pages/chat/Chat.vue'),
        },

        // Conversations
        {
          path: 'conversations',
          name: 'conversations',
          component: () => import('@/pages/chat/Conversations.vue'),
        },

        // Knowledge base
        {
          path: 'knowledge',
          name: 'knowledge',
          component: () => import('@/pages/knowledge/Knowledge.vue'),
        },

        // Skills library
        {
          path: 'skills',
          name: 'skills',
          component: () => import('@/pages/skills/Skills.vue'),
        },

        // Account settings
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/pages/dashboard/Settings.vue'),
        },

        // Scripts
        {
          path: 'scripts',
          name: 'scripts',
          component: () => import('@/pages/scripts/Scripts.vue'),
        },
        {
          path: 'scripts/:id',
          name: 'script-editor',
          component: () => import('@/pages/scripts/ScriptEditor.vue'),
        },

        // Training
        {
          path: 'training',
          name: 'training',
          component: () => import('@/pages/training/Training.vue'),
        },

        // Admin
        {
          path: 'admin',
          name: 'admin',
          component: () => import('@/pages/admin/Admin.vue'),
          meta: { requiresAdmin: true },
        },
      ],
    },

    // Catch-all
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

// ── Navigation guards ────────────────────────────────────────────────────────
router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // Restore session on first load
  if (!auth.user && auth.accessToken) {
    await auth.restoreSession()
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.guest && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }

  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return { name: 'dashboard' }
  }
})

export default router