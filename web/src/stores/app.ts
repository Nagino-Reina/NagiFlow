/**
 * stores/app.js
 * Global application state: snackbar notifications, drawer, etc.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  // ── Navigation drawer ──────────────────────────────────────────────────
  const drawerOpen = ref(true)

  function toggleDrawer() { drawerOpen.value = !drawerOpen.value }

  // ── Snackbar ───────────────────────────────────────────────────────────
  const snackbar = ref({
    show:    false,
    text:    '',
    color:   'success',
    timeout: 3500,
  })

  function notify(text, color = 'success', timeout = 3500) {
    snackbar.value = { show: true, text, color, timeout }
  }

  function notifyError(err) {
    const msg =
      err?.response?.data?.detail ??
      err?.message ??
      'An unexpected error occurred.'
    notify(msg, 'error', 5000)
  }

  // ── Confirm dialog ─────────────────────────────────────────────────────
  const confirm = ref({
    show:    false,
    title:   '',
    message: '',
    resolve: null,
  })

  function showConfirm(title, message) {
    return new Promise((resolve) => {
      confirm.value = { show: true, title, message, resolve }
    })
  }

  function resolveConfirm(value) {
    confirm.value.resolve?.(value)
    confirm.value.show = false
  }

  return {
    drawerOpen, toggleDrawer,
    snackbar, notify, notifyError,
    confirm, showConfirm, resolveConfirm,
  }
})