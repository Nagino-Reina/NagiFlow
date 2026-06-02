# Changelog

All notable changes to NagiFlow are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/); versions track the
[roadmap milestones](docs/15-roadmap-and-milestones.md).

## [0.2.0] — P1 · MVP

The smallest end-to-end product: create a character, give it a voice, and hold a voiced chat.

### Added
- **Character management** — create / read / update / delete / duplicate / list; basic info
  (name, aliases, description, persona, tags, language, status), **Big Five** personality with
  a documented behavior mapping, and **portrait** image upload (FR-CM-1/2/3/4).
- **Voice** — zero-shot cloning (reference clip + transcript) and voice-design via the in-process
  **VoxCPM** provider, with sample preview (FR-CM-5/7).
- **Chat** — single-user local auth + guest sessions; synchronous turns through **Ollama** using
  the recent-conversation window; emotion/affect engine; provider error envelope and fallback.
- **Roleplay** — editable global roleplay prompt (Settings); reply audio playback with action
  /stage directions stripped before TTS.
- **Observability** — token/usage accounting and a live system-status bar (CPU/RAM/GPU/usage)
  pushed over a WebSocket (FR-OBS-1/3).

### Changed
- Downgraded the supported Python to **3.12** (`>=3.12,<3.13`) for broad local-provider wheel
  coverage.
- Code style is now owned by `ruff format` (backend) and `eslint` (frontend); see the README
  *Development* section.

### Notes
- VoxCPM voice needs CUDA-enabled PyTorch; CPU synthesis is impractically slow.
- Persistent per-character memory (FR-MM-6) is deferred to **P3**.

## [0.1.0] — P0 · Foundations

- FastAPI backend + Vuetify SPA shell + brand theme; layered config and workspace layout.
- SQLite + SQLAlchemy + Alembic; provider/adapter interfaces with a stub provider.
- One-click launcher (`nagiflow up`): prereq checks, single-terminal logs, clean shutdown.
