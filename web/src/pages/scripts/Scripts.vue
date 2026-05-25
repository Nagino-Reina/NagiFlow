<template>
  <div>
    <!-- Header -->
    <div class="d-flex align-center mb-6">
      <div>
        <div class="text-h5 font-weight-bold">Scripts</div>
        <div class="text-caption text-medium-emphasis">Screenplay editor — scenes, dialogue lines, TTS generation</div>
      </div>
      <v-spacer />
      <v-btn color="primary" prepend-icon="mdi-plus" @click="showCreate = true">
        New Script
      </v-btn>
    </div>

    <!-- Script cards -->
    <v-row v-if="scripts.length">
      <v-col v-for="s in scripts" :key="s.id" cols="12" sm="6" md="4">
        <v-card
          class="glass-card h-100"
          @click="router.push({ name: 'script-editor', params: { id: s.id } })"
          style="cursor:pointer;"
        >
          <v-card-title class="font-weight-semibold pt-4 pb-1">{{ s.title }}</v-card-title>
          <v-card-subtitle class="pb-3">{{ s.description || 'No description' }}</v-card-subtitle>
          <v-card-actions class="pt-0">
            <v-btn size="small" variant="text" :to="{ name: 'script-editor', params: { id: s.id } }">
              Open Editor
            </v-btn>
            <v-spacer />
            <v-btn size="small" icon variant="text" color="error" @click.stop="confirmDelete(s)">
              <v-icon size="18">mdi-delete-outline</v-icon>
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-empty-state
      v-else-if="!loading"
      icon="mdi-script-text-outline"
      title="No scripts yet"
      text="Create your first screenplay to get started."
    />

    <div v-if="loading" class="d-flex justify-center py-12">
      <v-progress-circular indeterminate color="primary" />
    </div>

    <!-- Create dialog -->
    <v-dialog v-model="showCreate" max-width="480">
      <v-card class="glass-bright">
        <v-card-title class="pt-5 px-6">New Script</v-card-title>
        <v-card-text class="px-6">
          <v-text-field v-model="form.title" label="Title" variant="outlined" density="compact" autofocus />
          <v-textarea v-model="form.description" label="Description" variant="outlined" density="compact" rows="3" />
        </v-card-text>
        <v-card-actions class="px-6 pb-5">
          <v-spacer />
          <v-btn variant="text" @click="showCreate = false">Cancel</v-btn>
          <v-btn color="primary" :loading="saving" @click="createScript">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete confirm -->
    <v-dialog v-model="showDelete" max-width="380">
      <v-card class="glass-bright">
        <v-card-title class="pt-5 px-6">Delete Script?</v-card-title>
        <v-card-text class="px-6">
          This will permanently delete "<strong>{{ deleteTarget?.title }}</strong>" and all its scenes and lines.
        </v-card-text>
        <v-card-actions class="px-6 pb-5">
          <v-spacer />
          <v-btn variant="text" @click="showDelete = false">Cancel</v-btn>
          <v-btn color="error" :loading="deleting" @click="deleteScript">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { scriptsApi } from '@/api'

const router = useRouter()

const scripts = ref([])
const loading = ref(false)
const saving  = ref(false)
const deleting = ref(false)

const showCreate = ref(false)
const showDelete = ref(false)
const deleteTarget = ref(null)

const form = ref({ title: '', description: '' })

async function load() {
  loading.value = true
  try {
    const { data } = await scriptsApi.list()
    scripts.value = data
  } finally {
    loading.value = false
  }
}

async function createScript() {
  if (!form.value.title.trim()) return
  saving.value = true
  try {
    const { data } = await scriptsApi.create(form.value)
    scripts.value.unshift(data)
    showCreate.value = false
    form.value = { title: '', description: '' }
    router.push({ name: 'script-editor', params: { id: data.id } })
  } finally {
    saving.value = false
  }
}

function confirmDelete(s) {
  deleteTarget.value = s
  showDelete.value = true
}

async function deleteScript() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await scriptsApi.delete(deleteTarget.value.id)
    scripts.value = scripts.value.filter(s => s.id !== deleteTarget.value.id)
    showDelete.value = false
  } finally {
    deleting.value = false
  }
}

onMounted(load)
</script>
