/**
 * api/characters.ts
 *
 * Character endpoints (docs/05 §4.1, docs/08). CRUD + duplicate + the personality-mapping
 * preview that powers the editor's read-only "resulting directives" panel (FR-CM-4).
 */

import { http } from './http'
import type {
  Character,
  CharacterCreate,
  CharacterUpdate,
  Page,
  PersonalitySchema,
} from './types'

export const charactersApi = {
  list: (cursor?: string) =>
    http.get<Page<Character>>(`/characters${cursor ? `?cursor=${encodeURIComponent(cursor)}` : ''}`),
  get: (id: string) => http.get<Character>(`/characters/${id}`),
  create: (body: CharacterCreate) => http.post<Character>('/characters', body),
  update: (id: string, body: CharacterUpdate) => http.patch<Character>(`/characters/${id}`, body),
  archive: (id: string) => http.delete<void>(`/characters/${id}`),
  duplicate: (id: string) => http.post<Character>(`/characters/${id}:duplicate`),
  personalitySchema: () => http.get<PersonalitySchema>('/characters/personality/schema'),
}
