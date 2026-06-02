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
  has_portrait: boolean
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

export type VoiceKind = 'zero_shot' | 'voice_design' | 'fine_tuned'

export interface VoiceModel {
  id: string
  character_id: string
  kind: VoiceKind
  provider: string
  version: number
  design_description: string | null
  status: string
  is_default: boolean
  created_at: string
  updated_at: string
}

/** Active TTS provider capability flags (docs/06 §5.1). */
export interface TTSCaps {
  name: string
  streaming: boolean
  voice_clone: boolean
  voice_design: boolean
  fine_tune: boolean
  sample_rate: number
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

// --- conversations & chat (docs/05 §4.3, docs/10) ---

export type MessageRole = 'user' | 'character' | 'system' | 'tool'

/** Short-term emotion carried on a character reply (docs/10 §2, §9). */
export interface AffectVAD {
  v: number
  a: number
  d: number
}

export interface Affect {
  vad: AffectVAD
  label: string
  intensity: number
  source: string
}

export interface MessageMeta {
  usage?: { prompt_tokens: number | null, completion_tokens: number | null }
  affect?: Affect
  expression?: string
  voice_style?: string[]
}

export interface Message {
  id: string
  conversation_id: string
  role: MessageRole
  speaker_character_id: string | null
  content: string
  media_asset_id: string | null
  created_at: string
  meta: MessageMeta
}

export interface Conversation {
  id: string
  character_id: string
  user_id: string
  mode: string
  sensitive_mode: boolean
  title: string | null
  status: string
  created_at: string
}

export interface ConversationCreate {
  character_id: string
  title?: string
}

export interface SendMessageResponse {
  user_message: Message
  reply: Message
}

// --- observability (docs/05 §4.7, docs/12) ---

export interface ServiceStatus {
  capability: string
  name: string
  model: string | null
  status: string
}

export interface SystemResources {
  cpu_percent: number
  cpu_count: number | null
  memory: { used: number, total: number, percent: number }
  disk: { used: number, total: number, free: number, percent: number }
  process: { pid: number, rss: number }
  gpus: Array<{ name: string, utilization_percent: number, memory_used: number, memory_total: number }>
}

export interface UsageTotals {
  calls: number
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  audio_seconds: number
  est_cost: number
}

export interface UsageGroup {
  key: string | null
  calls: number
  total_tokens: number
}

export interface UsageSummary {
  totals: UsageTotals
  by_character: UsageGroup[]
  by_provider: UsageGroup[]
  by_day: UsageGroup[]
}
