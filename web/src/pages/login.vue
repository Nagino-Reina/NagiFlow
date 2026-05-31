<template>
  <v-container class="py-12">
    <v-card class="mx-auto pa-2" max-width="420" :elevation="3">
      <v-card-title class="text-h6 pt-4">{{ t('auth.title') }}</v-card-title>
      <v-card-subtitle class="pb-2">{{ t('auth.noAccount') }}</v-card-subtitle>

      <v-tabs v-model="tab" color="primary" grow>
        <v-tab value="login">{{ t('auth.loginTab') }}</v-tab>
        <v-tab value="register">{{ t('auth.registerTab') }}</v-tab>
      </v-tabs>

      <v-card-text>
        <v-alert
          v-if="errorCode"
          type="error"
          variant="tonal"
          density="compact"
          class="mb-4"
          :text="t(`error.${errorCode}`)"
        />

        <v-form @submit.prevent="submit">
          <v-text-field
            v-model="username"
            :label="t('auth.username')"
            prepend-inner-icon="mdi-account-outline"
            autocomplete="username"
          />
          <v-text-field
            v-if="tab === 'register'"
            v-model="displayName"
            :label="t('auth.displayName')"
            prepend-inner-icon="mdi-card-account-details-outline"
          />
          <v-text-field
            v-model="password"
            :label="t('auth.password')"
            type="password"
            prepend-inner-icon="mdi-lock-outline"
            :autocomplete="tab === 'register' ? 'new-password' : 'current-password'"
          />

          <v-btn
            type="submit"
            color="primary"
            block
            class="mt-2"
            :loading="busy"
          >
            {{ tab === 'register' ? t('common.action.register') : t('common.action.login') }}
          </v-btn>
        </v-form>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script lang="ts" setup>
  import { ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useRouter } from 'vue-router'
  import { ApiError } from '@/api/http'
  import { useAuthStore } from '@/stores/auth'

  const { t } = useI18n()
  const router = useRouter()
  const auth = useAuthStore()

  const tab = ref<'login' | 'register'>('login')
  const username = ref('')
  const password = ref('')
  const displayName = ref('')
  const busy = ref(false)
  const errorCode = ref<string | null>(null)

  async function submit () {
    busy.value = true
    errorCode.value = null
    try {
      if (tab.value === 'register') {
        await auth.register({
          username: username.value,
          password: password.value,
          display_name: displayName.value || undefined,
        })
      } else {
        await auth.login({ username: username.value, password: password.value })
      }
      router.push('/')
    } catch (error) {
      errorCode.value = error instanceof ApiError ? error.code : 'generic'
    } finally {
      busy.value = false
    }
  }
</script>
