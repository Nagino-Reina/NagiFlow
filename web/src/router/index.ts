/**
 * router/index.ts
 *
 * Shell routes (docs/03 §3.4, docs/12 §4). Top-level destinations map to the nav rail;
 * the landing route is the guest chat. Module `nav.item` contributions register routes
 * dynamically in later phases. Guest-gating is handled in the shell (visible-but-gated).
 */

import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'landing', component: () => import('@/pages/index.vue') },
    { path: '/login', name: 'login', component: () => import('@/pages/login.vue') },
    { path: '/characters', name: 'characters', component: () => import('@/pages/characters.vue') },
    { path: '/characters/:id', name: 'character-editor', component: () => import('@/pages/character-editor.vue') },
    { path: '/scripts', name: 'scripts', component: () => import('@/pages/scripts.vue') },
    { path: '/live', name: 'live', component: () => import('@/pages/live.vue') },
    { path: '/dashboard', name: 'dashboard', component: () => import('@/pages/dashboard.vue') },
    { path: '/modules', name: 'modules', component: () => import('@/pages/modules.vue') },
    { path: '/settings', name: 'settings', component: () => import('@/pages/settings.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

export default router
