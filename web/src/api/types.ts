/**
 * api/types.ts
 *
 * Shared API types — minimal P0 subset mirroring the backend schemas (docs/05 §2).
 * Broader types are generated from OpenAPI later (docs/03 §3.4, docs/05 §7).
 */

export type PrincipalKind = 'guest' | 'user'

/** GET /auth/me (backend `MeResponse`). */
export interface Principal {
  user_id: string
  kind: PrincipalKind
  is_admin: boolean
  username?: string | null
  display_name?: string | null
}

/** POST /auth/guest | /auth/login (backend `SessionResponse`). */
export interface SessionResponse {
  token: string
  user_id: string
  kind: PrincipalKind
  expires_at: string
}

/** POST /auth/register — creates the account; does not start a session. */
export interface RegisterResponse {
  id: string
  username: string
}

/** Cursor-paginated list response (docs/05 §1). */
export interface Page<T> {
  items: T[]
  next_cursor: string | null
}

export interface BigFive {
  openness: number
  conscientiousness: number
  extraversion: number
  agreeableness: number
  neuroticism: number
}

export type CharacterStatus = 'draft' | 'active' | 'archived'

export interface Character {
  id: string
  name: string
  aliases: string[]
  description: string
  persona: string
  big_five: BigFive
  default_language: string
  guest_visible: boolean
  avatar_renderer: string | null
  status: CharacterStatus
  tags: string[]
  created_at: string
  updated_at: string
}

export interface CharacterCreate {
  name: string
  description?: string
  persona?: string
  big_five?: BigFive
  default_language?: string
  aliases?: string[]
  tags?: string[]
  guest_visible?: boolean
  avatar_renderer?: string | null
}

export type CharacterUpdate = Partial<CharacterCreate & { status: CharacterStatus }>

export type PersonalityBand = 'very_low' | 'low' | 'moderate' | 'high' | 'very_high'

export interface TraitEffect {
  trait: string
  score: number
  band: PersonalityBand
  directive: string
}

/** Resolved Big Five behavior — the FR-CM-4 explainability view (docs/08 §3.2). */
export interface PersonalityMapping {
  traits: TraitEffect[]
  temperature: number
  top_p: number
  verbosity: string
  speech_rate: number
  expressiveness: string
  voice_style: string[]
}

/** A continuous parameter as `base + Σ coefficients[trait] * norm(score)`, clamped. */
export interface ParamFormula {
  base: number
  coefficients: Record<string, number>
  min: number
  max: number
}

/** The full mapping spec, fetched once; the client computes mappings locally from it. */
export interface PersonalitySchema {
  bands: PersonalityBand[]
  thresholds: number[]
  traits: string[]
  directives: Record<string, string[]>
  verbosity: string[]
  expressiveness: string[]
  voice_style: Record<string, Record<string, string>>
  params: Record<string, ParamFormula>
}

/** The API error envelope (docs/05 §3). */
export interface ErrorEnvelope {
  error: {
    code: string
    message: string
    details?: Record<string, unknown>
    correlation_id?: string
  }
}
