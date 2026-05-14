/**
 * stores/auth.js
 * Pinia store for authentication state.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  // ── State ──────────────────────────────────────────────────────────────
  const user          = ref(null)
  const accessToken   = ref(localStorage.getItem('access_token') ?? null)
  const refreshToken  = ref(localStorage.getItem('refresh_token') ?? null)
  const loading       = ref(false)

  // ── Getters ────────────────────────────────────────────────────────────
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const isAdmin         = computed(() => user.value?.role === 'admin')
  const isModerator     = computed(() => ['admin', 'moderator'].includes(user.value?.role))

  // ── Actions ────────────────────────────────────────────────────────────
  function _persist(access, refresh) {
    accessToken.value  = access
    refreshToken.value = refresh
    localStorage.setItem('access_token',  access)
    localStorage.setItem('refresh_token', refresh)
  }

  async function register(payload) {
    loading.value = true
    try {
      const { data } = await authApi.register(payload)
      return data
    } finally { loading.value = false }
  }

  async function login(payload) {
    loading.value = true
    try {
      const { data } = await authApi.login(payload)
      _persist(data.access_token, data.refresh_token)
      await fetchMe()
      router.push({ name: 'dashboard' })
    } finally { loading.value = false }
  }

  async function fetchMe() {
    const { data } = await authApi.me()
    user.value = data
  }

  async function logout() {
    user.value          = null
    accessToken.value   = null
    refreshToken.value  = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    router.push({ name: 'login' })
  }

  // Restore session on page reload
  async function restoreSession() {
    if (!accessToken.value) return
    try { await fetchMe() }
    catch { await logout() }
  }

  // Listen for forced logout from Axios interceptor
  window.addEventListener('auth:logout', logout)

  return {
    user, accessToken, refreshToken, loading,
    isAuthenticated, isAdmin, isModerator,
    register, login, logout, fetchMe, restoreSession,
  }
})