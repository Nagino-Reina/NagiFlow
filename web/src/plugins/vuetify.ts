/**
 * plugins/vuetify.ts
 *
 * Framework documentation: https://vuetifyjs.com`
 */

// Composables
import { createVuetify } from 'vuetify'
// Styles
import '@mdi/font/css/materialdesignicons.css'

import 'vuetify/styles'


const neonStudio = {
  dark: true,
  colors: {
    // Base palette
    background:  '#080C18',
    surface:     '#0E1425',
    'surface-1': '#141B2E',
    'surface-2': '#1A2338',

    // Brand
    primary:    '#06B6D4',   // Cyan
    secondary:  '#EC4899',   // Pink
    accent:     '#8B5CF6',   // Purple
    tertiary:   '#10B981',   // Emerald

    // Semantic
    success: '#10B981',
    warning: '#F59E0B',
    error:   '#EF4444',
    info:    '#3B82F6',

    // Text
    'on-background': '#E2E8F0',
    'on-surface':    '#CBD5E1',
  },
}

// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
export default createVuetify({
  theme: {
    defaultTheme: 'neonStudio',
    themes: { neonStudio },
  },
  defaults: {
    VBtn: {
      rounded: 'lg',
      fontWeight: '500',
    },
    VCard: {
      rounded: 'xl',
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
      rounded: 'lg',
      color: 'primary',
    },
    VTextarea: {
      variant: 'outlined',
      density: 'comfortable',
      rounded: 'lg',
      color: 'primary',
    },
    VSelect: {
      variant: 'outlined',
      density: 'comfortable',
      rounded: 'lg',
      color: 'primary',
    },
    VChip: {
      rounded: 'lg',
    },
    VAlert: {
      rounded: 'xl',
    },
    VSnackbar: {
      rounded: 'xl',
    },
  },
  icons: {
    defaultSet: 'mdi',
  },
})
