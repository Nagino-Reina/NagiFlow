# 02 · Requirements Specification (SRS)

| | |
|---|---|
| **Document** | Software Requirements Specification |
| **Doc ID** | NF-02 |
| **Version** | 0.1 (Draft) |
| **Last updated** | 2026-05-30 |
| **Related** | [01 Vision](01-vision-and-scope.md), [03 Architecture](03-system-architecture.md), feature docs [07](07-feature-script-management.md)–[13](13-runtime-and-deployment.md) |

---

## 1. Purpose & scope

This document specifies **what** NagiFlow must do and the qualities it must exhibit. It is the contract between product intent ([01](01-vision-and-scope.md)) and design ([03](03-system-architecture.md) onward). Functional requirements are grouped by area and carry stable IDs that feature documents trace against.

**Conventions**

- IDs: `FR-<AREA>-<n>` functional, `NFR-<AREA>-<n>` non-functional.
- Areas: `SM` Script Mgmt · `CM` Character Mgmt · `MM` Multi-user & Memory · `MOD` Modules · `RT` Realtime & Media · `OBS` Observability · `SYS` Platform/Runtime · `API` API.
- Priority: **M** Must, **S** Should, **C** Could, **W** Won't-for-now (MoSCoW).
- Each requirement states intent and, where useful, acceptance criteria (AC).

## 2. Overall description

### 2.1 Product perspective
NagiFlow is a self-contained, locally-installed application: a **FastAPI** backend serving a **Vuetify** single-page frontend, persisting to a local **workspace folder + SQLite**, and integrating AI services (LLM, TTS, ASR) and storage through a **provider/module** layer. Bundled defaults (Ollama LLM, VoxCPM TTS) are themselves official modules.

### 2.2 User classes
- **Guest** — anonymous; basic conversation only.
- **User (local account)** — full authoring, configuration, and operations.
- **Module developer** — interacts via the SDK/extension surface rather than the UI alone.

(Roles and the exact capability matrix are defined in [09](09-feature-multiuser-memory-and-privacy.md).)

### 2.3 Operating environment
- OS: Windows 10/11, macOS (Apple Silicon/Intel), modern Linux.
- Runtime: Python (backend) + Node/Vite-built static assets (frontend).
- Optional GPU (NVIDIA/Apple Metal) for fast local LLM/TTS; CPU fallback supported with degraded performance.
- External (default): Ollama; VoxCPM runtime; ffmpeg; optional ASR model.

### 2.4 Design & implementation constraints
- Backend core **must** be FastAPI; frontend core **must** be Vuetify.
- Defaults **must** be local and lightweight; cloud/external integrations are opt-in via modules.
- Data default **must** be local workspace + SQLite, with storage and DB seams left pluggable.

### 2.5 Assumptions & dependencies
See [01 §9](01-vision-and-scope.md). NagiFlow depends on the availability and licenses of integrated OSS (e.g. VoxCPM, Apache-2.0).

---

## 3. Functional requirements

### 3.1 Script management (`SM`) — see [07](07-feature-script-management.md)

| ID | Pri | Requirement |
|---|---|---|
| FR-SM-1 | M | Users can create, read, update, delete, duplicate, and list **scripts**. |
| FR-SM-2 | M | A script contains an ordered set of **lines**; each line has: dialogue text, an associated character (by reference or free name), and an ordering/timestamp. |
| FR-SM-3 | M | Each line supports optional voice-direction metadata: **reference audio**, **style guidance** (free text and/or structured), **speech rate/speed**, language, and notes. |
| FR-SM-4 | M | Users can reorder lines and edit any field; changes are validated and persisted. |
| FR-SM-5 | M | Users can **import audio/video files** and have them transcribed into a script via **ASR**, producing lines with text and timestamps. |
| FR-SM-6 | S | Imported audio/video supports optional **speaker separation/diarization**, mapping segments to distinct characters/speakers for review. |
| FR-SM-7 | M | ASR import runs as a **tracked background job** with progress, cancellation, and a review/correction step before commit. |
| FR-SM-8 | M | Users can **generate media** (audio, optionally video) from selected lines, applying each line's voice direction and the assigned character's voice. |
| FR-SM-9 | S | Media generation can **export subtitles** (e.g. SRT/VTT) aligned to lines/timestamps. |
| FR-SM-10 | S | Scripts (and their reference audio) can be **exported as training data** for voice fine-tuning (text + audio pairs in a defined dataset format). |
| FR-SM-11 | S | Scripts import/export in machine-readable formats (JSON; subtitle import for SRT/VTT). |
| FR-SM-12 | C | Line-level **takes/versions** allow keeping alternative renderings/wordings. |

**AC (representative)** — FR-SM-5: Given a supported media file, the system produces a draft script whose line count and timestamps reflect detected speech segments, presented for review; committing creates a persisted script.

### 3.2 Character management (`CM`) — see [08](08-feature-character-management.md)

| ID | Pri | Requirement |
|---|---|---|
| FR-CM-1 | M | Users can create, read, update, delete, duplicate, and list **characters**. |
| FR-CM-2 | M | A character has **basic info**: name, aliases, portrait/avatar asset, description, default language, tags, and lifecycle status (draft/active/archived). |
| FR-CM-3 | M | A character has an editable **persona** (system prompt / behavioral description). |
| FR-CM-4 | M | A character has a **Big Five (OCEAN) personality** profile with five 0–100 trait values that demonstrably influence dialogue behavior. |
| FR-CM-5 | M | A character has one or more **voice models**; the default path produces a usable voice via VoxCPM **voice design** (text description) and/or **zero-shot cloning** (reference audio). |
| FR-CM-6 | S | Users can run **voice fine-tune training** for a character from a dataset (e.g. from scripts/reference audio), producing a stored voice artifact that can be selected, previewed, versioned, and rolled back. |
| FR-CM-7 | M | Users can **preview** a character's voice by synthesizing sample text. |
| FR-CM-8 | M | A character has a **memory bank**; memory is scoped per user and per character (and may include cross-character interaction memory) per [09](09-feature-multiuser-memory-and-privacy.md). |
| FR-CM-9 | M | Users can **inspect and edit** a character's memory entries (subject to scope/permission). |
| FR-CM-10 | M | Users can **export a character as a portable package** (profile, Big Five, voice config; voice artifacts and memory optional) and **import** it on another install. |
| FR-CM-11 | S | Character export offers **privacy options** (e.g. exclude user-linked memory by default). |
| FR-CM-12 | S | A character can be flagged **guest-visible** to control whether guests may converse with it. |

**AC (representative)** — FR-CM-4: Adjusting a trait (e.g. raising Extraversion) changes how the character's generated responses present (verbosity/expressiveness) in a consistent, documented way ([08 §3](08-feature-character-management.md)).

### 3.3 Multi-user & memory (`MM`) — see [09](09-feature-multiuser-memory-and-privacy.md)

| ID | Pri | Requirement |
|---|---|---|
| FR-MM-1 | M | The system supports **multiple users** and **multiple characters** concurrently. |
| FR-MM-2 | M | Initial access is as a **guest** without login; guests can perform **basic operations** (e.g. converse with guest-visible characters) but **not advanced operations**. |
| FR-MM-3 | M | Users can create/sign in to a **local account** to unlock advanced operations. |
| FR-MM-4 | M | A character stores **memories scoped to each user** it interacts with. |
| FR-MM-5 | S | A character can retain **memories from interacting with other characters** (cross-character memory). |
| FR-MM-6 | M | Memory **retrieval is scope-aware**: a conversation between character C and user U draws on (C,U) memory and C's general memory, and may draw on cross-character memory when permitted. |
| FR-MM-7 | M | A **sensitive mode** ensures that, when enabled, a character does **not** reveal or reference **other users'** information during a conversation. |
| FR-MM-8 | M | Sensitive mode is enforceable at multiple layers (retrieval filtering and prompt instruction at minimum). |
| FR-MM-9 | S | Sensitive mode can be configured globally, per character, and/or per conversation, with a safe default. |
| FR-MM-10 | M | Deleting a user removes that user's scoped memories; users can request deletion of their data. |
| FR-MM-11 | M | A **permission matrix** defines guest vs user capabilities and is enforced server-side. |
| FR-MM-12 | S | **Guest sessions have a bounded lifecycle**: ephemeral guest principals and their scoped memory are garbage-collected after expiry/inactivity, and generative use is rate/resource-capped per guest to protect a shared instance. |

**AC (representative)** — FR-MM-7: With sensitive mode on, no response from character C to user U contains information sourced from another user's scoped memory, verified by retrieval-scope tests and prompt review.

### 3.4 Modularity & extensions (`MOD`) — see [06](06-module-and-extension-system.md)

| ID | Pri | Requirement |
|---|---|---|
| FR-MOD-1 | M | The platform supports **modules** that extend functionality without modifying core source. |
| FR-MOD-2 | M | Modules can contribute **Agent Skills** (tools a character/agent can invoke). |
| FR-MOD-3 | M | Modules can contribute **Connectors** (integrations with external services/platforms). |
| FR-MOD-4 | S | Modules can contribute **framework extensions** (hooks/middleware) and **UI extensions** (panels/pages/widgets). |
| FR-MOD-5 | M | Modules can contribute **provider implementations** for LLM, TTS, ASR, Storage, and Vector Store. |
| FR-MOD-6 | M | The default **LLM (Ollama)** and **TTS (VoxCPM)** integrations are delivered as **official modules / sub-projects** serving as reference examples. |
| FR-MOD-7 | M | Each module declares a **manifest** (identity, version, contributions, permissions/capabilities, compatibility). |
| FR-MOD-8 | M | Modules can be **discovered, installed, enabled, disabled, and configured** locally; module-contributed routes are namespaced. |
| FR-MOD-9 | S | An **SDK / documented interfaces** exist for each extension type, with access to core services (config, logging, jobs, persistence as permitted). |
| FR-MOD-10 | S | Module **permissions/capabilities** are declared and gated; the system can constrain what a module may access. |
| FR-MOD-11 | C | Modules can be distributed as folders/archives now, with a registry as a future option. |

### 3.5 Realtime & media generation (`RT`) — see [10](10-feature-realtime-and-media-generation.md)

| ID | Pri | Requirement |
|---|---|---|
| FR-RT-1 | M | Users (and permitted guests) can hold a **conversation** with a character; the character replies in text and synthesized **voice**. |
| FR-RT-2 | M | The platform provides a **real-time streaming interaction mode** over WebSocket: streamed LLM tokens and streamed/low-latency audio for live use. |
| FR-RT-3 | S | The streaming pipeline emits **avatar-driving events** (visemes/timing/expression) consumed by a renderer. |
| FR-RT-4 | S | Live **chat ingestion via Connectors** (e.g. Twitch/YouTube/Discord) can route incoming messages as inputs to a character during a stream. |
| FR-RT-5 | M | The platform supports **offline/batch media generation** from scripts (audio; optional **video** via the avatar renderer — see FR-RT-9). |
| FR-RT-6 | S | Generated media is stored as **media assets** with metadata and is downloadable; render runs as a tracked job. |
| FR-RT-7 | S | Voice input (speech-to-text) can be used as a conversation input where ASR is available. |
| FR-RT-8 | S | The system handles **interruption/barge-in** and reconnection in live sessions gracefully (best-effort by provider capability). |
| FR-RT-9 | M | The platform provides a **built-in avatar renderer** behind a pluggable `AvatarRenderProvider` capability. The **default renderer is PNGTuber** (drives a character's layered-PNG sprite set from emitted amplitude/viseme/expression events to produce video and a live avatar); the capability is **extensible to Live2D, 3D-model renderers, and external engines** (OBS, VTube Studio). |
| FR-RT-10 | S | A **live session may include multiple characters** (a *cast*); each character can respond to the user/viewers **and** to other characters' utterances. |
| FR-RT-11 | M | When multiple characters are active, a **turn-arbitration director** serializes turns (one speaker at a time), selects responders, and **bounds character-to-character chains** (max chain depth, no immediate ping-pong, per-input turn budget) to prevent overlapping speech and infinite loops. |

### 3.6 Observability (`OBS`) — see [11](11-feature-observability.md)

| ID | Pri | Requirement |
|---|---|---|
| FR-OBS-1 | M | Users can view **local system resource** usage (CPU, memory, disk/workspace; GPU/VRAM where available). |
| FR-OBS-2 | M | Users can view **external service health/status** (e.g. Ollama, TTS runtime, ASR, storage, active connectors). |
| FR-OBS-3 | M | The system **records token usage** per LLM/embedding call and reports **totals** and breakdowns (per user, per character, over time). |
| FR-OBS-4 | S | The system maintains **structured logs** viewable/tailing from the UI/API, with sensitive-data redaction. |
| FR-OBS-5 | C | Optional **budgets/alerts** on token spend. |
| FR-OBS-6 | M | All observability data stays **local** by default (no external telemetry without explicit opt-in). |

### 3.7 Platform & runtime (`SYS`) — see [13](13-runtime-and-deployment.md)

| ID | Pri | Requirement |
|---|---|---|
| FR-SYS-1 | M | A **one-click local launcher** starts the full stack. |
| FR-SYS-2 | M | The launcher **checks required tools/packages** are installed and reports/guides on anything missing. |
| FR-SYS-3 | M | The launcher ensures the **frontend is built** (or runs the dev server in dev mode) before/while serving. |
| FR-SYS-4 | M | The launcher shows **frontend and backend logs together in a single terminal**. |
| FR-SYS-5 | M | On terminating the terminal/launcher, it **shuts down the frontend and backend** it started — but does **not** stop external services (e.g. Ollama). |
| FR-SYS-6 | M | Data persists in a **local workspace folder** with a **SQLite** database by default. |
| FR-SYS-7 | S | **Storage** and **database** layers are abstracted to allow future cloud storage / external DB modules. |
| FR-SYS-8 | M | **LLM** defaults to local **Ollama**, with seams to integrate other LLM services. |
| FR-SYS-9 | M | **TTS** defaults to **VoxCPM**, with seams to integrate other speech engines/services. |
| FR-SYS-10 | S | Database **migrations** run on startup with a backup safeguard. |
| FR-SYS-11 | S | Configuration is file/env-based with a clear precedence and safe secret handling. |

### 3.8 API & integration (`API`) — see [05](05-api-specification.md)

| ID | Pri | Requirement |
|---|---|---|
| FR-API-1 | M | All functionality is exposed via a **versioned HTTP API** (`/api/v1`) returning JSON, with a real-time **WebSocket** channel for streaming. |
| FR-API-2 | M | The API enforces **authentication/authorization** (guest vs user) server-side. |
| FR-API-3 | M | The API auto-publishes a **machine-readable schema** (OpenAPI) and interactive docs. |
| FR-API-4 | S | Errors use a **consistent envelope** with stable codes; list endpoints support pagination. |

---

## 4. User stories (selected)

**Creator (P1/P2)**
- As a creator, I want to import a past video and get a draft script so that I can reuse my content quickly. *(FR-SM-5/6/7)*
- As a creator, I want a character's personality sliders to actually change how it talks so that the character feels consistent. *(FR-CM-4)*
- As a creator, I want to design a voice from a description and later fine-tune it so that I get a distinctive, improving voice. *(FR-CM-5/6)*
- As a creator, I want to batch-render a dialogue script to audio with per-line pacing so that production is fast. *(FR-SM-8, FR-RT-5)*
- As a creator, I want to go live with my character responding to chat, without leaking one viewer's info to others. *(FR-RT-2/4, FR-MM-7)*
- As a creator, I want to see how many tokens I'm spending per character so that I can manage cost. *(FR-OBS-3)*
- As a creator, I want to export a character and move it to another machine intact. *(FR-CM-10)*

**Developer (P3)**
- As a developer, I want to add a new TTS provider as a module so that I can use my preferred engine. *(FR-MOD-5)*
- As a developer, I want to give a character an Agent Skill (e.g. "look up today's schedule") so that it can take actions. *(FR-MOD-2)*
- As a developer, I want to add a Connector that pipes Discord messages to a character. *(FR-MOD-3, FR-RT-4)*
- As a developer, I want to add a dashboard widget without touching core. *(FR-MOD-4)*

**Guest (P4)**
- As a guest, I want to chat with a character immediately, without an account. *(FR-MM-2)*
- As a guest, when I try an advanced action, I want to be told I need an account. *(FR-MM-11)*

**Operator (any user)**
- As a user, I want to start everything with one command and stop it cleanly. *(FR-SYS-1/4/5)*
- As a user, I want to see if Ollama/TTS are healthy before I rely on them. *(FR-OBS-2)*

## 5. Key use cases (expanded)

### UC-1 · Import audio/video into a script
- **Actor:** User. **Pre:** A media file; ASR provider available.
- **Main flow:** User uploads file → system extracts audio (ffmpeg) → submits ASR import job → (optional) diarization → produces draft lines with timestamps → user reviews/corrects and maps speakers to characters → commits → script persisted.
- **Alt/exceptions:** Unsupported format → clear error; ASR provider down → job fails with actionable message; user cancels → job stops, no commit.
- **Post:** A reviewable/committed script. *(FR-SM-5/6/7)*

### UC-2 · Create & voice a character
- **Actor:** User.
- **Main flow:** Create character → set basic info, persona, Big Five → choose voice approach (voice design via description **or** zero-shot via reference audio) → preview sample → save.
- **Extension:** Start a fine-tune job from a dataset → on completion, select/preview/version the trained voice. *(FR-CM-2/3/4/5/6/7)*

### UC-3 · Guest conversation
- **Actor:** Guest.
- **Main flow:** Open app → guest session auto-created → list guest-visible characters → start conversation → exchange messages with synthesized replies. Attempting an advanced op → prompted to register/login. *(FR-MM-2/11, FR-RT-1)*

### UC-4 · Live streaming session
- **Actor:** User; viewers (anonymous).
- **Main flow:** Start live session for **one or more characters** (a *cast*; sensitive mode default on for public context) → connect a chat Connector → incoming messages routed as inputs → the **turn director** picks a responder; characters stream text+voice responses and may answer one another within bounded chains → viseme events available to avatar engine → session ends, summary persisted. *(FR-RT-2/3/4/10/11, FR-MM-7)*

### UC-5 · Install & configure a module
- **Actor:** User/developer.
- **Main flow:** Place/import module → system reads manifest, validates compatibility, lists contributions/permissions → user enables and configures → contributions register (provider/skill/connector/route/UI) → available for use. *(FR-MOD-1/7/8)*

### UC-6 · Produce media from a script
- **Actor:** User.
- **Main flow:** Open script → select lines → confirm per-line voice/pacing & character voices → submit render job → audio assembled (+ optional subtitles/video) → media asset stored and downloadable. *(FR-SM-8/9, FR-RT-5/6)*

### UC-7 · Export/import a character
- **Actor:** User.
- **Main flow:** Choose character → select what to include (profile/personality always; voice artifacts/memory optional, privacy-filtered by default) → export package → on another install, import → character reconstructed. *(FR-CM-10/11)*

---

## 6. Non-functional requirements

### 6.1 Performance & latency
- **NFR-PERF-1 (M):** Typical interactive API calls (non-generative) respond within a low-hundreds-of-milliseconds budget on a typical dev machine.
- **NFR-PERF-2 (M):** In live mode, **time-to-first-audio** for a turn stays within a low single-digit-second budget on a capable consumer GPU; the system streams rather than waiting for full synthesis.
- **NFR-PERF-3 (S):** Repeated identical synthesis (same text/voice/params) may be cached to reduce latency and cost.
- **NFR-PERF-4 (S):** Long operations (ASR import, batch render, fine-tune) never block the request thread; they run as async jobs.

### 6.2 Scalability
- **NFR-SCALE-1 (M):** Support tens of characters and thousands of script lines per workspace without UI/DB degradation.
- **NFR-SCALE-2 (S):** Support multiple concurrent conversations/live sessions bounded by local hardware. The default runtime is **single-process and stateful** (in-process jobs, SQLite, server-side WebSocket turn state); horizontal scaling is **not a v1 goal** but is kept reachable by the documented extraction path (external job broker, external DB/object store, sticky/stateless gateway — [03 §11](03-system-architecture.md)).
- **NFR-SCALE-3 (S):** Storage and DB seams allow migration to external systems for larger deployments.

### 6.3 Reliability & availability
- **NFR-REL-1 (M):** A crash of an external provider (LLM/TTS) is reported and degrades gracefully (clear error, optional fallback) rather than crashing NagiFlow.
- **NFR-REL-2 (M):** Data writes are transactional; the DB uses WAL for resilience; jobs are restartable or clearly marked failed.
- **NFR-REL-3 (S):** Live sessions attempt reconnection and recover or end cleanly.

### 6.4 Usability
- **NFR-UX-1 (M):** A non-developer can set up and reach a first conversation following the docs/launcher without editing code.
- **NFR-UX-2 (M):** UI uses Vuetify/Material patterns consistently; long jobs show progress; errors are actionable.
- **NFR-UX-3 (S):** UI supports **Traditional Chinese and English** (i18n-ready), reflecting the maintainer's locale and the global audience.

### 6.5 Security
- **NFR-SEC-1 (M):** Authorization is enforced server-side for every protected operation (never trust the client).
- **NFR-SEC-2 (M):** Secrets (API keys for external providers/connectors) are never logged, never embedded in URLs, and stored with appropriate care; the user supplies them.
- **NFR-SEC-3 (M):** Module permissions are declared and gated; untrusted module code is treated with caution ([06 §11](06-module-and-extension-system.md), [15 Security](15-security-and-threat-model.md)).
- **NFR-SEC-4 (S):** Sensitive data is redacted from logs.

### 6.6 Privacy
- **NFR-PRIV-1 (M):** Local-first: no user content leaves the machine unless a user-configured external provider/connector requires it.
- **NFR-PRIV-2 (M):** Cross-user memory leakage is prevented by scoping + sensitive mode ([09](09-feature-multiuser-memory-and-privacy.md)).
- **NFR-PRIV-3 (M):** Character export strips user-linked memory by default.
- **NFR-PRIV-4 (M):** No external telemetry by default.

### 6.7 Portability & footprint
- **NFR-PORT-1 (M):** Runs on Windows, macOS, and Linux.
- **NFR-PORT-2 (M):** Defaults are lightweight; the base install runs on a typical creator machine.
- **NFR-PORT-3 (S):** The launcher behaves consistently across OSes (a cross-platform launcher approach is recommended in [13](13-runtime-and-deployment.md)).

### 6.8 Maintainability & extensibility
- **NFR-MAINT-1 (M):** Clear separation between API, services, providers, and persistence; new providers/modules slot into defined interfaces.
- **NFR-MAINT-2 (S):** Provider **contract tests** verify any LLM/TTS/ASR/storage implementation against expected behavior.
- **NFR-MAINT-3 (S):** Code and APIs are documented; the SDK has examples.

### 6.9 Observability (quality)
- **NFR-OBS-1 (M):** Requests/jobs are traceable via correlation IDs; key counters (requests, errors, latencies, tokens) are collected locally.

### 6.10 Compliance & licensing
- **NFR-COMP-1 (M):** Integrated OSS licenses are honored and surfaced; voice-cloning misuse warnings from upstream (e.g. VoxCPM) are preserved in product guidance.
- **NFR-COMP-2 (S):** The product provides guidance discouraging impersonation/deepfake misuse of voice features.

## 7. External interface requirements

| Interface | Default | Requirement |
|---|---|---|
| **LLM** | Ollama (local) | Text generation with streaming; model listing; pluggable to other providers via a provider interface. *(FR-SYS-8, FR-MOD-5)* |
| **TTS** | VoxCPM | Speech synthesis supporting voice design (text description) and controllable cloning (reference audio + style); streaming where available; pluggable. *(FR-SYS-9, FR-MOD-5)* |
| **ASR** | Local model (e.g. SenseVoice-class) | Transcription with timestamps; optional diarization; pluggable. *(FR-SM-5/6, FR-MOD-5)* |
| **Embeddings / Vector store** | Local default | Embedding generation + similarity search for memory; pluggable. *(FR-CM-8, FR-MM-6)* |
| **Storage** | Local workspace FS | Read/write of assets/media/models; pluggable to cloud. *(FR-SYS-6/7, FR-MOD-5)* |
| **Database** | SQLite | Relational persistence; seam for external DB. *(FR-SYS-6/7)* |
| **Media tooling** | ffmpeg | Audio extraction from video, audio assembly. *(FR-SM-5/8)* |
| **Streaming platforms** | via Connectors | Optional live-chat ingestion/output. *(FR-RT-4, FR-MOD-3)* |
| **Avatar renderer** | Built-in **PNGTuber** (default); pluggable | Drives a character's avatar (layered-PNG sprite set by default) from emitted amplitude/viseme/timing/expression events to render video/live avatar. Extensible to **Live2D**, **3D** renderers, and **external engines** (OBS, VTube Studio) via the capability / Connectors. *(FR-RT-3/9, FR-MOD-5)* |

## 8. Verification approach

- **Functional:** automated API/integration tests per area; manual checks for media quality and live latency.
- **Provider behavior:** contract tests run against each provider implementation.
- **Privacy:** targeted tests for memory scoping and sensitive-mode filtering (no cross-user leakage).
- **NFRs:** performance probes (latency budgets), portability smoke tests per OS, security review of permission enforcement and secret handling.
- **Traceability:** every feature doc references the `FR-*`/`NFR-*` IDs it satisfies.
