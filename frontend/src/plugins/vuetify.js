import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'

const lightTheme = {
  dark: false,
  colors: {
    background: '#F8FAFC',
    surface: '#FFFFFF',
    primary: '#0066FF',
    secondary: '#64748B',
    accent: '#FF6B35',
    error: '#EF4444',
    info: '#3B82F6',
    success: '#10B981',
    warning: '#F59E0B',
  },
}

const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: { mdi },
  },
  theme: {
    defaultTheme: 'light',
    themes: {
      light: lightTheme,
    },
  },
  defaults: {
    VBtn: {
      variant: 'flat',
      density: 'comfortable',
      rounded: 'lg',
    },
    VCard: {
      variant: 'flat',
      density: 'comfortable',
      rounded: 'xl',
      elevation: 1,
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
      rounded: 'lg',
    },
    VSelect: {
      variant: 'outlined',
      density: 'comfortable',
      rounded: 'lg',
    },
    VSlider: {
      density: 'comfortable',
    },
    VDialog: {
      transition: 'scale-transition',
    },
    VList: {
      density: 'comfortable',
    },
    VAppBar: {
      elevation: 1,
      rounded: 'none',
    },
  },
  styles: {
    config: {
      preflight: true,
    },
  },
})

export default vuetify
