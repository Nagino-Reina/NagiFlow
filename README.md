# NagiFlow

An extensible AI Vtuber streaming framework that wires together **LLM**, **TTS**, and **Live2D / 3D character models** into a unified, modular backend.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [WebSocket Streaming Protocol](#websocket-streaming-protocol)
- [Plugin System](#plugin-system)
- [Agent Skills](#agent-skills)
- [Character Setup](#character-setup)
- [Development](#development)
- [Project Structure](#project-structure)

---

## Features

| Area | Details |
|------|---------|
| **LLM** | Ollama (`gpt-oss:20b` default) and OpenAI-compatible endpoints; streaming and one-shot |
| **TTS** | VOICEVOX (sentence-level streaming synthesis); pluggable provider interface |
| **Characters** | Big Five personality, custom config, system prompt, per-character LLM/TTS overrides |
| **Assets** | Avatar images, voice reference samples, Live2D (`.model3.json`, `.moc3`, `.zip`) and 3D (`.vrm`, `.glb`, `.gltf`) models |
| **Memory** | Per-character, per-user long-term memory with cosine-similarity semantic search |
| **Knowledge Base** | RAG pipeline — upload text/markdown files, automatic chunking + embedding, semantic retrieval |
| **Skills** | Modular agent tools (web search, calculator built-in); extendable via plugins |
| **Auth** | JWT access + refresh tokens, bcrypt passwords, role-based access control (user / moderator / admin) |
| **Streaming** | WebSocket text-delta stream and concurrent LLM+TTS audio stream |
| **Plugins** | Drop Python packages into `workspace/plugins/` for zero-config loading at startup |
| **Database** | SQLite default; swap to PostgreSQL or any SQLAlchemy-supported DB via `DATABASE_URL` |
| **Workspace** | All dynamic files (models, audio cache, knowledge files) isolated under `workspace/` |

---

## Architecture

```
nagiflow/
├── api/v1/          HTTP REST + WebSocket routes
├── core/            Database engine, security, workspace manager, exceptions
├── llm/             LLM provider abstraction + CharacterAgent
│   └── providers/   OllamaProvider, OpenAICompatProvider
├── tts/             TTS provider abstraction
│   └── providers/   VoicevoxProvider
├── services/        Business logic (auth, character, conversation, memory, knowledge)
├── models/          SQLAlchemy ORM models
├── schemas/         Pydantic request/response schemas
├── skills/          Skill (tool) registry + built-in skills
│   └── builtin/     WebSearchSkill, CalculatorSkill
└── plugins/         Plugin base class + dynamic loader
```

**Request flow (streaming audio)**:
```
Client → WebSocket /ws/stream/audio
  → JWT auth → ConversationService.stream_tts_with_llm()
    → LLM stream (sentence accumulation)
    → VoicevoxProvider.synthesize(sentence) → WAV bytes
  ← Binary WebSocket frame (WAV chunk per sentence)
  ← { "type": "done" } text frame
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai/) running locally with `gpt-oss:20b` pulled
- [VOICEVOX](https://voicevox.hiroshiba.jp/) engine running on port 50021

### Installation

```bash
git clone https://github.com/yourorg/nagiflow.git
cd nagiflow

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e ".[dev]"

cp .env.example .env
# Edit .env – set SECRET_KEY, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD
```

### Run

```bash
# Development (auto-reload)
uvicorn nagiflow.main:app --reload

# Or via the CLI entry point
nagiflow
```

Visit **http://localhost:8000/docs** for the interactive OpenAPI documentation.

---

## Configuration

All settings are read from environment variables or a `.env` file.  See [.env.example](.env.example) for the full list.

Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | *(required)* | JWT signing key — use a random 32-byte hex string |
| `DATABASE_URL` | `sqlite+aiosqlite:///workspace/nagiflow.db` | SQLAlchemy async URL |
| `DEFAULT_LLM_PROVIDER` | `ollama` | `ollama` or `openai_compat` |
| `DEFAULT_LLM_MODEL` | `gpt-oss:20b` | Model name passed to the provider |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama HTTP endpoint |
| `OPENAI_API_KEY` | — | Used when `DEFAULT_LLM_PROVIDER=openai_compat` |
| `DEFAULT_TTS_PROVIDER` | `voicevox` | TTS provider name |
| `VOICEVOX_BASE_URL` | `http://localhost:50021` | VOICEVOX HTTP endpoint |
| `WORKSPACE_DIR` | `./workspace` | Root path for all dynamic files |
| `FIRST_ADMIN_EMAIL` | — | Bootstrapped on first startup (skipped if empty) |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins (JSON array) |

### PostgreSQL

```dotenv
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/nagiflow
```

Install the extra: `pip install -e ".[postgres]"`

---

## API Reference

Full Swagger UI: `GET /docs` | ReDoc: `GET /redoc`

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/auth/register` | Register a new user |
| `POST` | `/api/v1/auth/login` | Login, receive access + refresh tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh the access token |
| `GET`  | `/api/v1/auth/me` | Get current user profile |

All protected routes require the header: `Authorization: Bearer <access_token>`

### Characters

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/characters` | Create a character |
| `GET`  | `/api/v1/characters` | List your characters |
| `GET`  | `/api/v1/characters/{id}` | Get character detail |
| `PATCH`| `/api/v1/characters/{id}` | Update character |
| `DELETE`| `/api/v1/characters/{id}` | Delete character + workspace |
| `POST` | `/api/v1/characters/{id}/avatar` | Upload avatar image |
| `POST` | `/api/v1/characters/{id}/voice-sample` | Upload voice reference |
| `POST` | `/api/v1/characters/{id}/model?model_type=live2d` | Upload Live2D / 3D model |
| `GET`  | `/api/v1/characters/{id}/skills` | List assigned skills |
| `POST` | `/api/v1/characters/{id}/skills` | Assign a skill |
| `DELETE`| `/api/v1/characters/{id}/skills/{skill_id}` | Remove skill |

### Conversations & Chat

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/conversations` | Create a conversation |
| `GET`  | `/api/v1/conversations` | List conversations |
| `GET`  | `/api/v1/conversations/{id}` | Get conversation + history |
| `DELETE`| `/api/v1/conversations/{id}` | Delete conversation |
| `POST` | `/api/v1/conversations/characters/{char_id}/chat` | One-shot chat |
| `POST` | `/api/v1/conversations/characters/{char_id}/tts` | Generate TTS for text |

### Memory

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/characters/{id}/memories` | Add memory |
| `GET`  | `/api/v1/characters/{id}/memories` | List memories |
| `POST` | `/api/v1/characters/{id}/memories/search` | Semantic search |
| `PATCH`| `/api/v1/characters/{id}/memories/{mem_id}` | Update memory |
| `DELETE`| `/api/v1/characters/{id}/memories/{mem_id}` | Delete memory |
| `DELETE`| `/api/v1/characters/{id}/memories` | Clear all memories |

### Knowledge Base

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/knowledge` | Create document from text |
| `POST` | `/api/v1/knowledge/upload` | Upload text/markdown file |
| `GET`  | `/api/v1/knowledge` | List documents |
| `GET`  | `/api/v1/knowledge/{id}` | Get document |
| `DELETE`| `/api/v1/knowledge/{id}` | Delete document |
| `POST` | `/api/v1/knowledge/search` | Semantic search |

### Skills

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/api/v1/skills` | List all available skills |
| `GET`  | `/api/v1/skills/{id}` | Get skill detail |
| `PATCH`| `/api/v1/skills/{id}/toggle` | Enable/disable skill (admin) |

---

## WebSocket Streaming Protocol

### Text Stream: `WS /api/v1/ws/stream/text`

**Client sends** (single JSON message):
```json
{
  "token": "<access_token>",
  "character_id": "<uuid>",
  "conversation_id": "<uuid or null>",
  "message": "Tell me a story!"
}
```

**Server sends** (sequence of JSON text frames):
```json
{ "type": "delta", "content": "Once" }
{ "type": "delta", "content": " upon" }
{ "type": "delta", "content": " a time..." }
{ "type": "done",  "conversation_id": "<uuid>" }
```

### Audio Stream: `WS /api/v1/ws/stream/audio`

Same client message format.  Server responds with:
- **Binary frames** — raw WAV audio chunks (one per synthesised sentence)
- **Final text frame** — `{ "type": "done" }`

---

## Plugin System

Place a Python package in `workspace/plugins/` and it will be loaded automatically at startup.

```
workspace/plugins/my_plugin/__init__.py
```

```python
from nagiflow.plugins.base import BasePlugin, PluginMeta
from nagiflow.skills.registry import skill_registry
from nagiflow.tts import register_tts_provider
from .my_skill import MySkill
from .my_tts import MyTTSProvider

class MyPlugin(BasePlugin):
    meta = PluginMeta(name="my_plugin", version="1.0.0", author="You")

    async def setup(self) -> None:
        skill_registry.register(MySkill)
        register_tts_provider("my_tts", MyTTSProvider)

    async def teardown(self) -> None:
        pass  # cleanup if needed
```

See `examples/plugins/weather_plugin/` for a complete example.

---

## Agent Skills

Skills are Python classes that implement `BaseSkill` and expose an `async execute(**kwargs) -> str` method.

**Built-in skills:**
- `web_search` — DuckDuckGo instant answers
- `calculator` — Safe AST-based math evaluator

**Creating a custom skill:**
```python
from nagiflow.skills.base import BaseSkill, SkillMeta, SkillParameter

class MySkill(BaseSkill):
    meta = SkillMeta(
        name="my_skill",
        display_name="My Skill",
        description="Does something useful.",
        parameters=[
            SkillParameter(name="input", type="string", description="Input text"),
        ],
    )

    async def execute(self, input: str, **kwargs) -> str:
        return f"Processed: {input}"
```

Register it in a plugin's `setup()` via `skill_registry.register(MySkill)`.

---

## Character Setup

```json
POST /api/v1/characters
{
  "name": "Nagi",
  "description": "A cheerful AI Vtuber who loves games and anime.",
  "system_prompt": "You are Nagi. Respond in a casual, upbeat tone.",
  "personality": {
    "big_five": {
      "openness": 82,
      "conscientiousness": 55,
      "extraversion": 78,
      "agreeableness": 88,
      "neuroticism": 28
    },
    "custom": {
      "catchphrase": "Let's go~!",
      "speech_style": "casual",
      "interests": ["gaming", "anime", "music"]
    }
  },
  "llm_provider": "ollama",
  "llm_model": "gpt-oss:20b",
  "tts_provider": "voicevox",
  "tts_speaker_id": 1,
  "model_type": "live2d",
  "is_public": false
}
```

Then upload assets:
```bash
curl -X POST /api/v1/characters/{id}/avatar -F file=@avatar.png
curl -X POST /api/v1/characters/{id}/voice-sample -F file=@voice.wav
curl -X POST "/api/v1/characters/{id}/model?model_type=live2d" -F file=@model.zip
```

---

## Development

```bash
# Run tests
pytest

# Code style
ruff check .
ruff format .

# Type checking
mypy nagiflow/

# Generate a new Alembic migration after model changes
alembic revision --autogenerate -m "add_new_column"
alembic upgrade head
```

---

## Project Structure

```
nagiflow/
├── alembic/                 Database migration scripts
├── examples/
│   └── plugins/
│       └── weather_plugin/  Example plugin
├── nagiflow/
│   ├── api/
│   │   └── v1/              Route handlers (auth, users, characters, …)
│   ├── core/                Database, security, workspace, exceptions
│   ├── llm/
│   │   └── providers/       OllamaProvider, OpenAICompatProvider
│   ├── tts/
│   │   └── providers/       VoicevoxProvider
│   ├── models/              SQLAlchemy ORM models
│   ├── schemas/             Pydantic v2 schemas
│   ├── services/            Business logic layer
│   ├── skills/
│   │   └── builtin/         WebSearchSkill, CalculatorSkill
│   ├── plugins/             Plugin base + loader
│   ├── config.py            Application settings
│   └── main.py              FastAPI app factory + entry point
├── tests/
├── .env.example
├── alembic.ini
└── pyproject.toml
```
