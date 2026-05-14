# nagiflow-web

Vue 3 + Vuetify 3 frontend for the [NagiFlow](../nagiflow/) AI Vtuber backend.

## Tech Stack

| Layer | Library |
|-------|---------|
| Framework | Vue 3 (Composition API + `<script setup>`) |
| UI | Vuetify 3 (Material Design 3 blueprint) |
| State | Pinia |
| Router | Vue Router 4 |
| HTTP | Axios (with auto JWT refresh) |
| WebSocket | Native `WebSocket` via `useWebSocket` composable |
| Audio | Web Audio API via `useAudioPlayer` composable |
| Build | Vite 6 + `vite-plugin-vuetify` (auto-import) |
| Styles | SCSS + Vuetify theme variables |

## Tooling — same as `pnpm create vuetify` (Recommended preset)

This project was scaffolded to mirror the output of:
```bash
pnpm create vuetify@latest
# Project name: nagiflow-web
# Preset: Recommended
# TypeScript: No
# Install dependencies: (manual)
```

## Quick Start

```bash
cd nagiflow-web
pnpm install
cp .env.example .env
pnpm dev          # starts at http://localhost:5173
```

Make sure the NagiFlow backend is running on `http://localhost:8000`.

## Project Structure

```
src/
├── api/
│   ├── client.js         # Axios instance + JWT interceptors
│   └── index.js          # All API service modules
├── assets/styles/
│   └── main.scss         # Global styles, Neon Studio tokens
├── components/
│   ├── character/        # CharacterCard, PersonalityRadar, AssetUpload, SkillAssignPanel
│   ├── chat/             # MessageBubble
│   ├── knowledge/        # KnowledgePanel
│   ├── memory/           # MemoryPanel
│   └── layout/           # AppShell (sidebar + topbar)
├── composables/
│   ├── useWebSocket.js   # WS streaming (text deltas & audio chunks)
│   └── useAudioPlayer.js # Web Audio API sequential chunk player
├── plugins/
│   └── vuetify.js        # Theme, defaults, icons
├── router/
│   └── index.js          # Routes + auth guards
├── stores/
│   ├── auth.js           # JWT auth + user state
│   ├── app.js            # Snackbar, confirm dialog, drawer
│   └── characters.js     # Character list / current
└── views/
    ├── auth/             # LoginView, RegisterView
    ├── characters/       # CharacterListView, CharacterFormView, CharacterDetailView
    ├── chat/             # ChatView (WS streaming), ConversationsView
    ├── dashboard/        # DashboardView, SettingsView
    ├── knowledge/        # KnowledgeView
    ├── skills/           # SkillsView
    └── admin/            # AdminView
```

## Page Map

| Route | View | Description |
|-------|------|-------------|
| `/login` | LoginView | JWT login |
| `/register` | RegisterView | Account creation |
| `/` | DashboardView | Stats, quick-access, health |
| `/characters` | CharacterListView | Grid/list of all characters |
| `/characters/new` | CharacterFormView | Create character + Big Five sliders |
| `/characters/:id` | CharacterDetailView | Profile, skills, memory, knowledge tabs |
| `/characters/:id/edit` | CharacterFormView | Edit character |
| `/characters/:id/chat` | ChatView | Live streaming chat (text + audio WS) |
| `/conversations` | ConversationsView | All conversation history |
| `/knowledge` | KnowledgeView | RAG document manager + semantic search |
| `/skills` | SkillsView | Skills library browser |
| `/settings` | SettingsView | Profile & password |
| `/admin` | AdminView | Users table, system health, plugins (admin only) |

## WebSocket Streaming

`ChatView` connects to two NagiFlow WebSocket endpoints:

- **Text stream** (`/api/v1/ws/stream/text`) — LLM text deltas rendered in real-time with a blinking cursor.
- **Audio stream** (`/api/v1/ws/stream/audio`) — Binary WAV chunks piped into the Web Audio API via `useAudioPlayer`, enabling near-realtime TTS playback while the LLM is still generating.

The mode is toggled per-conversation via the ⚡ and 🔊 buttons in the chat header.

## Theme: Neon Studio

Dark space-blue base (`#070B16`) with:
- **Primary** — Cyan `#06B6D4`
- **Secondary** — Pink `#EC4899`
- **Accent** — Violet `#8B5CF6`
- **Tertiary** — Emerald `#10B981`

Global utility classes: `.glass`, `.glass-glow`, `.gradient-text`, `.glow-cyan`, `.chip-cyan/pink/violet/emerald`.