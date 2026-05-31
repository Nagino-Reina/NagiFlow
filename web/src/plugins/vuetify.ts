/**
 * plugins/vuetify.ts
 *
 * Central Vuetify theme — NagiFlow brand palette (docs/12 §6.1, MD3 tokens).
 * Two themes (light/dark) from one token set; container / surface-container roles
 * are exposed as theme colors so chips, status, and UI extensions share them.
 * Framework documentation: https://vuetifyjs.com
 */

// Composables
import { createVuetify } from 'vuetify'
// Styles
import '@mdi/font/css/materialdesignicons.css'

import 'vuetify/styles'

const light = {
  dark: false,
  colors: {
    primary: '#6C4CE0', 'on-primary': '#FFFFFF',
    'primary-container': '#E7DEFF', 'on-primary-container': '#21005D',
    secondary: '#0E7C86', 'on-secondary': '#FFFFFF',
    'secondary-container': '#B8ECF1', 'on-secondary-container': '#00363B',
    tertiary: '#B0286B', 'on-tertiary': '#FFFFFF',
    'tertiary-container': '#FFD8E6', 'on-tertiary-container': '#3E0021',
    background: '#FCFBFF', surface: '#FCFBFF', 'on-surface': '#1B1B21',
    'surface-variant': '#E5E1EC', 'on-surface-variant': '#47464F',
    'surface-container-low': '#F6F3FB',
    'surface-container': '#F0EDF7',
    'surface-container-high': '#EAE7F2',
    error: '#BA1A1A', 'on-error': '#FFFFFF',
    warning: '#9A6B00', 'on-warning': '#FFFFFF',
    success: '#1E7D43', 'on-success': '#FFFFFF',
    info: '#1763C7', 'on-info': '#FFFFFF',
    outline: '#79767F', 'outline-variant': '#C9C5D4',
  },
}

const dark = {
  dark: true,
  colors: {
    primary: '#CFBCFF', 'on-primary': '#371E73',
    'primary-container': '#523FA0', 'on-primary-container': '#E7DEFF',
    secondary: '#54D6E2', 'on-secondary': '#00363B',
    'secondary-container': '#004F58', 'on-secondary-container': '#B8ECF1',
    tertiary: '#FFB0CE', 'on-tertiary': '#5E1138',
    'tertiary-container': '#7A2950', 'on-tertiary-container': '#FFD8E6',
    background: '#131318', surface: '#131318', 'on-surface': '#E5E1E9',
    'surface-variant': '#47464F', 'on-surface-variant': '#C9C5D4',
    'surface-container-low': '#1B1B21',
    'surface-container': '#1F1F25',
    'surface-container-high': '#2A2930',
    error: '#FFB4AB', 'on-error': '#690005',
    warning: '#F4C44C', 'on-warning': '#412D00',
    success: '#8BD6A0', 'on-success': '#003919',
    info: '#A9C7FF', 'on-info': '#002E69',
    outline: '#938F99', 'outline-variant': '#47464F',
  },
}

// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
export default createVuetify({
  theme: {
    defaultTheme: 'light',
    themes: { light, dark },
  },
  defaults: {
    global: { ripple: true },
    VCard: { rounded: 'md' },
    VBtn: { rounded: 'md' },
    VTextField: { variant: 'outlined', density: 'comfortable' },
    VSelect: { variant: 'outlined', density: 'comfortable' },
  },
})
