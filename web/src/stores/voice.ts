/**
 * stores/voice.ts
 *
 * Voice-model state for the character editor's Voice tab (docs/08 §4). Holds the active
 * provider's capability flags (cached for the session) and the current character's models.
 */

import { defineStore } from 'pinia'
import { voiceApi } from '@/api/voice'
import type { TTSCaps, VoiceModel } from '@/api/types'

export const useVoiceStore = defineStore('voice', {
  state: () => ({
    models: [] as VoiceModel[],
    caps: null as TTSCaps | null,
    loading: false,
  }),
  actions: {
    async loadCaps () {
      if (!this.caps) this.caps = await voiceApi.capabilities()
    },
    async load (characterId: string) {
      this.loading = true
      try {
        this.models = await voiceApi.list(characterId)
      } finally {
        this.loading = false
      }
    },
    async createDesign (characterId: string, description: string) {
      const model = await voiceApi.createDesign(characterId, description)
      await this.load(characterId)
      return model
    },
    async clone (characterId: string, reference: File, sampleText?: string) {
      const model = await voiceApi.clone(characterId, reference, sampleText)
      await this.load(characterId)
      return model
    },
    async setDefault (characterId: string, voiceModelId: string) {
      await voiceApi.setDefault(characterId, voiceModelId)
      await this.load(characterId)
    },
    async remove (characterId: string, voiceModelId: string) {
      await voiceApi.remove(characterId, voiceModelId)
      await this.load(characterId)
    },
    reset () {
      this.models = []
    },
  },
})
