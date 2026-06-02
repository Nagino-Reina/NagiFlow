/**
 * api/characters.ts
 *
 * Character endpoints (docs/05 §4.1, docs/08). CRUD + duplicate + the personality-mapping
 * preview that powers the editor's read-only "resulting directives" panel (FR-CM-4).
 */

import { http } from './http'
import { getToken } from './session'
import type {
  Character,
  CharacterCreate,
  CharacterUpdate,
  Page,
  PersonalitySchema,
} from './types'

const BASE = '/api/v1'

export const charactersApi = {
  list: (cursor?: string) =>
    http.get<Page<Character>>(`/characters${cursor ? `?cursor=${encodeURIComponent(cursor)}` : ''}`),
  get: (id: string) => http.get<Character>(`/characters/${id}`),
  create: (body: CharacterCreate) => http.post<Character>('/characters', body),
  update: (id: string, body: CharacterUpdate) => http.patch<Character>(`/characters/${id}`, body),
  archive: (id: string) => http.delete<void>(`/characters/${id}`),
  duplicate: (id: string) => http.post<Character>(`/characters/${id}:duplicate`),
  personalitySchema: () => http.get<PersonalitySchema>('/characters/personality/schema'),

  /** Upload a portrait image (multipart); returns the updated character. */
  async uploadPortrait (id: string, file: File): Promise<Character> {
    const token = getToken()
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${BASE}/characters/${id}/portrait`, {
      method: 'PUT',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    })
    if (!res.ok) throw new Error(`portrait upload failed (${res.status})`)
    return res.json() as Promise<Character>
  },

  deletePortrait: (id: string) => http.delete<void>(`/characters/${id}/portrait`),

  /** Fetch the portrait with the session token and return a playable object URL (or null if
      none / unauthorized). A native <img src> can't carry the Authorization header. */
  async portraitObjectUrl (id: string): Promise<string | null> {
    const token = getToken()
    const res = await fetch(`${BASE}/characters/${id}/portrait`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) return null
    return URL.createObjectURL(await res.blob())
  },
}
