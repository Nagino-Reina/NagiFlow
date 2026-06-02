<template>
  <svg :aria-label="ariaLabel" class="bigfive-radar" role="img" :viewBox="`0 0 ${W} ${H}`">
    <!-- grid rings + spokes -->
    <polygon v-for="(ring, i) in rings" :key="`r${i}`" class="radar-grid" :points="ring" />

    <line
      v-for="(p, i) in axisPoints"
      :key="`s${i}`"
      class="radar-grid"
      :x1="cx"
      :x2="p.x"
      :y1="cy"
      :y2="p.y"
    />

    <!-- default (50) reference, semi-transparent grey -->
    <polygon class="radar-baseline" :points="baselinePolygon" />

    <!-- actual values -->
    <polygon class="radar-value" :points="valuePolygon" />

    <!-- vertices coloured by deviation from default: red above, blue below -->
    <circle
      v-for="(v, i) in vertices"
      :key="`v${i}`"
      :cx="v.x"
      :cy="v.y"
      :r="v.r"
      :style="{ fill: v.color }"
    />

    <!-- axis labels -->
    <text
      v-for="(l, i) in axisLabels"
      :key="`l${i}`"
      class="radar-label"
      :text-anchor="l.anchor"
      :x="l.x"
      :y="l.y"
    >{{ l.text }}</text>
  </svg>
</template>

<script lang="ts" setup>
  import { computed } from 'vue'

  const props = withDefaults(defineProps<{
    data: { label: string, value: number }[]
    baseline?: number
    ariaLabel?: string
  }>(), { baseline: 50, ariaLabel: 'Big Five radar chart' })

  const W = 240
  const H = 210
  const cx = W / 2
  const cy = H / 2 + 4
  const maxR = 76

  const n = computed(() => props.data.length)
  const angle = (i: number) => -Math.PI / 2 + (i * 2 * Math.PI) / n.value
  const clamp = (v: number) => Math.max(0, Math.min(100, v))

  function at (value: number, i: number) {
    const r = (maxR * clamp(value)) / 100
    return { x: cx + r * Math.cos(angle(i)), y: cy + r * Math.sin(angle(i)) }
  }
  function toPoints (pts: { x: number, y: number }[]) {
    return pts.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')
  }

  const rings = computed(() =>
    [25, 50, 75, 100].map(level =>
      toPoints(props.data.map((_, i) => at(level, i)))))

  const axisPoints = computed(() => props.data.map((_, i) => at(100, i)))

  const baselinePolygon = computed(() =>
    toPoints(props.data.map((_, i) => at(props.baseline, i))))

  const valuePolygon = computed(() =>
    toPoints(props.data.map((d, i) => at(d.value, i))))

  const vertices = computed(() => props.data.map((d, i) => {
    const diff = clamp(d.value) - props.baseline
    const p = at(d.value, i)
    const color = diff > 0
      ? 'rgb(var(--v-theme-error))'
      : (diff < 0
        ? 'rgb(var(--v-theme-info))'
        : 'rgb(var(--v-theme-on-surface-variant))')
    return { ...p, r: 2.4 + Math.min(4, Math.abs(diff) / 14), color }
  }))

  const axisLabels = computed(() => props.data.map((d, i) => {
    const a = angle(i)
    const r = maxR + 16
    const x = cx + r * Math.cos(a)
    const y = cy + r * Math.sin(a) + 3
    const anchor = x < cx - 4 ? 'end' : (x > cx + 4 ? 'start' : 'middle')
    return { text: d.label, x, y, anchor }
  }))
</script>

<style scoped>
.bigfive-radar {
  width: 100%;
  height: auto;
}
.radar-grid {
  fill: none;
  stroke: rgba(var(--v-theme-on-surface), 0.12);
  stroke-width: 1;
}
.radar-baseline {
  fill: rgba(var(--v-theme-on-surface-variant), 0.18);
  stroke: rgba(var(--v-theme-on-surface-variant), 0.45);
  stroke-width: 1;
}
.radar-value {
  fill: rgba(var(--v-theme-primary), 0.14);
  stroke: rgb(var(--v-theme-primary));
  stroke-width: 2;
}
.radar-label {
  fill: rgba(var(--v-theme-on-surface), 0.75);
  font-size: 11px;
}
</style>
