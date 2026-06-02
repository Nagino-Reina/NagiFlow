<template>
  <div class="d-flex align-center ga-2 flex-grow-1">
    <v-btn
      :aria-label="playing ? t('scripts.editor.pauseAudio') : t('scripts.editor.play')"
      :disabled="!ready"
      :icon="playing ? 'mdi-pause' : 'mdi-play'"
      size="small"
      variant="text"
      @click="toggle"
    />

    <div ref="container" class="flex-grow-1" style="min-width: 120px; max-width: 420px;" />

    <span class="text-caption text-medium-emphasis" style="white-space: nowrap;">
      {{ fmt(current) }} / {{ fmt(duration) }}
    </span>
  </div>
</template>

<script lang="ts" setup>
  import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
  import { useI18n } from 'vue-i18n'
  import WaveSurfer from 'wavesurfer.js'

  const props = defineProps<{ url: string | null }>()
  const { t } = useI18n()

  const container = ref<HTMLElement | null>(null)
  const ready = ref(false)
  const playing = ref(false)
  const current = ref(0)
  const duration = ref(0)
  let ws: WaveSurfer | null = null

  function fmt (s: number): string {
    const m = Math.floor(s / 60)
    const sec = Math.floor(s % 60)
    return `${m}:${String(sec).padStart(2, '0')}`
  }

  function destroy () {
    ws?.destroy()
    ws = null
    ready.value = false
    playing.value = false
    current.value = 0
    duration.value = 0
  }

  function build () {
    destroy()
    if (!props.url || !container.value) return
    ws = WaveSurfer.create({
      container: container.value,
      url: props.url,
      height: 28,
      waveColor: '#bdbdbd',
      progressColor: '#7c4dff',
      cursorWidth: 1,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
    })
    ws.on('ready', () => {
      ready.value = true
      duration.value = ws?.getDuration() ?? 0
    })
    ws.on('timeupdate', (time: number) => {
      current.value = time
    })
    ws.on('play', () => {
      playing.value = true
    })
    ws.on('pause', () => {
      playing.value = false
    })
    ws.on('finish', () => {
      playing.value = false
    })
  }

  function toggle () {
    ws?.playPause()
  }

  onMounted(build)
  watch(() => props.url, build)
  onBeforeUnmount(destroy)
</script>
