<template>
  <div class="bubble-enter d-flex ga-3" :class="isUser ? 'flex-row-reverse' : 'flex-row'">
    <!-- Avatar -->
    <v-avatar v-if="!isUser" size="28" color="surface-2" class="flex-shrink-0 mt-1">
      <span class="font-display font-weight-bold text-primary" style="font-size:11px;">
        {{ (charName ?? 'A').charAt(0) }}
      </span>
    </v-avatar>

    <div style="max-width:72%;">
      <!-- Bubble -->
      <div
        class="bubble pa-3 px-4 rounded-xl text-body-2"
        :class="[isUser ? 'bubble--user rounded-tr-sm' : 'bubble--assistant rounded-tl-sm']"
        style="white-space:pre-wrap;word-break:break-word;line-height:1.65;"
      >
        {{ message.content }}<span v-if="streaming" class="cursor-blink">▋</span>
      </div>

      <!-- Audio playback -->
      <div v-if="message.audio_url" class="mt-1 d-flex align-center ga-2">
        <v-btn
          icon
          size="x-small"
          variant="text"
          color="primary"
          @click="playAudio"
        >
          <v-icon size="16">{{ playing ? 'mdi-pause' : 'mdi-play' }}</v-icon>
        </v-btn>
        <span class="text-caption text-medium-emphasis">Audio</span>
      </div>

      <!-- Timestamp -->
      <div
        class="text-caption mt-1"
        style="opacity:.35;font-size:10px;"
        :class="isUser ? 'text-right' : 'text-left'"
      >
        {{ formattedTime }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  message:  { type: Object,  required: true },
  charName: { type: String,  default: 'A'   },
  streaming:{ type: Boolean, default: false  },
})

const isUser = computed(() => props.message.role === 'user')
const playing = ref(false)
let audio = null

const formattedTime = computed(() => {
  if (!props.message.created_at) return ''
  return new Date(props.message.created_at).toLocaleTimeString(undefined, {
    hour: '2-digit', minute: '2-digit',
  })
})

async function playAudio() {
  if (playing.value && audio) {
    audio.pause()
    playing.value = false
    return
  }
  const token = localStorage.getItem('access_token')
  const resp  = await fetch(props.message.audio_url, {
    headers: { Authorization: `Bearer ${token}` },
  })
  const blob = await resp.blob()
  const url  = URL.createObjectURL(blob)
  audio = new Audio(url)
  audio.onended = () => { playing.value = false }
  audio.play()
  playing.value = true
}
</script>

<style scoped>
.bubble {
  line-height: 1.65;
  position: relative;
}
.bubble--user {
  background: linear-gradient(135deg, rgba(6,182,212,0.25), rgba(139,92,246,0.18));
  border: 1px solid rgba(6,182,212,0.25);
  color: #E2E8F0;
}
.bubble--assistant {
  background: rgba(26, 35, 56, 0.85);
  border: 1px solid rgba(255,255,255,0.07);
  color: #CBD5E1;
}

@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
.cursor-blink {
  animation: blink 0.9s step-end infinite;
  color: #06B6D4;
  font-size: 14px;
}
</style>