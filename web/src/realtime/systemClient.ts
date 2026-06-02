/**
 * realtime/systemClient.ts
 *
 * WebSocket client for the system-status stream (docs/05 §5.1). Holds one connection that
 * the backend pushes resources / service health / usage on an interval, replacing REST
 * polling. Reconnects with exponential backoff; a 1008 close (auth refused) stops retrying.
 */

import { getToken } from '@/api/session'
import type { ServiceStatus, SystemResources, UsageSummary } from '@/api/types'

export interface SystemStatus {
  type: 'system.status'
  resources: SystemResources
  services: ServiceStatus[]
  usage: UsageSummary
}

export type StatusHandler = (status: SystemStatus) => void

const MAX_BACKOFF_MS = 30_000

export class SystemStatusClient {
  private socket: WebSocket | null = null
  private handler: StatusHandler | null = null
  private retry = 0
  private timer: number | undefined
  private stopped = false

  /** Open the stream and invoke `handler` on every pushed status. */
  start (handler: StatusHandler): void {
    this.handler = handler
    this.stopped = false
    this.open()
  }

  private open (): void {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${proto}://${location.host}/api/v1/system/stream`
    const token = getToken()
    // The token rides the bearer sub-protocol, never the query string (docs/05 §5).
    const protocols = token ? ['bearer', token] : undefined

    const socket = new WebSocket(url, protocols)
    this.socket = socket

    socket.addEventListener('open', () => {
      this.retry = 0
    })
    socket.addEventListener('message', event => {
      if (typeof event.data !== 'string') return
      try {
        const msg = JSON.parse(event.data) as SystemStatus
        if (msg.type === 'system.status') this.handler?.(msg)
      } catch {
        // ignore malformed frames
      }
    })
    socket.addEventListener('close', event => {
      this.socket = null
      // 1008 = auth refused; reconnecting would just be refused again.
      if (this.stopped || event.code === 1008) return
      this.scheduleReconnect()
    })
  }

  private scheduleReconnect (): void {
    const delay = Math.min(MAX_BACKOFF_MS, 1000 * 2 ** this.retry)
    this.retry++
    this.timer = window.setTimeout(() => this.open(), delay)
  }

  stop (): void {
    this.stopped = true
    if (this.timer) clearTimeout(this.timer)
    this.socket?.close()
    this.socket = null
    this.handler = null
  }
}
