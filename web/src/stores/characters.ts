/**
 * stores/characters.ts
 *
 * Character domain state (docs/03 §3.4). Holds the list + the editor's working copy;
 * create/update/duplicate/archive flow through the typed API client.
 */

import { defineStore } from 'pinia'
import { charactersApi } from '@/api/characters'
import type { Character, CharacterCreate, CharacterUpdate, PersonalitySchema } from '@/api/types'

type Status = 'idle' | 'loading' | 'ready' | 'error'

export const useCharactersStore = defineStore('characters', {
  state: () => ({
    items: [] as Character[],
    status: 'idle' as Status,
    personalitySchema: null as PersonalitySchema | null,
  }),
  actions: {
    /** Fetch the Big Five mapping spec once; cached for the session. */
    async loadPersonalitySchema () {
      if (!this.personalitySchema) {
        this.personalitySchema = await charactersApi.personalitySchema()
      }
    },
    async load () {
      this.status = 'loading'
      try {
        const page = await charactersApi.list()
        this.items = page.items
        this.status = 'ready'
      } catch {
        this.status = 'error'
      }
    },
    async get (id: string): Promise<Character> {
      const cached = this.items.find(c => c.id === id)
      if (cached) return cached
      return charactersApi.get(id)
    },
    async create (body: CharacterCreate): Promise<Character> {
      const created = await charactersApi.create(body)
      this.items = [created, ...this.items]
      return created
    },
    async update (id: string, body: CharacterUpdate): Promise<Character> {
      const updated = await charactersApi.update(id, body)
      this.items = this.items.map(c => (c.id === id ? updated : c))
      return updated
    },
    async duplicate (id: string): Promise<Character> {
      const clone = await charactersApi.duplicate(id)
      this.items = [clone, ...this.items]
      return clone
    },
    async archive (id: string): Promise<void> {
      await charactersApi.archive(id)
      this.items = this.items.filter(c => c.id !== id)
    },
  },
})
