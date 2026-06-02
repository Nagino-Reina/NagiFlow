# 15 · Roadmap & Milestones

| | |
|---|---|
| **Document** | Roadmap & Milestones |
| **Doc ID** | NF-15 |
| **Version** | 0.1 (Draft) |
| **Last updated** | 2026-05-30 |
| **Related** | [01 Vision](01-vision-and-scope.md), [02 SRS](02-requirements-specification.md), and all feature docs (07–12) |
| **Traces** | Sequences delivery of FR-* / NFR-* across phases |

---

## 1. Approach

The plan is **iterative and milestone-driven**: ship a thin vertical slice early, then widen. Each phase ends with concrete **exit criteria** and a runnable build. Scope is deliberately ordered so the **local-first core** and the **provider/module seams** exist before breadth is added — this avoids rework when external services are swapped in later.

Pre-1.0 the project uses **SemVer 0.x**: minor bumps may carry breaking changes, documented in a changelog; the **module API** is versioned separately so extension authors get stability signals ([06 §10](06-module-and-extension-system.md)).

```mermaid
flowchart LR
    P0[P0 Foundations] --> P1[P1 MVP - voice a character, chat]
    P1 --> P2[P2 Scripts + ASR + batch media]
    P2 --> P3[P3 Multi-user + memory scoping + sensitive mode]
    P3 --> P4[P4 Module system maturity]
    P4 --> P5[P5 Realtime streaming + avatar + live chat]
    P5 --> P6[P6 Fine-tune + advanced obs + cloud seams + polish]
```

---

## 2. Phases

### P0 — Foundations · ✅ Complete
**Goal:** the skeleton everything else hangs on.
- Repo scaffold; FastAPI backend + Vuetify SPA shell; brand theme.
- Config layering, **workspace** layout, **SQLite + ORM + Alembic** ([04](04-data-model-and-storage.md)).
- **Launcher MVP** (prereq checks, start both, single-terminal logs, clean shutdown — [14 §3](14-runtime-and-deployment.md)).
- **Provider/adapter interfaces** defined ([03 §6](03-system-architecture.md), [06 §5](06-module-and-extension-system.md)).

**Exit:** `nagiflow up` starts an empty-but-running app; migrations apply; provider interfaces compile with a stub provider.

### P1 — MVP (give a character a voice, and talk to it) · ✅ Complete
**Goal:** the smallest end-to-end that demonstrates the product.
- **Character management**: profile, **Big Five** + behavior mapping, **zero-shot voice** via **VoxCPM** ([08 §3–4](08-feature-character-management.md)).
- **Single-user** local auth + **guest** session; basic chat via **Ollama** using the **recent-conversation window** as context. (Persistent, scope-aware per-character **memory** — FR-MM-6 — moves to **P3** with the rest of the memory/privacy subsystem.)
- TTS playback of replies; **basic observability** (system + token totals) ([12](12-feature-observability.md) subset).
- Official **Ollama** and **VoxCPM** provider modules ([06 §12](06-module-and-extension-system.md)).

**Exit:** create a character, set personality, give it a voice from a reference clip, hold a spoken text-chat; tokens are counted; runs on a typical dev machine.

### P2 — Scripts, ASR import & batch media
**Goal:** authoring and production.
- **Script management**: manual authoring, multi-speaker, per-line direction ([07 §3](07-feature-script-management.md)).
- **ASR import** (default **SenseVoice**): audio/video → timed draft → review → commit ([07 §4](07-feature-script-management.md)).
- **Batch media render**: script → assembled audio + **subtitles (SRT/VTT)** ([11 §3](11-feature-realtime-and-media-generation.md)).
- **Token/cost accounting** broadened (per character/conversation) ([12 §3](12-feature-observability.md)).
- **Default PNGTuber avatar renderer** for **batch video**: render a script to video by animating the character's layered-PNG sprite set from emitted amplitude/viseme/expression events ([11 §3/§5](11-feature-realtime-and-media-generation.md)).

**Exit:** import a recording into a script, correct it, render narrated audio with subtitles **and a PNGTuber video**; export script as JSON/SRT.

### P3 — Multi-user, memory scoping & privacy
**Goal:** safe many-user operation.
- **Multi-user / multi-character**; full **permission matrix** ([09 §3](09-feature-multiuser-memory-and-privacy.md)).
- **Memory scoping** (user_scoped / character_general / character_interaction) with namespace isolation ([09 §4](09-feature-multiuser-memory-and-privacy.md)).
- **Sensitive mode** (retrieval filter + prompt; optional output guard) ([09 §5](09-feature-multiuser-memory-and-privacy.md)).
- **Character export/import** (`.nagichar`) with privacy-safe defaults ([08 §6](08-feature-character-management.md)).
- User **data deletion** ([09 §6](09-feature-multiuser-memory-and-privacy.md)).

**Exit:** two users converse with the same character without cross-leak; sensitive mode verified to exclude other-user data at retrieval; export a character without shipping user memories.

### P4 — Module system maturity
**Goal:** real extensibility.
- **Agent Skills** (code + declarative Markdown), **Connectors**, **UI extensions**, **framework hooks** ([06 §6–9](06-module-and-extension-system.md)).
- Public **SDK** + sample modules; **permission model** enforced ([06 §11](06-module-and-extension-system.md)).
- Provider **capability flags** + graceful fallback across the app.

**Exit:** a third party builds and installs a skill + a connector from docs/SDK alone; permissions are honored; defaults still pass as ordinary modules.

### P5 — Realtime streaming, avatar & live chat
**Goal:** live VTubing.
- **WebSocket turn pipeline**: streaming LLM + **streaming TTS** + **amplitude/viseme/timing** ([11 §4–5](11-feature-realtime-and-media-generation.md)).
- **Barge-in**, reconnection ([11 §4.2/4.4](11-feature-realtime-and-media-generation.md)).
- **Multi-character live sessions** (a *cast*) with the **turn director** (serialized turns, bounded character↔character chains) ([11 §4.5](11-feature-realtime-and-media-generation.md)).
- **Live-chat connectors** (Twitch/YouTube/Discord) routed as inputs with **sensitive mode default-on** ([11 §6](11-feature-realtime-and-media-generation.md)).
- **Live avatar via default PNGTuber renderer**: real-time sprite animation driven by the streaming amplitude/viseme/expression events ([11 §5](11-feature-realtime-and-media-generation.md)).
- **Pluggable renderers**: **Live2D**, **3D-model renderer**, and **external-engine** adapters (OBS/VTube Studio) via the `AvatarRenderProvider` capability + connectors.

**Exit:** a live session where viewer chat drives a **cast** of characters that answer the user and one another in coherent order, audio streams in near-real-time, the **default PNGTuber avatar** lip-syncs (with Live2D/3D/external selectable), and no viewer's info leaks to another.

### P6 — Fine-tune, advanced observability, cloud seams & polish
**Goal:** depth, scale-out seams, and release quality.
- **Voice fine-tune training** pipeline with versioning/rollback ([08 §4.1](08-feature-character-management.md)).
- **Advanced observability**: budgets/alerts, richer health/latency ([12 §3.2](12-feature-observability.md)).
- **Cloud/external seams**: storage and external DB adapters; optional vector backends ([03 §6](03-system-architecture.md), [04 §7](04-data-model-and-storage.md)).
- Packaging (pipx/Docker), docs, accessibility/i18n polish ([14 §7](14-runtime-and-deployment.md)).

**Exit:** train and activate a custom voice; set a token budget with alerts; point storage at an external backend via config; ship a packaged build.

---

## 3. Milestone summary

| Phase | Theme | Headline FR families | Exit criterion (short) | Status |
|---|---|---|---|---|
| P0 | Foundations | FR-SYS-1/8/9 | `nagiflow up` runs an empty app | ✅ Complete |
| P1 | MVP | FR-CM-1/2/3/4, FR-OBS-1/3 | Voiced character you can chat with | ✅ Complete |
| P2 | Scripts/Media | FR-SM-1…9, FR-RT-5 | Import→correct→render with subtitles | Next |
| P3 | Multi-user/Privacy | FR-MM-1…11, FR-CM-11/12 | Two users, no cross-leak; safe export | Planned |
| P4 | Modules | FR-MOD-1…11 | 3rd-party skill+connector from SDK | Planned |
| P5 | Realtime | FR-RT-1…11 | Live chat-driven, multi-character, lip-synced session | Planned |
| P6 | Depth/Scale/Polish | FR-CM-5/6, FR-OBS-4/5, NFR-SCALE-* | Fine-tuned voice; budgets; external storage | Planned |

---

## 4. MVP scope cut-lines

To keep P1 small, these are explicitly **deferred** past MVP:
- Realtime streaming & barge-in (P5) — MVP chat may be request/response, not low-latency streaming.
- Multi-user isolation & sensitive mode (P3) — MVP is effectively single-user.
- Voice **fine-tuning** (P6) — MVP uses **zero-shot** cloning only.
- Connectors / live-chat / avatars (P4–P5).
- ASR import & batch media (P2).
- Budgets/alerts, cloud/external storage & DB (P6).

This sequencing front-loads the riskiest *integration* (Ollama + VoxCPM + memory) while leaving breadth for later.

---

## 5. Risks & mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| **GPU availability** varies wildly | TTS/LLM speed; fine-tune feasibility | CPU fallbacks, smaller models, non-streaming path; detect & adapt ([11 §7](11-feature-realtime-and-media-generation.md)); fine-tune is P6/optional |
| **VoxCPM integration/training complexity** | Voice features slip | Wrap behind the TTS provider contract; ship zero-shot first, fine-tune later; pin versions; isolate in a module |
| **ASR diarization accuracy** | Messy script imports | Treat diarization as optional; always allow manual speaker mapping ([07 §4.1](07-feature-script-management.md)) |
| **Frontend module-federation / UI-extension complexity** | P4 slip | Start with backend skills/connectors; UI extensions can land incrementally |
| **Avatar rendering integration** (formats, lip-sync mapping) + **Live2D licensing** | Avatar video/live slips; license friction | Default to **PNGTuber** (layered PNG, amplitude-driven lip-flap, MIT, no proprietary SDK/GPU) so the core ships clean; wrap everything behind `AvatarRenderProvider`. **Live2D's Cubism SDK is non-MIT** with redistribution/revenue terms, so Live2D ships as a **separate optional module** (the operator accepts its license), as do 3D/external; portrait/audio-only fallback always available ([11 §5/§7](11-feature-realtime-and-media-generation.md)) |
| **Cross-user privacy bugs** | Serious trust failure | Enforce at **data layer** (namespaces + retrieval filter), test explicitly in P3 ([09](09-feature-multiuser-memory-and-privacy.md)) |
| **Scope creep** | Never-ship | This roadmap + cut-lines (§4) as the contract; defer to later phases by default |
| **Provider/API churn** (Ollama/VoxCPM changes) | Breakage | Adapter layer + capability flags + pinned versions ([06 §5](06-module-and-extension-system.md)) |

---

## 6. Testing strategy

A pragmatic test pyramid:

| Layer | What | When |
|---|---|---|
| **Unit** | Pure logic: Big Five mapping, memory scoping/retrieval filters, config layering, validation rules | Every phase |
| **Integration** | API + DB + repositories; job lifecycle; migrations | Every phase |
| **Provider-contract** | A shared test suite each provider module must pass (LLM/TTS/ASR/etc.), incl. capability-flag honesty | P0 onward; gate official + 3rd-party modules ([06 §5.1](06-module-and-extension-system.md)) |
| **Privacy tests** | Explicit cross-user no-leak + sensitive-mode retrieval-exclusion cases | P3 (and regression thereafter) ([09](09-feature-multiuser-memory-and-privacy.md)) |
| **E2E smoke** | "Create character → chat", "import → render", "live turn" happy paths | Per phase milestone |
| **Manual media QA** | Subjective audio/voice/lip-sync quality | P1/P2/P5 |

CI runs unit+integration+contract on each change; privacy tests are mandatory gates once P3 lands.

---

## 7. Versioning & change management

- **License:** NagiFlow is released under the **MIT License**. Integrated third-party components keep their own licenses (e.g. VoxCPM under Apache-2.0); optional renderer modules with non-MIT terms (e.g. **Live2D** Cubism SDK) ship **separately** so the MIT core stays unencumbered.
- **0.x SemVer**; changelog records breaking changes (config, schema, module API).
- **Schema** changes ship with Alembic migrations + startup backup ([14 §6](14-runtime-and-deployment.md)).
- **Module API** versioned separately with a deprecation window ([06 §10](06-module-and-extension-system.md)).
- A **1.0** target is reached when P1–P5 are stable, the module API is frozen for a cycle, and privacy tests are comprehensive.

---

## 8. Notes

Timeframes are intentionally omitted — phases are sequenced by dependency and risk, not dates, which lets the plan flex without churning the document. The ordering itself is the commitment.
