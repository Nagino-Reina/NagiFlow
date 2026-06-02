<template>
  <v-container class="py-12">
    <v-card class="mx-auto pa-2" :elevation="3" max-width="420">
      <v-card-title class="text-h6 pt-4">{{ t('auth.title') }}</v-card-title>
      <v-card-subtitle class="pb-2">{{ t('auth.noAccount') }}</v-card-subtitle>

      <v-tabs v-model="tab" color="primary" grow>
        <v-tab value="login">{{ t('auth.loginTab') }}</v-tab>
        <v-tab value="register">{{ t('auth.registerTab') }}</v-tab>
      </v-tabs>

      <v-card-text>
        <v-alert
          v-if="errorCode"
          class="mb-4"
          density="compact"
          :text="t(`error.${errorCode}`)"
          type="error"
          variant="tonal"
        />

        <v-form @submit.prevent="submit">
          <v-text-field
            v-model="username"
            autocomplete="username"
            :label="t('auth.username')"
            prepend-inner-icon="mdi-account-outline"
          />

          <v-text-field
            v-if="tab === 'register'"
            v-model="displayName"
            :label="t('auth.displayName')"
            prepend-inner-icon="mdi-card-account-details-outline"
          />

          <v-text-field
            v-model="password"
            :autocomplete="tab === 'register' ? 'new-password' : 'current-password'"
            :label="t('auth.password')"
            prepend-inner-icon="mdi-lock-outline"
            type="password"
          />

          <v-btn
            block
            class="mt-2"
            color="primary"
            :loading="busy"
            type="submit"
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
      await (tab.value === 'register'
        ? auth.register({
          username: username.value,
          password: password.value,
          display_name: displayName.value || undefined,
        })
        : auth.login({ username: username.value, password: password.value }))
      router.push('/')
    } catch (error) {
      errorCode.value = error instanceof ApiError ? error.code : 'generic'
    } finally {
      busy.value = false
    }
  }
</script>
