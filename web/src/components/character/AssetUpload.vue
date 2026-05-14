<template>
  <div
    class="upload-zone rounded-xl pa-4 d-flex align-center ga-3"
    :class="{ 'drag-over': dragging }"
    @dragover.prevent="dragging = true"
    @dragleave="dragging = false"
    @drop.prevent="onDrop"
    @click="inputRef.click()"
  >
    <div class="upload-icon d-flex align-center justify-center rounded-lg flex-shrink-0" :style="{ background: `rgba(${colorRgb},0.12)` }">
      <v-icon :icon="icon" :color="color" size="22" />
    </div>
    <div class="flex-1 overflow-hidden">
      <div class="text-body-2 font-weight-medium">{{ label }}</div>
      <div class="text-caption text-medium-emphasis text-truncate">
        {{ current ? `Current: …/${current.split('/').pop()}` : 'Click or drag to upload' }}
      </div>
    </div>
    <v-chip v-if="fileName" size="x-small" :color="color" variant="tonal" class="flex-shrink-0">
      {{ fileName }}
    </v-chip>
    <v-btn v-if="fileName" icon="mdi-upload" size="small" :color="color" variant="flat" @click.stop="doUpload" :loading="uploading" />
    <input ref="inputRef" type="file" :accept="accept" class="d-none" @change="onFileChange" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  label:   String,
  icon:    String,
  accept:  String,
  color:   { type: String, default: 'primary' },
  current: String,
})
const emit = defineEmits(['upload'])

const inputRef  = ref(null)
const file      = ref(null)
const dragging  = ref(false)
const uploading = ref(false)

const fileName = computed(() => file.value?.name ?? '')

const colorRgbMap = { primary: '6,182,212', secondary: '236,72,153', accent: '139,92,246' }
const colorRgb    = computed(() => colorRgbMap[props.color] ?? '6,182,212')

function onFileChange(e) {
  file.value = e.target.files[0] ?? null
}
function onDrop(e) {
  dragging.value = false
  file.value = e.dataTransfer.files[0] ?? null
}
async function doUpload() {
  if (!file.value) return
  uploading.value = true
  try { emit('upload', file.value); file.value = null }
  finally { uploading.value = false }
}
</script>

<style scoped>
.upload-zone {
  border: 1px dashed rgba(255,255,255,0.12);
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  &:hover, &.drag-over {
    border-color: rgba(6,182,212,0.5);
    background: rgba(6,182,212,0.04);
  }
}
.upload-icon { width:40px;height:40px; }
</style>