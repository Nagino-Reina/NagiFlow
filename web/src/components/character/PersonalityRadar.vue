<template>
  <svg :width="size" :height="size" :viewBox="`0 0 ${size} ${size}`">
    <!-- Background rings -->
    <polygon
      v-for="ring in [20,40,60,80,100]"
      :key="ring"
      :points="ringPoints(ring)"
      fill="none"
      stroke="rgba(255,255,255,0.06)"
      stroke-width="1"
    />
    <!-- Axis lines -->
    <line
      v-for="(axis, i) in axes"
      :key="`ax-${i}`"
      :x1="cx" :y1="cy"
      :x2="tipX(i, 100)" :y2="tipY(i, 100)"
      stroke="rgba(255,255,255,0.08)"
      stroke-width="1"
    />
    <!-- Score polygon -->
    <polygon
      :points="scorePoints"
      :fill="fillColor"
      :stroke="strokeColor"
      stroke-width="1.5"
      stroke-linejoin="round"
    />
    <!-- Axis labels -->
    <text
      v-for="(axis, i) in axes"
      :key="`lbl-${i}`"
      :x="labelX(i)"
      :y="labelY(i)"
      text-anchor="middle"
      dominant-baseline="middle"
      font-family="'DM Mono', monospace"
      font-size="9"
      fill="rgba(203,213,225,0.7)"
    >{{ axis.label }}</text>
    <!-- Value dots -->
    <circle
      v-for="(axis, i) in axes"
      :key="`dot-${i}`"
      :cx="tipX(i, scores[axis.key])"
      :cy="tipY(i, scores[axis.key])"
      r="3"
      :fill="axis.color"
    />
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  scores: { type: Object, required: true },
  size:   { type: Number, default: 180 },
})

const axes = [
  { key: 'openness',          label: 'O', color: '#06B6D4' },
  { key: 'conscientiousness', label: 'C', color: '#8B5CF6' },
  { key: 'extraversion',      label: 'E', color: '#EC4899' },
  { key: 'agreeableness',     label: 'A', color: '#10B981' },
  { key: 'neuroticism',       label: 'N', color: '#F59E0B' },
]

const cx = computed(() => props.size / 2)
const cy = computed(() => props.size / 2)
const r  = computed(() => props.size / 2 - 24)

function angle(i)         { return (Math.PI * 2 * i) / axes.length - Math.PI / 2 }
function tipX(i, pct)     { return cx.value + r.value * (pct / 100) * Math.cos(angle(i)) }
function tipY(i, pct)     { return cy.value + r.value * (pct / 100) * Math.sin(angle(i)) }
function labelX(i)        { return cx.value + (r.value + 14) * Math.cos(angle(i)) }
function labelY(i)        { return cy.value + (r.value + 14) * Math.sin(angle(i)) }

function ringPoints(pct) {
  return axes.map((_, i) => `${tipX(i, pct)},${tipY(i, pct)}`).join(' ')
}

const scorePoints = computed(() =>
  axes.map((a, i) => `${tipX(i, props.scores[a.key] ?? 50)},${tipY(i, props.scores[a.key] ?? 50)}`).join(' ')
)

const fillColor   = 'rgba(6,182,212,0.12)'
const strokeColor = 'rgba(6,182,212,0.7)'
</script>