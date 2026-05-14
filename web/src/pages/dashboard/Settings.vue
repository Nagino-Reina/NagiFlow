<template>
  <v-row>
    <v-col cols="12" md="7">
      <!-- Profile -->
      <v-card class="glass mb-5" rounded="xl">
        <v-card-title class="d-flex align-center pa-5 pb-3 ga-2">
          <v-icon color="primary" size="20">mdi-account-circle-outline</v-icon>
          <span class="font-display text-h6">Profile</span>
        </v-card-title>
        <v-card-text class="pa-5 pt-2">
          <v-form ref="profileForm" @submit.prevent="saveProfile" validate-on="submit">
            <v-row dense>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="profile.username"
                  label="Username"
                  prepend-inner-icon="mdi-account-outline"
                  :rules="[rules.required, rules.username]"
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="profile.email"
                  label="Email"
                  type="email"
                  prepend-inner-icon="mdi-email-outline"
                  :rules="[rules.required, rules.email]"
                />
              </v-col>
            </v-row>
            <div class="d-flex justify-end mt-2">
              <v-btn type="submit" color="primary" variant="tonal" :loading="savingProfile"
                prepend-icon="mdi-content-save-outline">
                Save Profile
              </v-btn>
            </div>
          </v-form>
        </v-card-text>
      </v-card>

      <!-- Password -->
      <v-card class="glass mb-5" rounded="xl">
        <v-card-title class="d-flex align-center pa-5 pb-3 ga-2">
          <v-icon color="secondary" size="20">mdi-lock-outline</v-icon>
          <span class="font-display text-h6">Change Password</span>
        </v-card-title>
        <v-card-text class="pa-5 pt-2">
          <v-form ref="passwordForm" @submit.prevent="changePassword" validate-on="submit">
            <v-text-field
              v-model="pwForm.current_password"
              label="Current Password"
              type="password"
              prepend-inner-icon="mdi-lock-outline"
              :rules="[rules.required]"
              class="mb-3"
            />
            <v-text-field
              v-model="pwForm.new_password"
              label="New Password"
              type="password"
              prepend-inner-icon="mdi-lock-plus-outline"
              :rules="[rules.required, rules.password]"
              class="mb-3"
            />
            <v-text-field
              v-model="pwForm.confirm"
              label="Confirm New Password"
              type="password"
              prepend-inner-icon="mdi-lock-check-outline"
              :rules="[rules.required, v => v === pwForm.new_password || 'Passwords do not match.']"
              class="mb-4"
            />
            <div class="d-flex justify-end">
              <v-btn type="submit" color="secondary" variant="tonal" :loading="savingPw"
                prepend-icon="mdi-shield-check-outline">
                Update Password
              </v-btn>
            </div>
          </v-form>
        </v-card-text>
      </v-card>

      <!-- Danger zone -->
      <v-card class="glass" rounded="xl" style="border:1px solid rgba(244,63,94,0.2);">
        <v-card-title class="d-flex align-center pa-5 pb-3 ga-2">
          <v-icon color="error" size="20">mdi-alert-circle-outline</v-icon>
          <span class="font-display text-h6">Danger Zone</span>
        </v-card-title>
        <v-card-text class="pa-5 pt-2">
          <div class="d-flex align-center justify-space-between">
            <div>
              <div class="text-body-2 font-weight-medium">Sign out of all sessions</div>
              <div class="text-caption text-medium-emphasis">Revoke all active tokens.</div>
            </div>
            <v-btn color="error" variant="tonal" size="small" @click="auth.logout">
              Sign Out
            </v-btn>
          </div>
        </v-card-text>
      </v-card>
    </v-col>

    <!-- Right: account info -->
    <v-col cols="12" md="5">
      <v-card class="glass" rounded="xl" style="position:sticky;top:80px;">
        <v-card-text class="pa-6">
          <div class="d-flex flex-column align-center mb-6">
            <v-avatar
              size="80"
              color="surface-2"
              class="mb-4"
              style="outline:3px solid rgba(6,182,212,0.3);outline-offset:3px;"
            >
              <span class="font-display font-weight-bold text-h4" style="color:#06B6D4;">
                {{ userInitial }}
              </span>
            </v-avatar>
            <div class="font-display text-h6 font-weight-bold">{{ auth.user?.username }}</div>
            <div class="text-caption text-medium-emphasis">{{ auth.user?.email }}</div>
            <v-chip class="mt-2" size="small" :class="roleChipClass" >
              {{ auth.user?.role }}
            </v-chip>
          </div>
          <v-divider class="mb-4" />
          <div class="d-flex flex-column ga-3">
            <div class="d-flex justify-space-between align-center">
              <span class="text-caption text-medium-emphasis">User ID</span>
              <span class="text-caption font-mono text-truncate ml-4" style="max-width:180px;">
                {{ auth.user?.id }}
              </span>
            </div>
            <div class="d-flex justify-space-between align-center">
              <span class="text-caption text-medium-emphasis">Account status</span>
              <v-chip size="x-small" class="chip-emerald">Active</v-chip>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { usersApi } from '@/api'

const auth = useAuthStore()
const app  = useAppStore()

const profileForm = ref(null)
const passwordForm = ref(null)
const savingProfile = ref(false)
const savingPw      = ref(false)

const profile = reactive({ username: '', email: '' })
const pwForm  = reactive({ current_password: '', new_password: '', confirm: '' })

const userInitial = computed(() => (auth.user?.username ?? 'U').charAt(0).toUpperCase())
const roleChipClass = computed(() => ({
  admin: 'chip-pink', moderator: 'chip-violet', user: 'chip-cyan',
}[auth.user?.role] ?? 'chip-cyan'))

const rules = {
  required: v => !!v || 'Required.',
  email:    v => /.+@.+\..+/.test(v) || 'Invalid email.',
  username: v => /^[a-zA-Z0-9_-]{3,64}$/.test(v) || '3-64 chars, letters/numbers/_ only.',
  password: v => v.length >= 8 || 'At least 8 characters.',
}

async function saveProfile() {
  const { valid } = await profileForm.value.validate()
  if (!valid) return
  savingProfile.value = true
  try {
    await usersApi.updateMe({ username: profile.username, email: profile.email })
    await auth.fetchMe()
    app.notify('Profile updated.')
  } catch (err) { app.notifyError(err) }
  finally { savingProfile.value = false }
}

async function changePassword() {
  const { valid } = await passwordForm.value.validate()
  if (!valid) return
  savingPw.value = true
  try {
    await usersApi.changePassword({
      current_password: pwForm.current_password,
      new_password: pwForm.new_password,
    })
    Object.assign(pwForm, { current_password: '', new_password: '', confirm: '' })
    app.notify('Password updated.')
  } catch (err) { app.notifyError(err) }
  finally { savingPw.value = false }
}

onMounted(() => {
  profile.username = auth.user?.username ?? ''
  profile.email    = auth.user?.email    ?? ''
})
</script>