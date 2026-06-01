# 09 · Feature — Multi-User, Memory & Privacy

| | |
|---|---|
| **Document** | Feature Spec — Multi-User, Memory & Privacy |
| **Doc ID** | NF-09 |
| **Version** | 0.1 (Draft) |
| **Last updated** | 2026-05-30 |
| **Related** | [03 Architecture](03-system-architecture.md), [04 Data](04-data-model-and-storage.md), [05 API](05-api-specification.md), [08 Characters](08-feature-character-management.md), [11 Realtime](11-feature-realtime-and-media-generation.md) |
| **Traces** | FR-MM-1 … FR-MM-12, FR-CM-8, NFR-PRIV-1/2/3/4, NFR-SEC-1/2/3 |

---

## 1. Overview

NagiFlow is **multi-character and multi-user** (FR-MM-1). The same character interacts with many people, and it must remember each of them **separately** — without bleeding one person's information into a conversation with another. Three mechanisms make this safe and usable:

1. **User classes & a permission matrix** — guests get basic chat; authenticated users get the full app (FR-MM-2/3/11).
2. **Scoped memory** — every memory belongs to a scope that binds it to a user, the character itself, or a character-to-character relationship, and retrieval is scope-aware (FR-MM-4/5/6).
3. **Sensitive mode** — a character can be prevented from revealing or referencing other users, enforced where it matters: at retrieval, in the prompt, and (optionally) on output (FR-MM-7/8/9).

This is the most privacy-sensitive part of NagiFlow; the design favors **enforcement at the data layer** over relying on the model to "behave" (ADR-005, NFR-PRIV-1).

---

## 2. User classes

| Class | How obtained | Capabilities (summary) |
|---|---|---|
| **Guest** | Auto-issued session, **no login** (FR-MM-2) | Converse with **guest-visible** characters only; basic, read-only-ish interaction. No advanced operations. |
| **Local user** | Authenticated session (login) | Full feature set: scripts, character authoring, memory inspection, media, modules, observability. |
| **Developer/admin** | A local user with the admin flag | Everything a user can do plus module install/permissions and system-level settings. |

> NagiFlow **never creates accounts on a user's behalf** and never performs password login automatically (NFR-SEC-3). Guests are anonymous sessions; promoting to a user requires the person to register/log in themselves.

### 2.1 Guest experience flow (FR-MM-2)

```mermaid
flowchart LR
    A[Open NagiFlow] --> B[Auto guest session issued]
    B --> C[Browse guest-visible characters]
    C --> D[Chat: send/receive turns]
    D --> E{Advanced action?}
    E -- e.g. edit character, scripts, memory --> F[Gated: prompt to log in]
    E -- no --> D
    F --> G[User logs in → full app]
```

The default landing state is a working **chat with a guest-visible character** — zero setup. Any attempt to reach an advanced operation is gated with a clear "log in to continue" path (FR-MM-2, FR-MM-11).

---

## 3. Permission matrix

Authorization is enforced **server-side** for every request and WebSocket action ([05 §2](05-api-specification.md), NFR-SEC-1). The matrix below is the source of truth; "guest-visible" is a per-character flag set by an owner ([08 §7](08-feature-character-management.md)).

| Operation | Guest | Local user | Admin |
|---|:---:|:---:|:---:|
| Start/own guest session | ✅ | — | — |
| Chat with **guest-visible** character | ✅ | ✅ | ✅ |
| Chat with **non-visible** character | ❌ | ✅ | ✅ |
| View character profile (public fields) | ✅ (visible chars) | ✅ | ✅ |
| **View/edit character memory** | ❌ | ✅ | ✅ |
| Create/edit/delete character | ❌ | ✅ | ✅ |
| Personality / voice training | ❌ | ✅ | ✅ |
| Export / import character | ❌ | ✅ | ✅ |
| Scripts (author/import/render/export) | ❌ | ✅ | ✅ |
| Media generation | ❌ | ✅ | ✅ |
| Observability dashboard | ❌ | ✅ | ✅ |
| Token/cost reports | ❌ | ✅ (own + aggregate per policy) | ✅ |
| Modules: enable/disable/configure | ❌ | ✅ (per policy) | ✅ |
| Modules: **install / permissions** | ❌ | ❌ | ✅ |
| System settings / providers config | ❌ | partial | ✅ |
| Toggle **sensitive mode** | ❌ | ✅ (chars they manage) | ✅ |
| Delete a user's data | ❌ | ✅ (self/own scope per policy) | ✅ |

Guests are confined to the first rows: **basic conversation only** (FR-MM-2, FR-MM-11). Everything that creates, reveals, or configures is user-gated.

---

## 4. Memory architecture & scoping

(Schema in [04 §5](04-data-model-and-storage.md); character-side view in [08 §5](08-feature-character-management.md).)

### 4.1 The three scopes (authoritative)

Every `memory_entry` has exactly one **scope**:

| Scope | Keying columns | Holds | Who may surface it |
|---|---|---|---|
| **`user_scoped`** | `character_id` + `user_id` | What the character knows **about a specific user** (the bulk of memories). | Only in a conversation **with that same user**. |
| **`character_general`** | `character_id` | User-agnostic self/world facts. | Any conversation (not user-specific). |
| **`character_interaction`** | `character_id` + `counterpart_character_id` | What the character recalls from **interacting with another character**. | Conversations involving that relationship; subject to sensitive-mode rules if it references users. |

This directly implements "a character keeps memories scoped to each user, and memories from interacting with other characters" (FR-MM-4/5, FR-CM-8).

> **Where `character_interaction` memories come from.** They are produced in **multi-character live sessions** (FR-RT-10): when the turn **director** lets character A respond to character B, the salient content of that exchange is written as a `character_interaction` memory on A keyed to counterpart B (and vice-versa) — see [11 §4.5](11-feature-realtime-and-media-generation.md). Outside a multi-character session this scope simply stays empty.

### 4.2 Vector namespaces

Retrieval indexes are partitioned so a query physically cannot pull another user's entries:

```
mem:<character_id>:user:<user_id>          # user_scoped (per user)
mem:<character_id>:general                 # character_general
mem:<character_id>:interaction:<counterpart_character_id>
```

At turn time the orchestrator queries only the namespaces permitted for the **current (character, user)** pair (and relevant interaction namespaces), then applies sensitive-mode filtering (§5). Isolation is structural, not advisory (NFR-PRIV-1).

### 4.3 Write & read policy

- **Write** — after a turn / on summarization, candidate memories are classified into a scope, scored for `importance`, embedded, and stored. The default scope for things learned about the speaking user is `user_scoped` bound to that user.
- **Read (retrieval)** — **scope-aware** top-K by **similarity + recency + importance**, restricted to permitted namespaces, then sensitive-mode-filtered (FR-MM-6).
- **Summarization** — periodic compaction turns many low-value entries into a few summaries to bound size and keep retrieval sharp (NFR-SCALE-1).
- **Decay / caps** — per-scope limits with importance-weighted pruning prevent unbounded growth (NFR-SCALE-1).

#### 4.3.1 Importance scoring (illustrative default)

`importance ∈ [0,1]` is computed at write time from cheap signals; the exact weights are **tunable defaults**, not a fixed contract:

```
importance = clamp01( w_emph · explicit_emphasis   # user said "remember…", or pinned
                    + w_nov  · novelty             # low similarity to existing entries in scope
                    + w_emo  · emotional_intensity # affect detected in the turn
                    + w_rec  · recurrence )        # topic seen across multiple turns
# defaults: w_emph 0.4, w_nov 0.25, w_emo 0.2, w_rec 0.15
```

Pinned/edited entries are floored to `importance = 1.0` and never auto-pruned ([08 §5.4](08-feature-character-management.md)).

#### 4.3.2 Retrieval ranking & summarization/decay triggers (illustrative)

- **Retrieval rank** — `rank = α·similarity + β·recency_decay + γ·importance` (defaults `α 0.6, β 0.2, γ 0.2`; `recency_decay = exp(−age / τ)`, τ per scope). Top-K (default K≈8, fits the context budget — [03 §4](03-system-architecture.md)).
- **Summarization trigger** — runs (off the response path) when a namespace exceeds a **soft entry cap** (default ~200) or on a periodic pass; clusters of low-importance, related entries are merged into a `summary` entry, originals pruned.
- **Decay / eviction** — when a namespace exceeds its **hard cap**, evict lowest `importance·recency_decay` first (never pinned). `expires_at` entries are dropped on expiry ([04 §5.3](04-data-model-and-storage.md)).

These thresholds are surfaced as config so an operator can trade memory size against recall.

---

## 5. Sensitive mode

**Sensitive mode** prevents a character from **mentioning or revealing other users** during a conversation (FR-MM-7/8). It is the privacy guarantee that makes public, multi-viewer streaming safe.

### 5.1 Configuration scope

Sensitive mode can be set at three levels, most specific wins (FR-MM-9):

| Level | Use |
|---|---|
| **Global default** | Operator-wide baseline. **Recommended ON** for any public/streaming deployment. |
| **Per-character** | A character is always sensitive (or not). |
| **Per-conversation** | Override for a specific session (e.g. a private 1:1 where cross-user context is fine). |

### 5.2 Enforcement layers (defense in depth)

```mermaid
flowchart TB
    Q[Turn begins] --> R[Layer 1: Retrieval filter<br/>exclude other-users' user_scoped;<br/>drop interaction entries referencing other users]
    R --> P[Layer 2: Prompt instruction<br/>do not reveal/reference other users]
    P --> G[LLM generates]
    G --> O[Layer 3 optional: Output guard<br/>scan/scrub leaked identifiers]
    O --> Out[Response to user]
```

1. **Retrieval filter (primary).** The query simply **never returns** memories scoped to other users, and filters `character_interaction` entries whose content references other users. If the data isn't in the prompt, it cannot be leaked (NFR-PRIV-1). This is the load-bearing layer.
2. **Prompt instruction.** A system directive tells the model not to reveal or reference other users, reinforcing the data-layer filter for any incidental context.
3. **Output guard (optional).** A configurable post-generation pass can scan for and scrub known other-user identifiers; available as a hook/module for deployments that want belt-and-suspenders. Off by default to avoid latency unless enabled. **Limits:** it matches only a known identifier set (names/handles the system can enumerate for the current scope) — it is **best-effort, not a guarantee**, and never the primary defense; the load-bearing protection remains Layer 1 (the data simply isn't retrieved).

### 5.3 What sensitive mode does **not** do

It does not erase the character's memory of the current user, nor block `character_general` facts. It scopes **outward** disclosure of *other* users. With sensitive mode **off** (e.g. a trusted private session) the character may use cross-user context the operator has deemed acceptable.

### 5.4 Edge cases

- **Public stream = everyone is "another user".** When live-chat viewers are routed in as inputs ([11 §6](11-feature-realtime-and-media-generation.md)), each viewer is a distinct (often guest) user; sensitive mode ON ensures the character won't surface one viewer's info to another. This is why the global default is ON for streaming.
- **Same user, different session.** `user_scoped` memory persists across that user's sessions (continuity), independent of sensitive mode.
- **Counterpart references users.** An interaction memory that embeds another user's info is filtered under sensitive mode even though its scope is `character_interaction`.

---

## 6. Data lifecycle & user rights

- **Deletion (FR-MM-10, NFR-PRIV-3).** Deleting a user **hard-deletes** their `user_scoped` memories across characters and removes their vector namespace(s); the user's conversations/messages are deleted or anonymized per policy. `character_general` and unrelated data are untouched.
- **Guest reaping (FR-MM-12).** Ephemeral **guest** principals are garbage-collected after session expiry/inactivity via the same hard-delete path (sessions + `user_scoped` memory + vector namespaces). On a public stream **every viewer is a distinct guest**, so reaping bounds row/namespace growth; generative use is also rate/resource-capped per guest to protect a shared instance ([04 §8](04-data-model-and-storage.md)).
- **Export hygiene (NFR-PRIV-2).** Character export excludes `user_scoped` memory by default so sharing a character never ships other people's data ([08 §6.2](08-feature-character-management.md)).
- **Local-first (NFR-PRIV-4).** All user data lives in the local workspace by default; nothing is sent to external services except what a configured provider/connector explicitly transmits to do its job, and that surface is visible in observability ([12](12-feature-observability.md)).
- **Auditability (NFR-SEC-2).** Sensitive operations — permission changes, sensitive-mode toggles, memory deletions, module permission grants — are written to the audit log ([04 §3](04-data-model-and-storage.md)).

---

## 7. Threat considerations (privacy-focused)

> The full cross-cutting threat model (modules, secrets, transport, supply chain) is consolidated in [16 Security & Threat Model](16-security-and-threat-model.md); this section covers the privacy slice.

| Concern | Mitigation |
|---|---|
| Cross-user memory leak | Structural namespace isolation + retrieval filter (§4.2, §5.2). |
| Guest escalation | Server-side permission matrix on every request/WS action (§3, NFR-SEC-1). |
| Account creation/credential misuse | NagiFlow never creates accounts or auto-logs-in; user supplies all credentials (NFR-SEC-3). |
| Leaking via shared character file | Export excludes user-scoped memory by default; import quarantines stray user memory (§6, [08 §6](08-feature-character-management.md)). |
| Prompt-injection coaxing disclosure | Primary defense is data exclusion (the info isn't present); prompt + optional output guard add depth. |
| Module exfiltration | Module permission model gates network/secret access ([06 §11](06-module-and-extension-system.md)). |

---

## 8. Requirements coverage

| Requirement | Where addressed |
|---|---|
| FR-MM-1 (multi-user & multi-character) | §1, §2 |
| FR-MM-2 (guest, no-login basic ops) | §2, §2.1 |
| FR-MM-3 (local account unlocks advanced) | §2, §2.1 |
| FR-MM-4 (per-user scoped memory) | §4.1 |
| FR-MM-5 (cross-character interaction memory) | §4.1 |
| FR-MM-6 (scope-aware retrieval) | §4.2, §4.3 |
| FR-MM-7 (sensitive mode) | §5 |
| FR-MM-8 (sensitive mode enforced multi-layer) | §5.2 |
| FR-MM-9 (sensitive-mode config levels) | §5.1 |
| FR-MM-10 (user data deletion) | §6 |
| FR-MM-11 (server-side permission matrix) | §3 |
| FR-MM-12 (guest lifecycle + per-guest quota) | §6, [04 §8](04-data-model-and-storage.md) |
| FR-CM-8 (memory bank scoping) | §4 |
| NFR-PRIV-1 (enforce at data layer) | §4.2, §5.2 |
| NFR-PRIV-2 (no leak on export) | §6 |
| NFR-PRIV-3 (deletion) | §6 |
| NFR-PRIV-4 (local-first) | §6 |
| NFR-SEC-1/2/3 | §3, §6, §7 |
