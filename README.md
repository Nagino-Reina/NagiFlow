# NagiFlow

**Local-first, modular AI VTuber studio.** Two core flows, both on your own machine:

1. **Script production** — author (or import + ASR-segment) a multi-speaker script, then render
   it to voiced multimedia (audio, optional video + subtitles) saved locally.
2. **Live streaming** — a character responds in real time to user dialogue or external input
   (live chat, screen content), driving voice + animation as it speaks.

Everything else — characters, voice, personality, emotion, memory, observability — supports
these two flows, and every external service (LLM, TTS, ASR, storage) sits behind a swappable
provider seam.

> Status: **P0 — Foundations** complete. The skeleton runs end to end (FastAPI backend +
> Vuetify SPA shell + brand theme, SQLite/ORM/Alembic, provider interfaces with a stub
> provider, and a one-click launcher). Feature work (character voicing, chat, scripts,
> live) lands in P1+ — see [docs/15 Roadmap](docs/15-roadmap-and-milestones.md).

---

## Quick start

### Prerequisites
- **Python 3.12** and [**uv**](https://docs.astral.sh/uv/) (backend deps + venv)
- **Node.js 18+** and [**pnpm**](https://pnpm.io/) (frontend)
- *Optional:* **ffmpeg** (media/ASR, P2+), **Ollama** (local LLM — an offline echo
  provider is used if absent)

Run `nagiflow check` to verify your toolchain at any time.

### Install
```bash
# Backend (from repo root)
cd backend
uv pip install -e .

# Frontend
cd ../web
pnpm install
```

### Run
```bash
nagiflow up
```
The launcher checks prerequisites, backs up the database, applies migrations, starts the
backend (uvicorn) and the Vite dev server, multiplexes both logs into one terminal, waits
until healthy, and opens the app. **Ctrl-C** shuts down NagiFlow's own processes only —
external services like Ollama are left running.

| Command | What it does |
|---|---|
| `nagiflow up` | Dev mode: backend + Vite dev server (HMR), single-terminal logs |
| `nagiflow up --prod` | Build the SPA and serve it from FastAPI (one process, one port) |
| `nagiflow up --no-browser` | Don't auto-open the browser |
| `nagiflow check` | Run prerequisite checks and exit |

- **Dev:** SPA on `http://localhost:5173`, proxying `/api` → backend on `:8000`.
- **Prod:** everything on `http://127.0.0.1:8000` (FastAPI serves the built SPA).
- API docs (OpenAPI): `http://127.0.0.1:8000/docs`.

---

## Layout

```
backend/    FastAPI app — API, services, providers, jobs, models, Alembic migrations
web/        Vue 3 + Vuetify SPA — shell, stores, API/WS clients, i18n (zh-Hant / en)
docs/       Design docs (vision, SRS, architecture, API, features, roadmap)
workspace/  Local data — SQLite DB, media, logs, backups (created on first run, git-ignored)
```

## Configuration

Layered, highest precedence last: **built-in defaults → `workspace/config/app.toml` →
environment (`NAGIFLOW_*` / `.env`)**. Secrets come from the environment only and are never
read from the committed workspace config. See `backend/.env.example` and
[docs/14 §4](docs/14-runtime-and-deployment.md).

## Documentation

Start with [docs/01 Vision](docs/01-vision-and-scope.md) and
[docs/03 Architecture](docs/03-system-architecture.md); the
[Roadmap](docs/15-roadmap-and-milestones.md) tracks phase scope and exit criteria.

## License

[MIT](LICENSE). Integrated third-party components keep their own licenses; optional
renderer modules with non-MIT terms (e.g. Live2D Cubism SDK) ship separately so the core
stays unencumbered.
