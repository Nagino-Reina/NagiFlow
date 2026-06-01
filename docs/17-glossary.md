# 17 · Glossary & References

| | |
|---|---|
| **Document** | Glossary & References |
| **Doc ID** | NF-17 |
| **Version** | 0.1 (Draft) |
| **Last updated** | 2026-05-30 |
| **Related** | All NagiFlow documents |

---

## 1. Core NagiFlow concepts

| Term | Definition |
|---|---|
| **NagiFlow** | A local-first, modular platform for building, voicing, and live-streaming AI VTubers; covers authoring, embodiment, production, and live interaction. |
| **AI VTuber** | A virtual streamer/character driven by AI — generated voice (and optionally avatar/video) plus conversational behavior. |
| **Character** | The central entity: a configured AI VTuber with a profile, Big Five personality, voice model(s), and a memory bank ([08](08-feature-character-management.md)). |
| **Persona prompt** | The authored system text defining a character's tone, quirks, and rules; combined at runtime with personality and memory. |
| **Script** | An ordered set of dialogue **lines** with speakers, optional timestamps, and voice direction; used to render media or as training data ([07](07-feature-script-management.md)). |
| **ScriptLine** | One spoken unit: text + speaker + optional timing + style/speech-rate/reference-audio direction. |
| **Big Five / OCEAN** | Five personality traits — **O**penness, **C**onscientiousness, **E**xtraversion, **A**greeableness, **N**euroticism — scored 0–100 and mapped to generation behavior ([08 §3](08-feature-character-management.md)). |
| **Memory bank** | A character's durable, **scoped** memories, retrieved at conversation time ([09 §4](09-feature-multiuser-memory-and-privacy.md)). |
| **Memory entry** | A single stored memory with a scope, importance, and embedding. |
| **Memory scope** | One of `user_scoped` (character+user), `character_general` (character only), or `character_interaction` (character+counterpart character). |
| **Sensitive mode** | A setting that prevents a character from revealing/referencing **other users**, enforced primarily at memory retrieval ([09 §5](09-feature-multiuser-memory-and-privacy.md)). |
| **Guest** | An anonymous, no-login session limited to basic conversation with guest-visible characters ([09 §2](09-feature-multiuser-memory-and-privacy.md)). |
| **Workspace** | The local folder holding NagiFlow's data: SQLite DB, config, characters, scripts, media, memory index, modules, jobs, backups, logs ([04 §2](04-data-model-and-storage.md)). |
| **MediaAsset** | A rendered output (audio and/or video, with subtitles) linked to a script ([11 §3](11-feature-realtime-and-media-generation.md)). |
| **Dialogue Orchestrator** | The runtime component that assembles context, retrieves memory, calls the LLM (with skills), streams TTS, and writes memory/usage ([03 §5](03-system-architecture.md), [11 §4](11-feature-realtime-and-media-generation.md)). |
| **Cast** | The set of characters active in a single (multi-character) live session; for ordinary chat the cast is one character ([11 §4.5](11-feature-realtime-and-media-generation.md)). |
| **Turn director / Conversation director** | The scheduler that, in a multi-character session, serializes turns (one speaker at a time), selects the next responder, and bounds character-to-character chains to prevent overlap and infinite loops ([11 §4.5](11-feature-realtime-and-media-generation.md)). |
| **Avatar bundle** | The directory (descriptor + assets) holding a character's avatar — a PNGTuber sprite set by default, or a Live2D / 3D model — referenced by a single storage key ([04 §5.2](04-data-model-and-storage.md)). |

---

## 2. Extensibility terms

| Term | Definition |
|---|---|
| **Module** | A packaged extension contributing one or more of: provider, agent skill, connector, UI extension, framework hook ([06](06-module-and-extension-system.md)). |
| **Provider / Adapter** | An implementation of a capability interface (LLM, TTS, ASR, Embedding, VectorStore, Storage) behind which a concrete service sits. |
| **Capability flag** | A declared feature a provider supports (e.g. TTS `streaming`, `voice_clone`); the orchestrator adapts to what's advertised. |
| **Agent Skill** | A tool the character can invoke during conversation (LLM function/tool calling), defined in code or as a declarative Markdown "SKILL" doc ([06 §6](06-module-and-extension-system.md)). |
| **Connector** | A module bridging NagiFlow to an external system as an event **source** and/or **sink** (e.g. Twitch chat, OBS) ([06 §7](06-module-and-extension-system.md)). |
| **UI extension** | A frontend contribution mounted into a defined extension point in the Vuetify app ([06 §8](06-module-and-extension-system.md)). |
| **Framework hook** | A subscriber to lifecycle/domain events on the event bus ([06 §9](06-module-and-extension-system.md)). |
| **Manifest** | `nagiflow.module.json` — a module's declarative metadata, contributions, permissions, and host-compatibility range ([06 §3.1](06-module-and-extension-system.md)). |
| **Host SDK** | The `host` object/API a module uses for registration and guarded resource access ([06 §5](06-module-and-extension-system.md)). |
| **`.nagichar`** | The portable character package format (zip) for export/import ([08 §6](08-feature-character-management.md)). |
| **Job** | A tracked long-running operation (ASR import, media render, voice fine-tune) with progress, events, and cancellation ([04 §6](04-data-model-and-storage.md)). |

---

## 3. Technologies & external components

| Term | Definition |
|---|---|
| **FastAPI** | The Python async web framework used for NagiFlow's backend core (serves the API and, in prod, the built SPA). |
| **Vuetify** | The Vue 3 Material component framework used for NagiFlow's frontend core. |
| **Vue / Pinia / Vite** | Frontend framework / state store / build tool underpinning the SPA. |
| **SQLite** | The default embedded relational database (file in the workspace). |
| **WAL** | Write-Ahead Logging — a SQLite journaling mode improving concurrency/resilience. |
| **ORM** | Object-Relational Mapper (SQLAlchemy) translating between Python objects and DB rows. |
| **Alembic** | Schema migration tool for the ORM; migrations run on startup after backup. |
| **Ollama** | The default **local LLM** runtime; an **external service** NagiFlow connects to but does not manage. |
| **LLM** | Large Language Model — produces the character's conversational text. |
| **TTS** | Text-to-Speech — synthesizes the character's voice. |
| **VoxCPM** | OpenBMB's text-to-speech model used as NagiFlow's **default TTS**: multilingual, high-sample-rate studio-quality output, with voice cloning and natural-language **voice design**, and fine-tuning support. Used via its Python API or an OpenAI-compatible server. |
| **ASR** | Automatic Speech Recognition — transcribes audio to text (for script import and voice input). |
| **SenseVoice** | The speech-recognition model used by the VoxCPM stack; NagiFlow's **default ASR**. |
| **Voice cloning** | Creating a voice from a short **reference** audio clip (zero-shot). |
| **Voice design** | Creating a voice from a **natural-language description** of how it should sound. |
| **Fine-tune** | Training a durable custom voice model from a dataset of text+audio pairs ([08 §4.1](08-feature-character-management.md)). |
| **Embedding** | A vector representation of text used for similarity search in memory retrieval. |
| **Vector store** | An index of embeddings enabling nearest-neighbor retrieval; partitioned by memory namespace. |
| **RAG** | Retrieval-Augmented Generation — injecting retrieved context (here, memories) into the prompt. |
| **WebSocket** | The bidirectional protocol carrying live conversation turns (streaming text/audio/visemes) ([05 §8](05-api-specification.md)). |
| **SSE** | Server-Sent Events — an optional one-way streaming transport alternative. |
| **Token** | The unit LLMs process text in; counted for usage/cost accounting ([12 §3](12-feature-observability.md)). |
| **RTF** | Real-Time Factor — synthesis time ÷ audio duration; < 1 means faster-than-real-time (needed for smooth live TTS). |
| **Viseme** | A visual mouth-shape unit; NagiFlow emits visemes/timing for avatar lip-sync ([11 §5](11-feature-realtime-and-media-generation.md)). |
| **Avatar renderer** | A provider (`AvatarRenderProvider`) that animates a character's avatar bundle from emitted amplitude/viseme/timing/expression events to produce video and live avatars. **Default: PNGTuber**; pluggable to Live2D, 3D, and external engines ([11 §5](11-feature-realtime-and-media-generation.md)). |
| **PNGTuber** | NagiFlow's **default** avatar renderer: a **layered-PNG sprite set** (mouth states + expression layers + optional blink/sway) driven by audio amplitude / visemes / expression events. Fully MIT, no proprietary runtime, no GPU required. |
| **Live2D** | A 2D model/animation technology for expressive avatars; available in NagiFlow as an **optional** `AvatarRenderProvider` module (`kind="live2d"`). Ships separately because its Cubism SDK carries non-MIT licensing terms. |
| **3D model (avatar)** | A spatial avatar model (e.g. glTF/VRM-class) rendered by an optional 3D `AvatarRenderProvider` module — an extension path beyond the default PNGTuber renderer. |
| **OBS / VTube Studio** | External streaming/avatar tools that can act as alternative avatar renderers via adapter modules/connectors. |
| **ffmpeg** | The media toolkit used for audio extraction, assembly, and transcoding. |
| **CLI** | Command-Line Interface — here, the `nagiflow` launcher/commands ([14 §3](14-runtime-and-deployment.md)). |

---

## 4. Document conventions

| Term | Definition |
|---|---|
| **FR-`AREA`-n** | Functional Requirement, grouped by area (SM=Script, CM=Character, MOD=Module, MM=Multi-user/Memory, RT=Realtime, OBS=Observability, SYS=System, API). Defined in [02 SRS](02-requirements-specification.md). |
| **NFR-`AREA`-n** | Non-Functional Requirement (PERF, PRIV, SEC, REL, PORT, COMP, MAINT, OBS, SCALE, UX). |
| **MoSCoW** | Prioritization scheme: **M**ust / **S**hould / **C**ould / **W**on't (this release). |
| **ADR** | Architecture Decision Record — a logged design decision with context and consequences ([03 §10](03-system-architecture.md)). |
| **SemVer** | Semantic Versioning (`MAJOR.MINOR.PATCH`); pre-1.0 the project is in `0.x`. |
| **Storage key** | An abstract, provider-resolved reference to a stored file (the DB stores keys, not absolute paths) ([04 §2](04-data-model-and-storage.md)). |
| **Correlation id** | An identifier threading a request → WS turn → jobs → usage/log records for tracing ([05 §1](05-api-specification.md)). |

---

## 5. References

> Informational pointers to the principal external technologies. Versions/details evolve; consult upstream docs for current specifics. (Verify before implementation; see [15 §5 risks](15-roadmap-and-milestones.md) on provider churn.)

| Component | What to consult | Note |
|---|---|---|
| **VoxCPM** | OpenBMB's VoxCPM model card / repository | Default TTS; multilingual, high-sample-rate, voice clone + voice design + fine-tune; Python API and OpenAI-compatible server; permissively licensed. |
| **SenseVoice** | SenseVoice model docs | Default ASR used with the VoxCPM stack. |
| **Ollama** | Ollama documentation | Default local LLM runtime; model management + local API. |
| **FastAPI** | FastAPI documentation | Backend framework; async, OpenAPI built-in. |
| **Vuetify / Vue / Vite** | Respective official docs | Frontend stack. |
| **SQLAlchemy / Alembic** | Respective official docs | ORM + migrations. |
| **ffmpeg** | ffmpeg documentation | Media processing. |
| **psutil / pynvml** | Respective project docs | System + GPU metrics ([12 §2](12-feature-observability.md)). |

---

*End of the NagiFlow document set. See the [README](../README.md) for the full index.*
