/**
 * api/voice.ts
 *
 * Voice-model + TTS endpoints (docs/05 §4.1, docs/08 §4). JSON calls go through the shared
 * `http` client; the multipart clone upload and the binary preview use a thin authed fetch
 * that surfaces the same error envelope (docs/05 §3).
 */

import type { TTSCaps, VoiceModel } from './types'
import { ApiError, http } from './http'
import { getToken } from './session'

const BASE = '/api/v1'

async function authed (path: string, init: RequestInit): Promise<Response> {
  const token = getToken()
  const headers = new Headers(init.headers)
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  let res: Response
  try {
    res = await fetch(`${BASE}${path}`, { ...init, headers })
  } catch {
    throw new ApiError('network.error', 'Network request failed.', 0)
  }
  if (!res.ok) {
    const env = await res.json().catch(() => null)
    const e = env?.error
    throw new ApiError(e?.code ?? 'internal.error', e?.message ?? res.statusText, res.status,
      e?.details, e?.correlation_id)
  }
  return res
}

export interface PreviewBody {
  text?: string
  voice_model_id?: string
  style?: string
  speech_rate?: number
}

export const voiceApi = {
  capabilities: () => http.get<TTSCaps>('/characters/voice/capabilities'),
  list: (characterId: string) =>
    http.get<VoiceModel[]>(`/characters/${characterId}/voice-models`),
  createDesign: (characterId: string, description: string) =>
    http.post<VoiceModel>(`/characters/${characterId}/voice-models`, {
      design_description: description,
    }),
  setDefault: (characterId: string, voiceModelId: string) =>
    http.post<VoiceModel>(`/characters/${characterId}/voice-models/${voiceModelId}:setDefault`),
  remove: (characterId: string, voiceModelId: string) =>
    http.delete<void>(`/characters/${characterId}/voice-models/${voiceModelId}`),

  async clone (characterId: string, reference: File, sampleText?: string): Promise<VoiceModel> {
    const form = new FormData()
    form.append('reference', reference)
    if (sampleText) {
      form.append('sample_text', sampleText)
    }
    const res = await authed(`/characters/${characterId}/voice-models:clone`, {
      method: 'POST', body: form,
    })
    return res.json() as Promise<VoiceModel>
  },

  /** Synthesize a sample and return the audio as an object URL for playback. */
  async preview (characterId: string, body: PreviewBody): Promise<string> {
    const res = await authed(`/characters/${characterId}/voice:preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    return URL.createObjectURL(await res.blob())
  },
}
