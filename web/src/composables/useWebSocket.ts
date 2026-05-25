/**
 * composables/useWebSocket.js
 *
 * Composable that wraps a NagiFlow streaming WebSocket connection.
 *
 * Usage:
 *   const { connect, disconnect, status, onDelta, onDone, onError } = useWebSocket()
 *   await connect({ characterId, conversationId, message, mode: 'text' | 'audio' })
 */

import { ref, onUnmounted } from 'vue'

export function useWebSocket() {
  const status = ref('idle')   // 'idle' | 'connecting' | 'open' | 'closed' | 'error'
  let ws = null

  const _deltaHandlers    = []
  const _doneHandlers     = []
  const _errorHandlers    = []
  const _audioHandlers    = []
  const _animStateHandlers = []

  function onDelta(fn)     { _deltaHandlers.push(fn)     }
  function onDone(fn)      { _doneHandlers.push(fn)      }
  function onError(fn)     { _errorHandlers.push(fn)     }
  function onAudio(fn)     { _audioHandlers.push(fn)     }
  function onAnimState(fn) { _animStateHandlers.push(fn) }

  function _dispatch(list, ...args) { list.forEach(fn => fn(...args)) }

  const CONNECT_TIMEOUT_MS = 10_000

  function connect({ characterId, conversationId, message, mode = 'text', token }) {
    disconnect()

    const path = mode === 'audio' ? '/api/v1/ws/stream/audio' : '/api/v1/ws/stream/text'
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const url   = `${proto}://${location.host}${path}`

    status.value = 'connecting'
    ws = new WebSocket(url)

    // Abort if the socket never opens within the timeout
    const connectTimer = setTimeout(() => {
      if (status.value === 'connecting') {
        ws?.close()
        status.value = 'error'
        _dispatch(_errorHandlers, 'WebSocket connection timed out.')
      }
    }, CONNECT_TIMEOUT_MS)

    ws.onopen = () => {
      clearTimeout(connectTimer)
      status.value = 'open'
      ws.send(JSON.stringify({
        token,
        character_id:    characterId,
        conversation_id: conversationId ?? null,
        message,
      }))
    }

    ws.onmessage = (evt) => {
      if (typeof evt.data === 'string') {
        let frame: Record<string, unknown>
        try {
          frame = JSON.parse(evt.data)
        } catch {
          _dispatch(_errorHandlers, 'Received malformed frame from server.')
          return
        }
        if (frame.type === 'delta')      _dispatch(_deltaHandlers,     frame.content)
        if (frame.type === 'done')       _dispatch(_doneHandlers,      frame.conversation_id)
        if (frame.type === 'error')      _dispatch(_errorHandlers,     frame.detail)
        if (frame.type === 'anim_state') _dispatch(_animStateHandlers, frame.state, frame.expression)
      } else {
        // Binary: audio chunk (ArrayBuffer or Blob)
        _dispatch(_audioHandlers, evt.data)
      }
    }

    ws.onerror = () => {
      clearTimeout(connectTimer)
      status.value = 'error'
      _dispatch(_errorHandlers, 'WebSocket connection error.')
    }

    ws.onclose = () => {
      clearTimeout(connectTimer)
      status.value = 'closed'
    }
  }

  function disconnect() {
    if (ws) { ws.close(); ws = null }
    status.value = 'idle'
  }

  onUnmounted(disconnect)

  return { status, connect, disconnect, onDelta, onDone, onError, onAudio, onAnimState }
}