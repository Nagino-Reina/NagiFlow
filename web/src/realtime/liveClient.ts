/**
 * realtime/liveClient.ts
 *
 * Thin WebSocket client wrapping the live-turn protocol (docs/05 §5). P0 ships the seam
 * only — connect/send/close plus event dispatch — so the live console (P5) and streaming
 * chat (P1) build on a stable surface. Audio binary frames and barge-in land later.
 */

import { getToken } from '@/api/session'

/** Server→client event shapes (docs/05 §5). Narrowed per-type as features land. */
export interface LiveEvent {
  type: string
  turn_id?: string
  character_id?: string
  text?: string
  [key: string]: unknown
}

export type LiveEventHandler = (event: LiveEvent) => void

export class LiveClient {
  private socket: WebSocket | null = null
  private readonly handlers = new Set<LiveEventHandler>()

  constructor (private readonly conversationId: string) {}

  /**
   * Open the stream. The session token rides the `Sec-WebSocket-Protocol` bearer
   * sub-protocol — never the query string (docs/05 §5).
   */
  connect (): void {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${proto}://${location.host}/api/v1/conversations/${this.conversationId}/stream`
    const token = getToken()
    const protocols = token ? ['bearer', token] : undefined

    this.socket = new WebSocket(url, protocols)
    this.socket.binaryType = 'arraybuffer'
    this.socket.addEventListener('message', event => {
      if (typeof event.data !== 'string') return // binary audio frames handled in P1+
      try {
        this.dispatch(JSON.parse(event.data) as LiveEvent)
      } catch {
        // ignore malformed control frames
      }
    })
  }

  send (message: Record<string, unknown>): void {
    this.socket?.send(JSON.stringify(message))
  }

  interrupt (): void {
    this.send({ type: 'control.interrupt' })
  }

  onEvent (handler: LiveEventHandler): () => void {
    this.handlers.add(handler)
    return () => this.handlers.delete(handler)
  }

  close (): void {
    this.socket?.close()
    this.socket = null
    this.handlers.clear()
  }

  private dispatch (event: LiveEvent): void {
    for (const handler of this.handlers) handler(event)
  }
}
