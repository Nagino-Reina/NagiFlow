# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NagiFlow is an extensible AI Vtuber streaming framework. It has two sub-projects:

- **`backend/`** — FastAPI + SQLAlchemy async Python backend
- **`web/`** — Vue 3 + Vuetify 4 frontend (TypeScript)

---

## Backend Commands

All backend commands run from the `backend/` directory with the virtualenv active.

```bash
# Install (editable + dev deps)
pip install -e ".[dev]"

# Run dev server (auto-reload)
uvicorn nagiflow.main:app --reload

# Or via the CLI entry point
nagiflow

# Tests
pytest
pytest tests/path/to/test_file.py::test_name   # single test

# Linting / formatting
ruff check .
ruff format .

# Type checking
mypy nagiflow/

# Database migrations (after changing SQLAlchemy models)
alembic revision --autogenerate -m "description"
alembic upgrade head
```

Config is loaded from `backend/.env` (copy `backend/.env.example`). Required: `SECRET_KEY`, `FIRST_ADMIN_EMAIL`, `FIRST_ADMIN_PASSWORD`.

---

## Frontend Commands

All frontend commands run from the `web/` directory. Uses **pnpm**.

```bash
pnpm dev          # dev server on :3000 (proxies /api → :8000)
pnpm build        # type-check + vite build
pnpm type-check   # vue-tsc only
pnpm lint         # eslint
pnpm lint:fix     # eslint --fix
```

The dev server proxies `/api/*` to `http://localhost:8000`, so both HTTP and WebSocket calls work without CORS changes during development. `VITE_API_BASE_URL` overrides the default `/api/v1` base.

---

## Backend Architecture

### Layer summary

| Layer | Location | Purpose |
|---|---|---|
| Config | `nagiflow/config.py` | Single `Settings` (pydantic-settings) singleton; reads `.env` |
| Models | `nagiflow/models/` | SQLAlchemy async ORM — User, Character, Conversation, Message, Memory, Knowledge, Skill |
| Schemas | `nagiflow/schemas/` | Pydantic v2 request/response DTOs |
| Services | `nagiflow/services/` | Business logic (auth, character, conversation, memory, knowledge, embedding) |
| API routes | `nagiflow/api/v1/` | FastAPI routers, one file per domain |
| LLM | `nagiflow/llm/` | Provider abstraction + `CharacterAgent` |
| TTS | `nagiflow/tts/` | Provider abstraction; VoicevoxProvider built-in |
| Skills | `nagiflow/skills/` | Skill registry + built-in skills (web_search, calculator) |
| Plugins | `nagiflow/plugins/` | Dynamic loader from `workspace/plugins/` |
| Core | `nagiflow/core/` | DB engine, security (JWT), workspace paths, exceptions |

### Startup sequence (`main.py` lifespan)

1. `workspace.ensure_structure()` — create workspace directories
2. `create_all_tables()` — SQLAlchemy create-all (dev); use Alembic for migrations
3. `skill_registry.sync_to_db()` — upsert built-in skills
4. `AuthService.ensure_admin()` — bootstrap first admin if `FIRST_ADMIN_EMAIL` set
5. `plugin_loader.load_from_directory()` — import plugins from `workspace/plugins/`

### CharacterAgent (`nagiflow/llm/agent.py`)

The central AI object. Stateless per-request; accepts conversation history + user message, injects memory/knowledge context into the system prompt, then calls the configured LLM provider. Supports both one-shot (`generate`) and streaming (`stream`) modes.

System prompt is built from: character name/description → Big Five personality scores → custom fields → `system_prompt` field → retrieved memories → retrieved knowledge.

### WebSocket streaming

- **Text stream**: `WS /api/v1/ws/stream/text` — sends `{ "type": "delta", "content": "..." }` frames, ends with `{ "type": "done" }`
- **Audio stream**: `WS /api/v1/ws/stream/audio` — sends binary WAV frames (one per synthesised sentence) then a `{ "type": "done" }` text frame

Auth for WebSocket: pass `token` field in the initial JSON message (not HTTP header).

### Plugin system

Drop a Python package into `workspace/plugins/`. Implement `BasePlugin` with `async setup()` / `async teardown()` methods. Use `setup()` to register custom LLM providers (`register_llm_provider`), TTS providers (`register_tts_provider`), and skills (`skill_registry.register`).

---

## Frontend Architecture

### Tech stack

- Vue 3 (Composition API, `<script setup>`)
- Vuetify 4 (auto-imported components via `vite-plugin-vuetify`)
- Pinia stores
- Vue Router 5
- Axios (`web/src/api/client.ts`) with automatic JWT refresh interceptor

### Routing

`AppShell.vue` wraps all authenticated routes as a layout parent. Navigation guards in `router/index.ts` handle: redirect to `/login` if unauthenticated, redirect away from guest routes if already authenticated, block `/admin` unless `isAdmin`.

### Pinia stores

| Store | File | Responsibility |
|---|---|---|
| `useAuthStore` | `stores/auth.ts` | Tokens (localStorage), user profile, login/logout/refresh |
| `useAppStore` | `stores/app.ts` | Global UI state (drawer, theme, snackbar) |
| `useCharactersStore` | `stores/characters.ts` | Character list cache |

### API layer

`web/src/api/index.ts` exports typed API modules (`authApi`, `charactersApi`, etc.) that all use the shared `client` Axios instance. The client auto-attaches `Authorization: Bearer <token>` and silently retries with a fresh token on 401. If refresh fails it dispatches an `auth:logout` DOM event, which `useAuthStore` listens for.

### Key composables

- `useWebSocket.ts` — wraps WebSocket with connect/disconnect lifecycle, message queue
- `useAudioPlayer.ts` — plays streaming WAV chunks from the audio WebSocket

---

## Workspace directory

All runtime files live under `workspace/` (configurable via `WORKSPACE_DIR`):

```
workspace/
├── characters/{id}/   avatar, voice samples, Live2D/3D models
├── knowledge/         uploaded text/markdown files
├── plugins/           custom plugin packages
├── audio_cache/       synthesised WAV files
└── nagiflow.db        SQLite database (default)
```