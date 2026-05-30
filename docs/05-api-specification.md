# 05 · API Specification

| | |
|---|---|
| **Document** | API Specification |
| **Doc ID** | NF-05 |
| **Version** | 0.1 (Draft) |
| **Last updated** | 2026-05-30 |
| **Related** | [03 Architecture](03-system-architecture.md), [04 Data](04-data-model-and-storage.md), [06 Modules](06-module-and-extension-system.md), [09 Privacy](09-feature-multiuser-memory-and-privacy.md) |

---

## 1. Conventions

- **Base path:** `/api/v1`. Breaking changes increment the version segment.
- **Format:** JSON request/response (`application/json`); binary uploads via `multipart/form-data`; media downloads stream bytes.
- **Style:** resource-oriented REST; nouns for resources, verbs for actions only where REST is awkward (e.g. `:render`, `:import`).
- **Async:** all handlers are async; long operations return a **job** (`202 Accepted` + job reference) rather than blocking.
- **Schema:** FastAPI auto-publishes **OpenAPI** at `/openapi.json` and interactive docs at `/docs`.
- **Time:** ISO-8601 UTC. **IDs:** opaque strings.
- **Pagination:** **cursor-based** — `?limit=&cursor=`; list responses include `items` + `next_cursor` (`null` when exhausted). Offset/`page` paging is not used, for stable paging over mutating data.
- **Idempotency:** mutating endpoints accept an optional `Idempotency-Key` header where retries are likely (uploads, job creation). The server stores `(key, route, principal) → first response` for a bounded TTL (default 24 h); a replay with the same key returns the stored response instead of re-executing; a different payload under a used key yields `409 idempotency.conflict`.

## 2. Authentication & authorization

NagiFlow uses **session-based** auth with two principal kinds (full model in [09](09-feature-multiuser-memory-and-privacy.md)).

| Principal | How obtained | Capabilities |
|---|---|---|
| **Guest** | Auto-issued on first contact (`POST /auth/guest`) — no credentials | Basic ops only (e.g. converse with guest-visible characters). |
| **User** | `POST /auth/login` with local credentials | Full authoring/config/ops. |

- The session token is returned and sent on subsequent requests (`Authorization: Bearer <token>` or an **HttpOnly, SameSite=Lax/Strict, Secure** cookie for the SPA).
- **Token model:** sessions are **opaque random tokens**; only their hash is stored (`session.token_hash`). Sessions carry an idle/absolute **expiry** and can be revoked (logout / logout-all). No long-lived JWTs by default (keeps revocation simple for a local app).
- **Password storage:** local-account passwords are hashed with **Argon2id** (memory-hard); never stored or logged in plaintext (NFR-SEC-2).
- **Cookie-mode CSRF:** when the cookie transport is used, state-changing requests require a double-submit CSRF token (or `Origin`/`Sec-Fetch-Site` checks); Bearer-token clients are exempt.
- **Authorization is enforced server-side** on every protected route against the permission matrix; the client never decides access.
- Account **creation** is a deliberate, user-driven action (the system never silently creates accounts on a user's behalf).

### Auth endpoints
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/guest` | none | Issue a guest session. |
| POST | `/auth/register` | none | Create a local account (user-initiated). |
| POST | `/auth/login` | none | Log in to a local account. |
| POST | `/auth/logout` | any | Invalidate current session. |
| POST | `/auth/logout-all` | user | Revoke all of the user's sessions. |
| GET | `/auth/me` | any | Current principal, kind, capabilities. |

## 3. Error model

All errors share an envelope with a **stable machine code**:

```json
{
  "error": {
    "code": "character.not_found",
    "message": "No character with id 'c_123'.",
    "details": { "id": "c_123" },
    "correlation_id": "req_01H..."
  }
}
```

| HTTP | Meaning | Example codes |
|---|---|---|
| 400 | Bad request / validation | `validation.failed`, `script.line.invalid` |
| 401 | Unauthenticated | `auth.required` |
| 403 | Forbidden (capability) | `auth.forbidden`, `guest.upgrade_required` |
| 404 | Not found | `character.not_found`, `module.not_found` |
| 409 | Conflict | `character.name_conflict`, `job.already_running` |
| 413 | Payload too large | `upload.too_large` |
| 422 | Semantic validation | `bigfive.out_of_range` |
| 429 | Rate/Resource limited | `rate.limited` |
| 500 | Internal | `internal.error` |
| 502/503 | Provider failure/unavailable | `provider.unavailable`, `provider.error` |

Provider failures are isolated and surfaced (with which provider failed) rather than crashing the request.

## 4. Endpoint catalog

> Representative catalog. Module-contributed routes are namespaced under `/api/v1/modules/{module_id}/...` ([06](06-module-and-extension-system.md)). `G` = guest-allowed, `U` = user-only.

### 4.1 Characters
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/characters` | G* | List characters (guests see only `guest_visible`). |
| POST | `/characters` | U | Create a character. |
| GET | `/characters/{id}` | G* | Get a character (guests: guest-visible only). |
| PATCH | `/characters/{id}` | U | Update profile/persona/Big Five/style/status. |
| DELETE | `/characters/{id}` | U | Soft-delete/archive. |
| POST | `/characters/{id}:duplicate` | U | Duplicate. |
| POST | `/characters/{id}/voice:preview` | U | Synthesize sample text with a voice config. |
| GET/POST | `/characters/{id}/voice-models` | U | List / create voice models (zero-shot, voice design). |
| POST | `/characters/{id}/voice-models:finetune` | U | Start a fine-tune **job**. |
| POST | `/characters/{id}/voice-models/{vid}:setDefault` | U | Set default voice. |
| GET/POST/DELETE | `/characters/{id}/assets` | U | Manage assets (portrait/images/audio). |
| POST | `/characters/{id}:export` | U | Export a character **package** (privacy options). |
| POST | `/characters:import` | U | Import a character package. |

### 4.2 Scripts
| Method | Path | Auth | Description |
|---|---|---|---|
| GET/POST | `/scripts` | U | List / create scripts. |
| GET/PATCH/DELETE | `/scripts/{id}` | U | Read / update / archive. |
| GET/POST | `/scripts/{id}/lines` | U | List / add lines. |
| PATCH/DELETE | `/scripts/{id}/lines/{lid}` | U | Edit / remove a line. |
| POST | `/scripts/{id}/lines:reorder` | U | Reorder lines. |
| POST | `/scripts:import` | U | Start an **ASR import job** from an uploaded media file. |
| GET | `/scripts/{id}/import/{job_id}` | U | Import job status + draft for review. |
| POST | `/scripts/{id}/import/{job_id}:commit` | U | Commit reviewed/corrected draft. |
| POST | `/scripts/{id}:render` | U | Start a **media render job** (line selection, voices). |
| POST | `/scripts/{id}:exportDataset` | U | Export training dataset (text+audio pairs). |
| GET | `/scripts/{id}:exportFile` | U | Export script as JSON / subtitles. |

### 4.3 Conversations & chat
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/conversations` | G* | Start a conversation. Body takes `character_id` (single) or `character_ids[]` + optional `director_config` for a multi-character **live** cast (guests: guest-visible only). |
| GET | `/conversations` | any | List own conversations. |
| GET | `/conversations/{id}` | owner | Get conversation + messages. |
| POST | `/conversations/{id}/messages` | owner | Send a message (synchronous reply: text + audio ref). |
| WS | `/conversations/{id}/stream` | owner | **Streaming turn** (see §5). |
| PATCH | `/conversations/{id}` | owner | Update (e.g. end, toggle sensitive mode if permitted). |
| DELETE | `/conversations/{id}` | owner | Delete conversation. |

### 4.4 Memory
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/characters/{id}/memory` | U | List/search memory entries (scope filters). |
| POST | `/characters/{id}/memory` | U | Add a memory entry (scope-typed). |
| PATCH | `/characters/{id}/memory/{mid}` | U | Edit a memory entry. |
| DELETE | `/characters/{id}/memory/{mid}` | U | Delete a memory entry. |
| GET | `/characters/{id}/memory:scopes` | U | Summarize memory by scope/user. |

### 4.5 Modules & providers
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/modules` | U | List installed modules + status. |
| GET | `/modules/available` | U | List discoverable/installable modules (local sources/registry). |
| POST | `/modules:install` | U | Install from a folder/archive reference. |
| POST | `/modules/{id}:enable` / `:disable` | U | Toggle a module. |
| GET/PUT | `/modules/{id}/config` | U | Get/set module config (validated against its schema). |
| GET | `/modules/{id}/ui` | U | Module UI contribution metadata/bundle reference. |
| GET/POST | `/providers/{capability}` | U | List/configure providers for a capability (`llm`/`tts`/`asr`/`embedding`/`vector`/`storage`). |
| POST | `/providers/{capability}/{cfgId}:test` | U | Health/connectivity test. |
| POST | `/providers/{capability}/{cfgId}:setDefault` | U | Set default + fallback order. |
| GET | `/providers/llm/models` | U | List available LLM models (e.g. Ollama tags). |

### 4.6 Media & jobs
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/media` | U | List media assets (filters). |
| GET | `/media/{id}` | owner | Metadata. |
| GET | `/media/{id}:download` | owner | Stream/download bytes. |
| GET | `/jobs` | U | List jobs (type/status filters). |
| GET | `/jobs/{id}` | owner | Job status + progress + result/error. |
| GET | `/jobs/{id}/events` | owner | Job progress/log stream (SSE) or paged events. |
| POST | `/jobs/{id}:cancel` | owner | Request cancellation. |

### 4.7 Observability & system
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/system/resources` | U | CPU/memory/disk/GPU snapshot. |
| GET | `/system/services` | U | External service health (Ollama, TTS, ASR, storage, connectors). |
| GET | `/usage` | U | Token/cost usage with filters (per user/character/time) + totals. |
| GET | `/usage:summary` | U | Aggregated dashboards data. |
| GET | `/logs:tail` | U | Recent structured logs (redacted), optional follow. |
| GET | `/system/info` | any | App/version/workspace info. |
| GET | `/healthz` / `/readyz` | none | Liveness / readiness. |

\* Guest access is gated to **guest-visible characters** and **basic conversation**; every other listed capability requires a user session and is enforced server-side ([09](09-feature-multiuser-memory-and-privacy.md)).

## 5. WebSocket streaming protocol (live turns)

**Endpoint:** `WS /api/v1/conversations/{id}/stream`. **Auth:** the session is taken from the **HttpOnly cookie** or a `Sec-WebSocket-Protocol` bearer sub-protocol — **never** a query-string token (query strings leak into access logs/history).

The protocol is **event-typed JSON** for control/text plus **binary frames** for audio. A turn is a client message followed by a stream of server events ending in `turn.end`.

### Client → server
```json
{ "type": "user.message", "text": "Hello!", "request_id": "r1" }
{ "type": "user.audio", "format": "wav", "final": true }   // + binary audio frames (voice input)
{ "type": "control.interrupt" }                            // barge-in: stop current turn
{ "type": "control.ping" }
```

### Server → client
```json
{ "type": "turn.assigned", "turn_id": "t1", "character_id": "c_01H...", "reason": "addressed" } // director picked the speaker (multi-character)
{ "type": "turn.start", "turn_id": "t1", "request_id": "r1", "character_id": "c_01H..." }
{ "type": "text.delta", "turn_id": "t1", "text": "Hel" }
{ "type": "skill.call", "turn_id": "t1", "name": "get_schedule", "args": {...} }     // Agent Skill invoked
{ "type": "skill.result", "turn_id": "t1", "name": "get_schedule", "ok": true }
{ "type": "audio.meta", "turn_id": "t1", "sample_rate": 48000, "codec": "pcm_s16le" }
// → followed by BINARY audio frames tagged to turn_id
{ "type": "viseme", "turn_id": "t1", "t_ms": 1200, "shape": "AA" }                    // avatar driving (FR-RT-3)
{ "type": "status", "turn_id": "t1", "phase": "synthesizing" }
{ "type": "error", "turn_id": "t1", "code": "provider.error", "message": "..." }
{ "type": "turn.end", "turn_id": "t1", "tokens": { "prompt": 312, "completion": 88 } }
```

**Semantics**
- Text and audio stream **concurrently**; the client may render captions from `text.delta` while playing audio frames.
- **Multi-character:** in a live session with a *cast*, every server event carries the speaker's `character_id`, and the **director** emits `turn.assigned` before each `turn.start`. Turns are serialized (one speaker at a time); a character may answer another within the director's bounded chain ([10 §4.5](10-feature-realtime-and-media-generation.md)).
- `control.interrupt` cancels in-flight LLM/TTS for the current turn (barge-in) and emits `turn.end` with a `cancelled` status.
- Reconnection: the client may resume the conversation; in-flight turn state is best-effort per provider capability.
- The same orchestration ([03 §4](03-system-architecture.md)) powers both this stream and the synchronous `POST /messages` endpoint.

> An optional **SSE** variant (`GET /conversations/{id}/messages:stream`) provides one-way token streaming for clients that don't need audio upstream.

## 6. Representative request/response examples

**Create character**
```http
POST /api/v1/characters
Authorization: Bearer <token>
Content-Type: application/json

{ "name": "Nagi", "persona": "A warm, curious co-host.",
  "big_five": {"openness":80,"conscientiousness":55,"extraversion":70,"agreeableness":75,"neuroticism":30},
  "default_language": "zh-Hant", "guest_visible": true }
```
```json
201 Created
{ "id": "c_01H...", "name": "Nagi", "status": "draft", "guest_visible": true, "created_at": "2026-05-30T..." }
```

**Start ASR import (returns a job)**
```http
POST /api/v1/scripts:import
Content-Type: multipart/form-data
file=<media.mp4>; diarize=true; language=auto
```
```json
202 Accepted
{ "job_id": "job_01H...", "script_id": "s_01H...", "status": "pending" }
```

**Voice preview**
```http
POST /api/v1/characters/c_01H.../voice:preview
{ "text": "你好，我是 Nagi。", "voice_model_id": "v_01H...", "style": "cheerful", "speech_rate": 1.0 }
```
```json
200 OK
{ "media_asset_id": "m_01H...", "duration_ms": 1850, "sample_rate": 48000 }
```

## 7. Versioning, compatibility & docs

- **API version** in the path (`/api/v1`); additive changes are non-breaking; removals/renames bump the version.
- **OpenAPI** is the source of truth for schemas; clients/SDKs may be generated from it.
- **Module routes** declare their own sub-schemas, merged into the published OpenAPI under their namespace.
- **Rate/resource protection:** generative endpoints may be soft-limited per session to protect local resources (`429 rate.limited`).
