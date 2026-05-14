<template>
  <div class="auth-bg d-flex align-center justify-center" style="min-height:100vh;">
    <div class="blob blob-1" />
    <div class="blob blob-2" />

    <v-card class="glass-glow" width="440" rounded="2xl">
      <div class="d-flex flex-column align-center pt-8 pb-4">
        <div class="logo-gem mb-4" />
        <div class="font-display gradient-text" style="font-size:1.6rem;font-weight:700;">Create Account</div>
        <div class="text-caption text-medium-emphasis mt-1">Join NagiFlow today</div>
      </div>

      <v-card-text class="px-8 pb-8">
        <v-form ref="formRef" @submit.prevent="submit" validate-on="submit">
          <v-text-field
            v-model="form.username"
            label="Username"
            prepend-inner-icon="mdi-account-outline"
            :rules="[rules.required, rules.username]"
            class="mb-3"
          />
          <v-text-field
            v-model="form.email"
            label="Email"
            type="email"
            prepend-inner-icon="mdi-email-outline"
            :rules="[rules.required, rules.email]"
            class="mb-3"
          />
          <v-text-field
            v-model="form.password"
            label="Password"
            :type="showPw ? 'text' : 'password'"
            prepend-inner-icon="mdi-lock-outline"
            :append-inner-icon="showPw ? 'mdi-eye-off' : 'mdi-eye'"
            @click:append-inner="showPw = !showPw"
            :rules="[rules.required, rules.password]"
            class="mb-3"
          />
          <v-text-field
            v-model="form.confirm"
            label="Confirm Password"
            :type="showPw ? 'text' : 'password'"
            prepend-inner-icon="mdi-lock-check-outline"
            :rules="[rules.required, rules.match]"
            class="mb-6"
          />

          <v-btn
            type="submit"
            color="primary"
            block
            size="large"
            :loading="loading"
            class="glow-cyan"
            style="font-family:var(--font-display);"
          >
            Create Account
          </v-btn>
        </v-form>

        <v-alert v-if="error" :text="error" color="error" variant="tonal" class="mt-4" density="compact" />
        <v-alert v-if="success" text="Account created! Redirecting to login…" color="success" variant="tonal" class="mt-4" density="compact" />

        <div class="text-center mt-6 text-body-2 text-medium-emphasis">
          Already have an account?
          <router-link :to="{ name: 'login' }" class="text-primary font-weight-medium text-decoration-none">
            Sign In
          </router-link>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router  = useRouter()
const auth    = useAuthStore()
const formRef = ref(null)
const showPw  = ref(false)
const loading = ref(false)
const error   = ref('')
const success = ref(false)

const form = reactive({ username: '', email: '', password: '', confirm: '' })

const rules = {
  required: v => !!v || 'Required.',
  email:    v => /.+@.+\..+/.test(v) || 'Invalid email.',
  username: v => /^[a-zA-Z0-9_-]{3,64}$/.test(v) || 'Letters, numbers, _ or - (3–64 chars).',
  password: v => v.length >= 8 || 'At least 8 characters.',
  match:    v => v === form.password || 'Passwords do not match.',
}

async function submit() {
  const { valid } = await formRef.value.validate()
  if (!valid) return
  error.value = ''
  loading.value = true
  try {
    await auth.register({ username: form.username, email: form.email, password: form.password })
    success.value = true
    setTimeout(() => router.push({ name: 'login' }), 1500)
  } catch (err) {
    error.value = err?.response?.data?.detail ?? 'Registration failed.'
  } finally { loading.value = false }
}
</script>

<style scoped>
.auth-bg { background: #070B16; position: relative; overflow: hidden; }
.logo-gem { width:56px;height:56px;background:linear-gradient(135deg,#06B6D4,#8B5CF6,#EC4899);border-radius:16px;box-shadow:0 0 32px rgba(6,182,212,0.5); }
.blob { position:absolute;border-radius:50%;filter:blur(80px);pointer-events:none;opacity:.16; }
.blob-1 { width:450px;height:450px;background:radial-gradient(circle,#8B5CF6,transparent);top:-120px;right:-80px; }
.blob-2 { width:350px;height:350px;background:radial-gradient(circle,#EC4899,transparent);bottom:-80px;left:-60px; }
</style>