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
    { path: '/', redirect: '/chat' },
    { path: '/chat', name: 'chat', component: () => import('@/pages/chat.vue') },
    { path: '/login', name: 'login', component: () => import('@/pages/login.vue') },
    { path: '/characters', name: 'characters', component: () => import('@/pages/characters.vue') },
    { path: '/characters/:id', name: 'character-editor', component: () => import('@/pages/character-editor.vue') },
    { path: '/scripts', name: 'scripts', component: () => import('@/pages/scripts.vue') },
    { path: '/scripts/:id', name: 'script-editor', component: () => import('@/pages/script-editor.vue') },
    { path: '/settings', name: 'settings', component: () => import('@/pages/settings.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

export default router
