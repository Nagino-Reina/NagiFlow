/**
 * stores/conversation.ts
 *
 * Synchronous chat state (docs/03 §3.4, docs/05 §4.3). Holds the active conversation and
 * its messages; each character reply carries the character's current emotion (docs/10).
 */

import type { Conversation, Message } from '@/api/types'
import { defineStore } from 'pinia'
import { conversationsApi } from '@/api/conversations'

export const useConversationStore = defineStore('conversation', {
  state: () => ({
    conversation: null as Conversation | null,
    messages: [] as Message[],
    history: [] as Conversation[],
    // Character chosen but not yet conversing: the conversation is created lazily on first send,
    // so picking a character never leaves an empty conversation behind.
    pendingCharacterId: null as string | null,
    sending: false,
    loading: false,
  }),
  getters: {
    /** The character of the active or pending conversation. */
    activeCharacterId: state => state.conversation?.character_id ?? state.pendingCharacterId,
    /** The character's latest emotion, for the mood indicator. */
    lastAffect: state => {
      for (let i = state.messages.length - 1; i >= 0; i--) {
        const msg = state.messages[i]
        if (msg && msg.role === 'character' && msg.meta?.affect) {
          return msg.meta.affect
        }
      }
      return null
    },
  },
  actions: {
    /** Load the user's past conversations (newest first) for the history list. */
    async loadHistory () {
      this.history = await conversationsApi.list()
    },
    /** Choose a character; the conversation is created lazily on the first send. */
    selectCharacter (characterId: string) {
      this.conversation = null
      this.messages = []
      this.pendingCharacterId = characterId
    },
    /** Load an existing conversation from the history list. */
    async open (conversation: Conversation) {
      this.loading = true
      try {
        this.pendingCharacterId = null
        this.conversation = conversation
        this.messages = await conversationsApi.messages(conversation.id)
      } finally {
        this.loading = false
      }
    },
    async send (text: string) {
      if (this.sending) {
        return
      }
      let conv = this.conversation
      if (!conv && this.pendingCharacterId === null) {
        return
      }
      this.sending = true
      try {
        // Create the conversation on the first message only (no empty conversations).
        if (!conv && this.pendingCharacterId !== null) {
          conv = await conversationsApi.create({ character_id: this.pendingCharacterId })
          this.conversation = conv
          this.pendingCharacterId = null
          this.history = [conv, ...this.history]
        }
        if (!conv) {
          return
        }
        const res = await conversationsApi.send(conv.id, text)
        this.messages.push(res.user_message, res.reply)
      } finally {
        this.sending = false
      }
    },
    /** Delete a conversation and drop it from history; resets the view if it was active. */
    async remove (conversationId: string) {
      await conversationsApi.remove(conversationId)
      this.history = this.history.filter(c => c.id !== conversationId)
      if (this.conversation?.id === conversationId) {
        this.conversation = null
        this.messages = []
      }
    },
    reset () {
      this.conversation = null
      this.messages = []
      this.pendingCharacterId = null
    },
  },
})
