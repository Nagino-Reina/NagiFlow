/**
 * personality/mapping.ts
 *
 * Computes the Big Five → behavior view locally from the server-provided spec
 * (docs/08 §3.2). The spec (directive tables, thresholds, parameter formulas) is the single
 * source of truth fetched once; this module only performs the generic interpretation
 * arithmetic, so adjusting sliders triggers no requests.
 */

import type { BigFive, ParamFormula, PersonalityMapping, PersonalitySchema } from '@/api/types'

const clamp = (v: number, min: number, max: number) => Math.max(min, Math.min(max, v))

/** Band index 0..N for a score against ascending thresholds (`< t[i]` → band i). */
export function bandIndexOf (score: number, thresholds: number[]): number {
  for (const [i, threshold] of thresholds.entries()) {
    if (score < threshold) {
      return i
    }
  }
  return thresholds.length
}

function score (big: BigFive, trait: string) {
  return clamp(Math.round(big[trait as keyof BigFive] ?? 50), 0, 100)
}

function param (cfg: ParamFormula, big: BigFive): number {
  let value = cfg.base
  for (const [trait, coef] of Object.entries(cfg.coefficients)) {
    value += coef * ((score(big, trait) - 50) / 50)
  }
  return Math.round(clamp(value, cfg.min, cfg.max) * 1000) / 1000
}

export function resolvePersonality (schema: PersonalitySchema, big: BigFive): PersonalityMapping {
  const traits = schema.traits.map(trait => {
    const s = score(big, trait)
    const idx = bandIndexOf(s, schema.thresholds)
    return { trait, score: s, band: schema.bands[idx], directive: schema.directives[trait][idx] }
  })

  const voiceStyle: string[] = []
  for (const [trait, rules] of Object.entries(schema.voice_style)) {
    const idx = bandIndexOf(score(big, trait), schema.thresholds)
    if (rules.very_high && idx === 4) {
      voiceStyle.push(rules.very_high)
    } else if (rules.high && idx >= 3) {
      voiceStyle.push(rules.high)
    } else if (rules.very_low && idx === 0) {
      voiceStyle.push(rules.very_low)
    } else if (rules.low && idx <= 1) {
      voiceStyle.push(rules.low)
    }
  }

  return {
    traits,
    temperature: param(schema.params.temperature, big),
    top_p: param(schema.params.top_p, big),
    verbosity: schema.verbosity[bandIndexOf(score(big, 'extraversion'), schema.thresholds)],
    speech_rate: param(schema.params.speech_rate, big),
    expressiveness: schema.expressiveness[bandIndexOf(score(big, 'neuroticism'), schema.thresholds)],
    voice_style: voiceStyle,
  }
}
