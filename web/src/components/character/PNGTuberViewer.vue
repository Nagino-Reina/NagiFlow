<template>
  <div
    class="pngtuber-root"
    :style="{ width: size + 'px', height: size + 'px' }"
  >
    <transition name="pngtuber-fade" mode="out-in">
      <img
        v-if="assetUrl"
        :key="assetUrl"
        :src="assetUrl"
        class="pngtuber-img"
        :class="{ 'pngtuber-talking': effectiveState === 'talking' }"
        draggable="false"
      />
      <div v-else class="pngtuber-placeholder d-flex align-center justify-center">
        <v-icon size="48" color="rgba(255,255,255,0.2)">mdi-account-circle-outline</v-icon>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  characterId:        { type: String,  default: null },
  currentState:       { type: String,  default: 'idle' },     // 'idle' | 'talking'
  currentExpression:  { type: String,  default: 'default' },
  size:               { type: Number,  default: 300 },
  baseUrl:            { type: String,  default: '/api/v1' },
})

// Autonomous blink timer
const blinking = ref(false)
let blinkTimer = null

function scheduleNextBlink() {
  const delay = 3000 + Math.random() * 4000   // 3–7 s
  blinkTimer = setTimeout(() => {
    if (props.currentState !== 'talking') {
      blinking.value = true
      setTimeout(() => {
        blinking.value = false
        scheduleNextBlink()
      }, 200)
    } else {
      scheduleNextBlink()
    }
  }, delay)
}

onMounted(scheduleNextBlink)
onBeforeUnmount(() => clearTimeout(blinkTimer))

// Effective state considers blink override
const effectiveState = computed(() => {
  if (blinking.value) return 'blinking'
  return props.currentState || 'idle'
})

const assetUrl = computed(() => {
  if (!props.characterId) return null
  const state = effectiveState.value
  const expr  = props.currentExpression || 'default'
  return `${props.baseUrl}/characters/${props.characterId}/avatar/pngtuber/${state}_${expr}.png`
})

// When transitioning to idle, keep the last expression for a moment then revert
watch(() => props.currentState, (next) => {
  if (next === 'idle') blinking.value = false
})
</script>

<style scoped>
.pngtuber-root {
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
}

.pngtuber-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  transition: transform 0.08s ease;
}

.pngtuber-talking {
  animation: talk-bounce 0.15s ease-in-out infinite alternate;
}

@keyframes talk-bounce {
  from { transform: translateY(0); }
  to   { transform: translateY(-3px); }
}

.pngtuber-placeholder {
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
}

.pngtuber-fade-enter-active,
.pngtuber-fade-leave-active {
  transition: opacity 0.12s ease;
}
.pngtuber-fade-enter-from,
.pngtuber-fade-leave-to {
  opacity: 0;
}
</style>
