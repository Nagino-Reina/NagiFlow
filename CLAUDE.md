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

### Plugin-first design

The core `nagiflow/` package is a **pure framework** — no LLM/TTS/avatar logic lives there. All service providers are **plugins** in `backend/plugins/` (built-in, auto-loaded) or `workspace/plugins/` (user-installed).

| Layer | Location | Purpose |
|---|---|---|
| Config | `nagiflow/config.py` | `Settings` singleton (pydantic-settings); reads `.env` |
| Plugin base | `nagiflow/plugin/base.py` | All abstract base classes: `BaseLLMProvider`, `BaseTTSProvider`, `BaseAvatarProvider`, `BaseEmbeddingProvider`, `BaseSkill`, `BasePlugin` |
| Plugin registry | `nagiflow/plugin/registry.py` | `ProviderRegistry` singleton — `register_*/get_*/list_*` for each provider type; `sync_skills_to_db()` |
| Plugin loader | `nagiflow/plugin/loader.py` | Scans `backend/plugins/` (built-in) then `workspace/plugins/` (user); calls `plugin.setup()` |
| Models | `nagiflow/models/` | SQLAlchemy async ORM — User, Character, Conversation, Message, Memory, Knowledge, Skill, Script, ScriptScene, ScriptLine, TrainingDataset, TrainingItem |
| Schemas | `nagiflow/schemas/` | Pydantic v2 DTOs matching the models |
| Services | `nagiflow/services/` | Business logic; use `registry.get_llm/tts()` not direct imports |
| API routes | `nagiflow/api/v1/` | FastAPI routers — one file per domain |
| Core | `nagiflow/core/` | DB engine, security (JWT), workspace paths, exceptions, EventBus |

### Built-in plugins (`backend/plugins/`)

| Directory | Provider name | Type |
|---|---|---|
| `llm_ollama/` | `"ollama"` | LLM |
| `llm_openai_compat/` | `"openai_compat"` | LLM |
| `tts_voxcpm2/` | `"voxcpm2"` | TTS (default) |
| `tts_voicevox/` | `"voicevox"` | TTS |
| `avatar_pngtuber/` | `"pngtuber"` | Avatar (default) |
| `skill_calculator/` | `"calculator"` | Skill |
| `skill_web_search/` | `"web_search"` | Skill |

### Startup sequence (`main.py` lifespan)

1. `workspace.ensure_structure()` — create workspace directories
2. `create_all_tables()` — SQLAlchemy create-all (dev); use Alembic for migrations
3. `plugin_loader.load_all(workspace.plugins_dir())` — load built-in then user plugins
4. `registry.sync_skills_to_db(db)` — upsert registered skills to DB
5. `AuthService.ensure_admin()` — bootstrap first admin if `FIRST_ADMIN_EMAIL` set

### CharacterAgent (`nagiflow/services/agent.py`)

Stateless per-request. Accepts conversation history + user message, injects memory/knowledge context into the system prompt, calls `registry.get_llm(character.llm_provider)`. Supports `generate()` (one-shot) and `stream()` (async generator).

System prompt order: character name/description → Big Five personality scores → custom fields → `system_prompt` → retrieved memories → retrieved knowledge.

### WebSocket streaming (`nagiflow/api/v1/streaming.py`)

- **Text stream**: `WS /api/v1/ws/stream/text` — frames: `{ "type": "delta", "content": "..." }`, `{ "type": "anim_state", "state": "talking"|"idle", "expression": "..." }`, `{ "type": "done" }`
- **Audio stream**: `WS /api/v1/ws/stream/audio` — binary WAV frames (one per synthesised sentence), wrapped by `anim_state` frames, ends with `{ "type": "done" }`

Auth: pass `token` in the initial JSON message.

### PNGTuber avatar system

States: `idle`, `talking`, `blinking` × Expressions: `default`, `happy`, `sad`, `angry`, `surprised`

PNGs stored at `workspace/characters/{id}/avatar/{state}_{expression}.png`. The `PNGTuberProvider` (`plugins/avatar_pngtuber/`) computes state from audio activity. The frontend `PNGTuberViewer.vue` component adds an autonomous blink timer and CSS animation.

### Script editor

`Script → ScriptScene (ordered) → ScriptLine (ordered)` — each line can have an associated character + text + TTS audio. `ScriptService` handles CRUD, per-line/all-line TTS synthesis, and ZIP export (WAVs + SRT subtitles).

### Training data management

`TrainingDataset → TrainingItem` (text + audio + quality rating). `TrainingService` handles item add/generate/delete, ZIP export (WAVs + metadata.json). Denormalized `item_count` and `total_duration_ms` counters on the dataset.

---

## Frontend Architecture

### Tech stack

- Vue 3 (Composition API, `<script setup>`)
- Vuetify 4 (auto-imported components via `vite-plugin-vuetify`)
- Pinia stores
- Vue Router 5
- Axios (`web/src/api/client.ts`) with automatic JWT refresh interceptor

### Key pages

| Route | Component | Purpose |
|---|---|---|
| `/` | `Dashboard.vue` | Overview |
| `/characters` | `CharacterList.vue` | Character management |
| `/characters/:id/chat` | `Chat.vue` | Live chat with PNGTuberViewer |
| `/scripts` | `Scripts.vue` | Script list |
| `/scripts/:id` | `ScriptEditor.vue` | Scene + line editor, TTS, export |
| `/training` | `Training.vue` | Dataset management |
| `/knowledge` | `Knowledge.vue` | RAG knowledge base |
| `/admin` | `Admin.vue` | Admin panel |

### Key composables

- `useWebSocket.ts` — wraps WebSocket; callbacks: `onDelta`, `onDone`, `onError`, `onAudio`, `onAnimState`
- `useAudioPlayer.ts` — plays streaming WAV chunks

### PNGTuberViewer (`components/character/PNGTuberViewer.vue`)

Props: `characterId`, `currentState` (`'idle'|'talking'`), `currentExpression`, `size`. Has autonomous blink timer (3–7 s random). Receives `anim_state` WebSocket frames via `Chat.vue` → `onAnimState`.

### API modules (`web/src/api/index.ts`)

`authApi`, `usersApi`, `charactersApi`, `conversationsApi`, `memoryApi`, `knowledgeApi`, `skillsApi`, `scriptsApi`, `trainingApi`, `providersApi`, `healthApi`

---

## Workspace directory

```
workspace/
├── characters/{id}/
│   ├── avatar/         PNGTuber PNGs: {state}_{expression}.png
│   ├── voice_samples/
│   └── models/
├── knowledge/
├── plugins/            user-installed plugin packages
├── audio_cache/        synthesised TTS WAV files
├── training/           training dataset WAV files
└── nagiflow.db         SQLite database (default)
```
