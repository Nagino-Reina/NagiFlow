/**
 * api/conversations.ts
 *
 * Conversation + chat endpoints (docs/05 §4.3). A reply carries the character's current
 * emotion in `meta.affect` (docs/10 §9).
 */

import { http } from './http'
import type {
  Conversation,
  ConversationCreate,
  Message,
  SendMessageResponse,
} from './types'

export const conversationsApi = {
  list: () => http.get<Conversation[]>('/conversations'),
  create: (body: ConversationCreate) => http.post<Conversation>('/conversations', body),
  messages: (id: string) => http.get<Message[]>(`/conversations/${id}/messages`),
  send: (id: string, text: string) =>
    http.post<SendMessageResponse>(`/conversations/${id}/messages`, { text }),
}
