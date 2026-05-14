<template>
  <div class="auth-bg d-flex align-center justify-center" style="min-height:100vh;">
    <!-- Ambient blobs -->
    <div class="blob blob-1" />
    <div class="blob blob-2" />
    <div class="blob blob-3" />

    <v-card class="auth-card glass-glow" width="420" rounded="2xl">
      <!-- Logo header -->
      <div class="d-flex flex-column align-center pt-8 pb-4">
        <div class="logo-gem mb-4" />
        <div class="font-display gradient-text" style="font-size:1.6rem;font-weight:700;">NagiFlow</div>
        <div class="text-caption text-medium-emphasis mt-1" style="letter-spacing:.1em;">
          AI VTUBER FRAMEWORK
        </div>
      </div>

      <v-card-text class="px-8 pb-6">
        <div class="text-h6 font-display mb-6 text-center">Sign in to your account</div>

        <v-form ref="formRef" @submit.prevent="submit" validate-on="submit">
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
            :rules="[rules.required]"
            class="mb-6"
          />

          <v-btn
            type="submit"
            color="primary"
            block
            size="large"
            :loading="auth.loading"
            class="glow-cyan"
            style="font-family:var(--font-display);letter-spacing:.01em;"
          >
            Sign In
          </v-btn>
        </v-form>

        <v-alert
          v-if="error"
          :text="error"
          color="error"
          variant="tonal"
          class="mt-4"
          density="compact"
          prepend-icon="mdi-alert-circle"
        />

        <div class="text-center mt-6 text-body-2 text-medium-emphasis">
          Don't have an account?
          <router-link :to="{ name: 'register' }" class="text-primary font-weight-medium text-decoration-none">
            Register
          </router-link>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth   = useAuthStore()
const formRef = ref(null)
const showPw  = ref(false)
const error   = ref('')

const form = reactive({ email: '', password: '' })

const rules = {
  required: v => !!v || 'This field is required.',
  email:    v => /.+@.+\..+/.test(v) || 'Enter a valid email.',
}

async function submit() {
  const { valid } = await formRef.value.validate()
  if (!valid) return
  error.value = ''
  try {
    await auth.login(form)
  } catch (err) {
    error.value = err?.response?.data?.detail ?? 'Login failed. Please try again.'
  }
}
</script>

<style scoped>
.auth-bg {
  background: #070B16;
  position: relative;
  overflow: hidden;
}

.logo-gem {
  width: 56px; height: 56px;
  background: linear-gradient(135deg, #06B6D4 0%, #8B5CF6 50%, #EC4899 100%);
  border-radius: 16px;
  box-shadow: 0 0 32px rgba(6,182,212,0.5);
}

.auth-card { position: relative; z-index: 1; }

/* Ambient blobs */
.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  pointer-events: none;
  opacity: 0.18;
}
.blob-1 {
  width: 400px; height: 400px;
  background: radial-gradient(circle, #06B6D4, transparent);
  top: -100px; left: -100px;
}
.blob-2 {
  width: 350px; height: 350px;
  background: radial-gradient(circle, #EC4899, transparent);
  bottom: -80px; right: -80px;
}
.blob-3 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, #8B5CF6, transparent);
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
}
</style>