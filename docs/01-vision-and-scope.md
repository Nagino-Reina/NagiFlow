# 01 · Vision & Scope

| | |
|---|---|
| **Document** | Vision & Scope |
| **Doc ID** | NF-01 |
| **Version** | 0.1 (Draft) |
| **Last updated** | 2026-05-30 |
| **Related** | [02 Requirements](02-requirements-specification.md), [13 Roadmap](13-roadmap-and-milestones.md) |

---

## 1. Problem statement

Creating an AI VTuber today means stitching together a fragmented toolchain. A creator typically juggles:

- a writing tool for scripts,
- a separate TTS tool (and yet another for voice cloning/fine-tuning),
- ad-hoc files for character "personality" prompts,
- a vector database or notes for "memory,"
- an LLM runtime,
- and OBS / avatar software for streaming.

Nothing connects these. Memory is not tied to a character or to the specific viewer being addressed. Voice direction in a script does not flow into synthesis. Importing an existing video to bootstrap a script is manual. There is no single, **local-first** place where a character's identity, voice, memory, scripts, and live presence live together — and there is no clean way to extend such a tool toward new models or services without forking it.

For privacy-conscious creators and small studios, sending scripts, voices, and viewer conversations to opaque cloud services is also undesirable.

## 2. Product vision

> **NagiFlow is the home for an AI VTuber's whole life — script, voice, personality, memory, and live presence — running on your own machine, open to extension, and respectful of privacy.**

NagiFlow treats a **character** as a first-class, portable asset and gives creators an integrated workflow from *idea → script → voice → produced media → live interaction*, defaulting to lightweight local services and exposing every external integration point as a replaceable module.

## 3. Goals & objectives

| ID | Goal | Objective (measurable intent) |
|---|---|---|
| G1 | **Unify the VTuber workflow** | A creator can author a script, attach it to a character, and produce voiced media without leaving NagiFlow. |
| G2 | **Make characters portable & coherent** | A character (profile, Big Five, voice, optional memory) can be exported and re-imported on another install as a single package. |
| G3 | **Local-first & lightweight by default** | A first-time user can run the whole stack on a single consumer machine via one command, with no mandatory cloud account. |
| G4 | **Extensible without forking** | A third-party developer can add a new LLM/TTS provider, an Agent Skill, a Connector, or a UI panel as a module — and the bundled defaults are themselves modules. |
| G5 | **Memory that respects people** | Memory is scoped per user and per character; a sensitive mode guarantees a character never leaks one user's information to another. |
| G6 | **Low barrier to try** | Anyone can converse with an available character as a guest, with advanced operations gated behind a local account. |
| G7 | **Operational transparency** | A user can see resource usage, service health, and total token spend at any time. |

## 4. Non-goals (out of scope for the foreseeable future)

- NagiFlow is **not** a general-purpose video editor or DAW; it orchestrates generation and integrates with specialist tools rather than replacing them.
- NagiFlow does **not** ship its own foundation LLM or train one; it integrates existing LLM runtimes.
- NagiFlow is **not** a hosted SaaS in its initial form; it is a locally-run application (cloud deployment is a later, optional path).
- NagiFlow does **not** provide a real-money marketplace, billing, or content-distribution network.
- NagiFlow does **not** attempt full 3D avatar rendering in core; avatar rendering is delegated to external engines via Connectors, with only lightweight viseme/timing output produced by core.

## 5. Target users & personas

### P1 — Indie VTuber creator ("Mei")
Runs a one-person channel. Comfortable installing software, not necessarily a programmer. Wants a consistent character voice and personality, wants to turn old streams/clips into scripts, and wants to go live with an AI co-host. **Cares about:** ease of setup, voice quality, character consistency, privacy.

### P2 — Small content studio ("Studio Koi")
2–5 people producing scripted shorts with several recurring characters. Wants script collaboration-adjacent workflows, batch media rendering, reusable characters, and clear cost visibility. **Cares about:** multi-character management, batch production, exports/handoff, token spend.

### P3 — Developer / integrator ("Ren")
Builds on top of NagiFlow — adds a custom LLM endpoint, a Twitch chat Connector, a custom dashboard widget, or a specialized Agent Skill. **Cares about:** a clean SDK, stable extension points, documentation, the ability to ship modules independently.

### P4 — Casual visitor / fan ("Guest")
Lands on a running instance (e.g. a creator's local or shared instance) and just wants to chat with a character. No account. **Cares about:** zero-friction access to basic conversation.

## 6. Value proposition & differentiators

| Differentiator | Why it matters |
|---|---|
| **Integrated character lifecycle** | Script, voice, personality, and memory are connected — voice direction and persona actually influence synthesis and dialogue. |
| **Local-first, one-command start** | No cloud dependency; a single launcher checks the environment, builds if needed, runs everything, and cleans up on exit. |
| **Modular by construction** | Even the defaults (Ollama, VoxCPM2) are modules — proving the extension model and letting users swap any layer. |
| **Privacy-aware memory** | Per-user/per-character scoping + sensitive mode prevents cross-user leakage, which matters acutely in public streaming. |
| **Portable characters** | A character is a single exportable asset, enabling sharing, backup, and migration. |
| **Built for real-time** | A streaming pipeline (token-streaming LLM + low-RTF streaming TTS + viseme events) targets live VTubing, not just offline rendering. |

## 7. Key usage scenarios (narrative)

1. **Bootstrap from an old stream.** Mei drops a 30-minute VOD into NagiFlow. ASR transcribes it into a script with timestamps and per-line speakers; she cleans it up and reuses lines as reference material and training data for her character's voice.
2. **Build a character.** Mei creates "Nagi," sets a warm/curious Big Five profile, designs a voice from a text description (and later refines it with a fine-tune), and writes a short persona. She previews a synthesized line.
3. **Produce a short.** Studio Koi writes a two-character dialogue script, assigns voices and per-line pacing/style, and batch-renders the audio plus subtitles, ready for editing.
4. **Go live.** Mei starts a live session; her character streams spoken responses to viewer chat (via a Twitch Connector), with sensitive mode on so no viewer's earlier private remarks leak to the audience.
5. **Extend.** Ren writes a Connector that pipes a Discord channel into a character, and a dashboard widget that charts daily token spend — distributed as a module, installed without touching NagiFlow's core.
6. **Drop-in chat.** A Guest opens the instance and chats with a public character; when they try to edit the character, they're invited to create a local account.

## 8. Success metrics (indicative)

| Dimension | Indicative target |
|---|---|
| Time-to-first-conversation | A new user reaches a working character chat in **< 30 minutes** from a clean machine. |
| Setup friction | The launcher detects and clearly reports **100%** of missing prerequisites. |
| Character portability | Export → import on a second machine reproduces profile, personality, and voice config with **no manual fix-up** (memory inclusion optional). |
| Live latency | First audible response in a live turn within a **low single-digit-second** budget on a capable consumer GPU (see [10](10-feature-realtime-and-media-generation.md)). |
| Extensibility | A reference provider/skill/connector/UI module can each be added **without modifying core source**. |
| Cost transparency | Token spend is attributable **per user and per character**, and a running total is always visible. |

## 9. Assumptions & constraints

- **A1** Primary deployment is a single consumer machine (Windows, macOS, or Linux); a discrete GPU is recommended for fast local TTS/LLM but not assumed mandatory (fallbacks exist).
- **A2** Users may not be developers; setup must be guided and forgiving.
- **A3** External services (Ollama, VoxCPM2 runtime) are installed/managed by the user or by official modules; NagiFlow controls its own processes but does not forcibly manage external ones.
- **A4** Network access is optional; the default path works offline once models are present.
- **C1** Core is constrained to **FastAPI** (backend) and **Vuetify** (frontend) per project direction.
- **C2** Defaults must remain lightweight and locally runnable; heavy/cloud options are opt-in via modules.
- **C3** The project is delivered by a small team / single maintainer; scope and sequencing in [13](13-roadmap-and-milestones.md) reflect this.

## 10. Stakeholders

| Stakeholder | Interest |
|---|---|
| Maintainer (Alyssum Information Ltd.) | Product direction, architecture, official modules, releases. |
| Creators / studios (P1, P2) | Reliable, private, integrated VTuber production & live tooling. |
| Module developers (P3) | Stable, documented extension surface. |
| Guests / viewers (P4) | Low-friction interaction. |
| Upstream OSS projects | NagiFlow integrates and credits them; compatibility expectations. |

## 11. Scope summary

**In scope (v0.x → v1.0):** script management with ASR import; character management with Big Five, voice (zero-shot + fine-tune) and memory; multi-user/multi-character with scoped memory, sensitive mode, and guest access; module system (providers, Agent Skills, Connectors, UI extensions); offline media generation and a real-time streaming interaction pipeline; observability; local-first runtime with a one-click launcher.

**Deferred / optional (post-1.0 or module-only):** managed cloud hosting; built-in advanced 3D avatar rendering; team/RBAC beyond guest+user; marketplace/registry; non-VTuber general use.
