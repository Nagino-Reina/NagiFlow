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

  const _deltaHandlers = []
  const _doneHandlers  = []
  const _errorHandlers = []
  const _audioHandlers = []

  function onDelta(fn) { _deltaHandlers.push(fn) }
  function onDone(fn)  { _doneHandlers.push(fn)  }
  function onError(fn) { _errorHandlers.push(fn) }
  function onAudio(fn) { _audioHandlers.push(fn) }

  function _dispatch(list, ...args) { list.forEach(fn => fn(...args)) }

  function connect({ characterId, conversationId, message, mode = 'text', token }) {
    disconnect()

    const path = mode === 'audio' ? '/api/v1/ws/stream/audio' : '/api/v1/ws/stream/text'
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const url   = `${proto}://${location.host}${path}`

    status.value = 'connecting'
    ws = new WebSocket(url)

    ws.onopen = () => {
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
        try {
          const frame = JSON.parse(evt.data)
          if (frame.type === 'delta') _dispatch(_deltaHandlers, frame.content)
          if (frame.type === 'done')  _dispatch(_doneHandlers,  frame.conversation_id)
          if (frame.type === 'error') _dispatch(_errorHandlers, frame.detail)
        } catch { /**/ }
      } else {
        // Binary: audio chunk (ArrayBuffer or Blob)
        _dispatch(_audioHandlers, evt.data)
      }
    }

    ws.onerror = () => {
      status.value = 'error'
      _dispatch(_errorHandlers, 'WebSocket connection error.')
    }

    ws.onclose = () => {
      status.value = 'closed'
    }
  }

  function disconnect() {
    if (ws) { ws.close(); ws = null }
    status.value = 'idle'
  }

  onUnmounted(disconnect)

  return { status, connect, disconnect, onDelta, onDone, onError, onAudio }
}