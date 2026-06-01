/**
 * stores/conversation.ts
 *
 * Synchronous chat state (docs/03 §3.4, docs/05 §4.3). Holds the active conversation and
 * its messages; each character reply carries the character's current emotion (docs/10).
 */

import { defineStore } from 'pinia'
import { conversationsApi } from '@/api/conversations'
import type { Conversation, Message } from '@/api/types'

export const useConversationStore = defineStore('conversation', {
  state: () => ({
    conversation: null as Conversation | null,
    messages: [] as Message[],
    sending: false,
    loading: false,
  }),
  getters: {
    /** The character's latest emotion, for the mood indicator. */
    lastAffect: state => {
      for (let i = state.messages.length - 1; i >= 0; i--) {
        const msg = state.messages[i]
        if (msg && msg.role === 'character' && msg.meta?.affect) return msg.meta.affect
      }
      return null
    },
  },
  actions: {
    /** Start (or restart) a conversation with a character. */
    async start (characterId: string) {
      this.loading = true
      try {
        this.conversation = await conversationsApi.create({ character_id: characterId })
        this.messages = await conversationsApi.messages(this.conversation.id)
      } finally {
        this.loading = false
      }
    },
    async send (text: string) {
      if (!this.conversation || this.sending) return
      this.sending = true
      try {
        const res = await conversationsApi.send(this.conversation.id, text)
        this.messages.push(res.user_message, res.reply)
      } finally {
        this.sending = false
      }
    },
    reset () {
      this.conversation = null
      this.messages = []
    },
  },
})
