<template>
  <v-app>
    <v-app-bar :elevation="2" color="surface-container-low">
      <v-app-bar-nav-icon :aria-label="t('shell.toggleNav')" @click="ui.toggleDrawer()" />

      <v-app-bar-title class="font-weight-bold text-primary">
        {{ t('app.name') }}
      </v-app-bar-title>

      <v-spacer />

      <!-- Locale switch (zh-Hant / en) -->
      <v-menu>
        <template #activator="{ props }">
          <v-btn icon="mdi-translate" :aria-label="t('shell.language')" v-bind="props" />
        </template>
        <v-list density="compact">
          <v-list-item
            v-for="loc in SUPPORTED_LOCALES"
            :key="loc"
            :active="ui.locale === loc"
            :title="localeLabel(loc)"
            @click="ui.setLocale(loc)"
          />
        </v-list>
      </v-menu>

      <!-- Theme toggle -->
      <v-btn
        :icon="ui.theme === 'dark' ? 'mdi-weather-night' : 'mdi-weather-sunny'"
        :aria-label="t('shell.toggleTheme')"
        @click="ui.toggleTheme()"
      />

      <!-- Principal menu -->
      <v-menu>
        <template #activator="{ props }">
          <v-btn icon="mdi-account-circle-outline" :aria-label="t('shell.account')" v-bind="props" />
        </template>
        <v-list density="compact" min-width="200">
          <v-list-item
            :subtitle="auth.isUser ? auth.principal?.username ?? '' : t('shell.guest')"
            :title="auth.principal?.display_name ?? t('shell.account')"
          />
          <v-divider />
          <template v-if="auth.isUser">
            <v-list-item
              prepend-icon="mdi-logout"
              :title="t('common.action.logout')"
              @click="auth.logout()"
            />
          </template>
          <template v-else>
            <v-list-item
              prepend-icon="mdi-login"
              :title="t('shell.registerOrLogin')"
              :subtitle="t('shell.accountHint')"
              to="/login"
            />
          </template>
        </v-list>
      </v-menu>
    </v-app-bar>

    <v-navigation-drawer v-model="ui.drawer" color="surface-container-low">
      <v-list nav density="comfortable">
        <v-list-item
          v-for="dest in NAV_DESTINATIONS"
          :key="dest.to"
          :prepend-icon="dest.icon"
          :title="t(dest.i18nKey)"
          :active="route.path === dest.to"
          @click="navigate(dest)"
        >
          <template v-if="isGated(dest)" #append>
            <v-icon icon="mdi-lock-outline" size="x-small" :aria-label="t('shell.loginRequired')" />
          </template>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <router-view />
    </v-main>

    <SystemBar v-if="auth.isUser" />
  </v-app>
</template>

<script lang="ts" setup>
  import { onMounted, watch } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useRoute, useRouter } from 'vue-router'
  import { useTheme } from 'vuetify'
  import SystemBar from '@/components/SystemBar.vue'
  import { SUPPORTED_LOCALES, type AppLocale } from '@/plugins/i18n'
  import { NAV_DESTINATIONS, type NavDestination } from '@/shell/navigation'
  import { useAuthStore } from '@/stores/auth'
  import { useUiStore } from '@/stores/ui'

  const { t, locale } = useI18n()
  const route = useRoute()
  const router = useRouter()
  const theme = useTheme()
  const ui = useUiStore()
  const auth = useAuthStore()

  // Reflect the i18n-resolved initial locale into the store, then keep them in sync.
  ui.locale = locale.value as AppLocale
  watch(() => ui.locale, value => { locale.value = value }, { immediate: true })

  // Drive the Vuetify theme from the store.
  watch(() => ui.theme, value => { theme.global.name.value = value }, { immediate: true })

  const localeLabel = (loc: AppLocale) => (loc === 'zh-Hant' ? '繁體中文' : 'English')

  const isGated = (dest: NavDestination) => dest.requiresUser && !auth.isUser

  function navigate (dest: NavDestination) {
    router.push(isGated(dest) ? '/login' : dest.to)
  }

  onMounted(() => {
    auth.ensureSession()
  })
</script>
