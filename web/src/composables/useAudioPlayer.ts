/**
 * composables/useAudioPlayer.js
 *
 * Streams WAV audio chunks (ArrayBuffer / Blob) received over WebSocket
 * into the Web Audio API, enabling near-real-time playback with minimal
 * buffering delay.
 *
 * Usage:
 *   const { enqueue, stop, playing } = useAudioPlayer()
 *   // inside onAudio callback:
 *   enqueue(blob)
 */

import { ref } from 'vue'

export function useAudioPlayer() {
  const playing = ref(false)

  let ctx        = null
  let queue      = []
  let isPlaying  = false

  function _ensureCtx() {
    if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)()
    if (ctx.state === 'suspended') ctx.resume()
  }

  async function _blobToBuffer(blob) {
    const ab = blob instanceof ArrayBuffer ? blob : await blob.arrayBuffer()
    return ctx.decodeAudioData(ab.slice(0))
  }

  async function _playNext() {
    if (queue.length === 0) { isPlaying = false; playing.value = false; return }
    isPlaying = true
    playing.value = true
    const blob = queue.shift()
    try {
      const buf    = await _blobToBuffer(blob)
      const source = ctx.createBufferSource()
      source.buffer = buf
      source.connect(ctx.destination)
      source.onended = _playNext
      source.start(0)
    } catch {
      // skip corrupted chunk
      _playNext()
    }
  }

  function enqueue(blob) {
    _ensureCtx()
    queue.push(blob)
    if (!isPlaying) _playNext()
  }

  function stop() {
    queue = []
    isPlaying = false
    playing.value = false
    if (ctx) { ctx.close(); ctx = null }
  }

  return { playing, enqueue, stop }
}