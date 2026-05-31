/**
 * plugins/i18n.ts
 *
 * vue-i18n with zh-Hant / en catalogs at parity (docs/12 §11). Backend returns stable
 * codes/keys; the SPA renders the localized string. Key convention: dot-namespaced
 * `area.screen.element`; `error.<code>` mirrors API error codes one-to-one (docs/05 §3).
 */

import { createI18n } from 'vue-i18n'
import en from '@/locales/en.json'
import zhHant from '@/locales/zh-Hant.json'

export const SUPPORTED_LOCALES = ['en', 'zh-Hant'] as const
export type AppLocale = (typeof SUPPORTED_LOCALES)[number]

const STORAGE_KEY = 'nf.locale'

function initialLocale (): AppLocale {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved && (SUPPORTED_LOCALES as readonly string[]).includes(saved)) {
    return saved as AppLocale
  }
  return navigator.language.startsWith('zh') ? 'zh-Hant' : 'en'
}

const i18n = createI18n({
  legacy: false,
  locale: initialLocale(),
  fallbackLocale: 'en',
  messages: {
    en,
    'zh-Hant': zhHant,
  },
})

export function persistLocale (locale: AppLocale): void {
  localStorage.setItem(STORAGE_KEY, locale)
}

export default i18n
