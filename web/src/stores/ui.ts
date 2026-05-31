/**
 * stores/ui.ts
 *
 * Shell UI state: theme (light/dark), active locale, and nav drawer. Theme + locale
 * persist to localStorage so a reload keeps the creator's choices (docs/12 §5/§6/§11).
 */

import { defineStore } from 'pinia'
import { persistLocale, SUPPORTED_LOCALES, type AppLocale } from '@/plugins/i18n'

const THEME_KEY = 'nf.theme'
export type ThemeName = 'light' | 'dark'

function initialTheme (): ThemeName {
  const saved = localStorage.getItem(THEME_KEY)
  if (saved === 'light' || saved === 'dark') return saved
  return matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export const useUiStore = defineStore('ui', {
  state: () => ({
    theme: initialTheme() as ThemeName,
    locale: 'en' as AppLocale,
    drawer: true,
  }),
  actions: {
    setTheme (theme: string) {
      if (theme !== 'light' && theme !== 'dark') return
      this.theme = theme
      localStorage.setItem(THEME_KEY, theme)
    },
    toggleTheme () {
      this.setTheme(this.theme === 'light' ? 'dark' : 'light')
    },
    setLocale (locale: string) {
      if (!(SUPPORTED_LOCALES as readonly string[]).includes(locale)) return
      this.locale = locale as AppLocale
      persistLocale(locale as AppLocale)
    },
    toggleDrawer () {
      this.drawer = !this.drawer
    },
  },
})
