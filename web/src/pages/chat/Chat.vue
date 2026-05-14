<template>
  <div class="chat-layout d-flex ga-0" style="height:calc(100vh - 128px);">

    <!-- ── Left: conversation list sidebar ── -->
    <div class="conv-sidebar d-none d-md-flex flex-column mr-4" style="width:240px;flex-shrink:0;">
      <div class="d-flex align-center justify-space-between mb-3">
        <span class="text-caption text-medium-emphasis font-weight-medium">CONVERSATIONS</span>
        <v-btn icon="mdi-plus" size="x-small" variant="text" color="primary" @click="newConversation" />
      </div>
      <div class="flex-1 overflow-y-auto d-flex flex-column ga-1">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="conv-item pa-3 rounded-xl"
          :class="{ 'conv-item--active': currentConvId === conv.id }"
          @click="selectConv(conv.id)"
        >
          <div class="text-body-2 font-weight-medium text-truncate">
            {{ conv.title ?? 'Untitled Chat' }}
          </div>
          <div class="text-caption text-medium-emphasis">
            {{ formatDate(conv.updated_at) }}
          </div>
        </div>
        <div v-if="conversations.length === 0" class="text-caption text-medium-emphasis text-center py-4">
          No conversations yet
        </div>
      </div>
    </div>

    <!-- ── Right: chat area ── -->
    <div class="flex-1 d-flex flex-column" style="min-width:0;">

      <!-- Character header bar -->
      <div class="d-flex align-center ga-3 mb-3 pa-3 glass-bright rounded-xl">
        <v-avatar size="36" color="surface-2">
          <span class="font-display font-weight-bold text-primary" style="font-size:14px;">
            {{ char?.name?.charAt(0) ?? '?' }}
          </span>
        </v-avatar>
        <div class="flex-1">
          <div class="font-display font-weight-semibold text-body-1">{{ char?.name ?? '…' }}</div>
          <div class="d-flex align-center ga-1">
            <div class="status-online" />
            <span class="text-caption text-medium-emphasis">Ready</span>
          </div>
        </div>

        <!-- Mode toggles -->
        <v-tooltip text="Stream Text (WebSocket)">
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              :icon="streamMode ? 'mdi-lightning-bolt' : 'mdi-lightning-bolt-outline'"
              size="small"
              :color="streamMode ? 'primary' : 'default'"
              variant="tonal"
              @click="streamMode = !streamMode"
            />
          </template>
        </v-tooltip>

        <v-tooltip text="Voice Output (TTS)">
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              :icon="audioMode ? 'mdi-volume-high' : 'mdi-volume-off'"
              size="small"
              :color="audioMode ? 'secondary' : 'default'"
              variant="tonal"
              @click="toggleAudio"
            />
          </template>
        </v-tooltip>

        <v-btn icon="mdi-delete-outline" size="small" variant="text" color="error"
          @click="clearConversation" />
      </div>

      <!-- Message list -->
      <div ref="messagesRef" class="flex-1 overflow-y-auto px-1 d-flex flex-column ga-3 mb-3">
        <div v-if="messages.length === 0 && !thinking"
          class="d-flex flex-column align-center justify-center h-100 text-center">
          <v-icon size="56" style="opacity:.2;color:#06B6D4;" class="mb-4">mdi-chat-outline</v-icon>
          <div class="font-display text-h6 mb-2" style="opacity:.5;">Start a conversation</div>
          <div class="text-body-2 text-medium-emphasis" style="max-width:320px;">
            Send a message to {{ char?.name ?? 'your character' }} to begin.
          </div>
          <!-- Suggested starters -->
          <div class="d-flex flex-wrap justify-center ga-2 mt-5">
            <v-chip
              v-for="starter in starters"
              :key="starter"
              size="small"
              variant="outlined"
              class="cursor-pointer"
              @click="sendMessage(starter)"
            >
              {{ starter }}
            </v-chip>
          </div>
        </div>

        <template v-else>
          <MessageBubble
            v-for="msg in messages"
            :key="msg.id"
            :message="msg"
            :char-name="char?.name"
          />
          <!-- Streaming bubble -->
          <MessageBubble
            v-if="streamBuffer"
            :message="{ role: 'assistant', content: streamBuffer, id: 'stream' }"
            :char-name="char?.name"
            :streaming="true"
          />
          <!-- Thinking indicator -->
          <div v-if="thinking && !streamBuffer" class="d-flex align-center ga-3">
            <v-avatar size="28" color="surface-2">
              <span class="font-display font-weight-bold text-primary" style="font-size:11px;">
                {{ char?.name?.charAt(0) }}
              </span>
            </v-avatar>
            <div class="thinking-bubble pa-3 rounded-xl rounded-tl-0">
              <span class="typing-dot" />
              <span class="typing-dot" />
              <span class="typing-dot" />
            </div>
          </div>
        </template>
      </div>

      <!-- Input area -->
      <div class="input-area glass-bright rounded-xl pa-3 d-flex align-end ga-2">
        <v-textarea
          v-model="inputText"
          placeholder="Type a message…"
          rows="1"
          auto-grow
          max-rows="5"
          variant="plain"
          hide-details
          :disabled="thinking"
          class="flex-1"
          style="font-size:15px;"
          @keydown.enter.exact.prevent="handleEnter"
          @keydown.shift.enter.exact="inputText += '\n'"
        />
        <div class="d-flex align-center ga-2 pb-1">
          <!-- Audio playing indicator -->
          <div v-if="audioPlayer.playing.value" class="d-flex align-center ga-1 text-caption text-primary">
            <v-icon size="14" class="audio-pulse">mdi-volume-high</v-icon>
            <span>Playing</span>
          </div>
          <v-btn
            icon="mdi-send"
            color="primary"
            :loading="thinking"
            :disabled="!inputText.trim()"
            class="glow-cyan"
            size="small"
            @click="handleEnter"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useCharactersStore } from '@/stores/characters'
import { useAppStore } from '@/stores/app'
import { conversationsApi } from '@/api'
import { useWebSocket } from '@/composables/useWebSocket'
import { useAudioPlayer } from '@/composables/useAudioPlayer'
import MessageBubble from '@/components/chat/MessageBubble.vue'

const route     = useRoute()
const auth      = useAuthStore()
const charStore = useCharactersStore()
const app       = useAppStore()

const char          = computed(() => charStore.current)
const conversations = ref([])
const messages      = ref([])
const currentConvId = ref(null)
const inputText     = ref('')
const thinking      = ref(false)
const streamBuffer  = ref('')
const streamMode    = ref(true)
const audioMode     = ref(false)
const messagesRef   = ref(null)

const starters = ['Hello! Who are you?', 'Tell me something interesting!', 'What can you help me with?']

// ── WebSocket + Audio ─────────────────────────────────────────────────────
const ws          = useWebSocket()
const audioPlayer = useAudioPlayer()

ws.onDelta((chunk) => { streamBuffer.value += chunk })
ws.onAudio((blob)  => audioPlayer.enqueue(blob))
ws.onDone(async (convId) => {
  if (convId && !currentConvId.value) currentConvId.value = convId
  // Flush stream buffer into messages list
  if (streamBuffer.value) {
    messages.value.push({ id: Date.now(), role: 'assistant', content: streamBuffer.value })
    streamBuffer.value = ''
  }
  thinking.value = false
  await loadConversations()
  scrollBottom()
})
ws.onError((detail) => {
  app.notifyError({ message: detail })
  thinking.value = false
  streamBuffer.value = ''
})

// ── Actions ────────────────────────────────────────────────────────────────
async function handleEnter() {
  const text = inputText.value.trim()
  if (!text || thinking.value) return
  await sendMessage(text)
}

async function sendMessage(text) {
  inputText.value = ''
  messages.value.push({ id: Date.now(), role: 'user', content: text })
  thinking.value = true
  streamBuffer.value = ''
  scrollBottom()

  const token = auth.accessToken
  const charId = route.params.id

  if (streamMode.value) {
    const mode = audioMode.value ? 'audio' : 'text'
    ws.connect({ characterId: charId, conversationId: currentConvId.value, message: text, mode, token })
  } else {
    // One-shot REST
    try {
      const { data } = await conversationsApi.chat(charId, {
        conversation_id: currentConvId.value,
        message: text,
        generate_audio: audioMode.value,
      })
      if (!currentConvId.value) currentConvId.value = data.conversation_id
      messages.value.push({
        id: data.message.id,
        role: 'assistant',
        content: data.message.content,
        audio_url: data.audio_url,
      })
      if (data.audio_url && audioMode.value) {
        const res = await fetch(data.audio_url, { headers: { Authorization: `Bearer ${token}` } })
        const blob = await res.blob()
        audioPlayer.enqueue(blob)
      }
    } catch (err) { app.notifyError(err) }
    finally { thinking.value = false; scrollBottom() }
  }
}

function toggleAudio() {
  audioMode.value = !audioMode.value
  if (!audioMode.value) audioPlayer.stop()
}

async function newConversation() {
  currentConvId.value = null
  messages.value = []
  streamBuffer.value = ''
}

async function selectConv(id) {
  currentConvId.value = id
  try {
    const { data } = await conversationsApi.get(id)
    messages.value = data.messages
    await nextTick(); scrollBottom()
  } catch (err) { app.notifyError(err) }
}

async function clearConversation() {
  if (!currentConvId.value) return
  const ok = await app.showConfirm('Delete Conversation', 'This will permanently delete the current conversation.')
  if (!ok) return
  try {
    await conversationsApi.delete(currentConvId.value)
    await newConversation()
    await loadConversations()
    app.notify('Conversation deleted.')
  } catch (err) { app.notifyError(err) }
}

async function loadConversations() {
  try {
    const { data } = await conversationsApi.list({ character_id: route.params.id })
    conversations.value = data
  } catch { /**/ }
}

function scrollBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

watch(() => messages.value.length, scrollBottom)

onMounted(async () => {
  await charStore.fetchOne(route.params.id)
  await loadConversations()
})
</script>

<style scoped>
.chat-layout { position: relative; }

.conv-sidebar { position: relative; }
.conv-item {
  cursor: pointer;
  border: 1px solid transparent;
  transition: background 0.15s;
  &:hover { background: rgba(6,182,212,0.06); }
  &--active {
    background: rgba(6,182,212,0.10) !important;
    border-color: rgba(6,182,212,0.25) !important;
  }
}

.thinking-bubble {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.07);
  display: flex; align-items: center; gap: 3px;
}

.input-area {
  border: 1px solid rgba(255,255,255,0.07);
  transition: border-color 0.2s;
  &:focus-within { border-color: rgba(6,182,212,0.35); }
}

@keyframes audio-pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
.audio-pulse { animation: audio-pulse 1s ease infinite; }
</style>