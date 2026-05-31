# 15 · Security & Threat Model

| | |
|---|---|
| **Document** | Security & Threat Model |
| **Doc ID** | NF-15 |
| **Version** | 0.1 (Draft) |
| **Last updated** | 2026-05-31 |
| **Related** | [02 SRS §6.5](02-requirements-specification.md), [05 API §2](05-api-specification.md), [06 Modules §11](06-module-and-extension-system.md), [09 Privacy](09-feature-multiuser-memory-and-privacy.md), [13 Runtime §4](13-runtime-and-deployment.md) |
| **Traces** | NFR-SEC-1/2/3/4, NFR-PRIV-1/2/3/4, FR-MM-11, FR-MOD-8/10 |

---

## 1. Purpose & scope

Security and privacy controls are specified in detail across several documents; this document is the **consolidated, authoritative map** of them — the single place to understand NagiFlow's threat model, the trust boundaries, and where each control is enforced. It does **not** re-specify behavior (the linked sections remain authoritative); it summarizes, connects, and fills gaps that span documents.

NagiFlow's stance reflects its nature: a **local-first, single-operator** application that can optionally face an audience (public streaming). The dominant risks are therefore **cross-user data leakage**, **untrusted module code**, and **secret mishandling** — not multi-tenant server compromise.

---

## 2. Security principles

| Principle | Where enforced |
|---|---|
| **Server-side authorization, always** | Every protected route/WS action checks the permission matrix; the client never decides access ([05 §2](05-api-specification.md), [09 §3](09-feature-multiuser-memory-and-privacy.md), NFR-SEC-1). |
| **Privacy at the data layer, not the prompt** | Memory scoping + sensitive-mode retrieval filtering prevent leakage structurally ([09 §4–5](09-feature-multiuser-memory-and-privacy.md), ADR-005, NFR-PRIV-1). |
| **Least privilege for modules** | A module gets only what its manifest declares; everything else is denied ([06 §11](06-module-and-extension-system.md), NFR-SEC-3). |
| **No ambient secrets** | Secrets come from env / OS store, are never logged, committed, or embedded in URLs ([13 §4](13-runtime-and-deployment.md), NFR-SEC-2). |
| **Local by default** | No content leaves the machine except what a user-configured provider/connector must transmit; no telemetry without opt-in (NFR-PRIV-1/4). |
| **No silent account creation** | Accounts/credentials are always user-initiated; NagiFlow never logs in on a user's behalf (NFR-SEC-3). |

---

## 3. Identity, authorization & secrets

### 3.1 Authentication & sessions
Specified in [05 §2](05-api-specification.md): two principal kinds (**guest**, **user**; admin = user + flag — [09 §2](09-feature-multiuser-memory-and-privacy.md)); **opaque session tokens** (only the hash stored), idle/absolute expiry, revocation (logout / logout-all); local passwords hashed with **Argon2id**; cookie transport is **HttpOnly + SameSite + Secure** with double-submit **CSRF** protection; Bearer clients exempt.

### 3.2 Authorization
The **permission matrix** ([09 §3](09-feature-multiuser-memory-and-privacy.md), FR-MM-11) is the source of truth, enforced server-side on every request and WebSocket action. Guests are confined to basic conversation with guest-visible characters; everything that creates, reveals, or configures is user/admin-gated. **Module install + permission grants are admin-only.**

### 3.3 Secrets handling
- Provider/connector credentials are supplied by the **user**, read from **environment / OS secret store**, never written to the repo or the shareable workspace config ([13 §4](13-runtime-and-deployment.md)).
- Secrets are **redacted** from all logs (core + module loggers pass through the same redaction — [11 §4](11-feature-observability.md)); never placed in URLs or query strings.
- In the UI, secret fields are **write-only/masked**; settings show env secrets as "set/unset", never values ([12 §7.9](12-ui-ux-design.md)).
- Modules read only their **declared** secrets via `host.secret(k)`; undeclared keys return `None` ([06 §11](06-module-and-extension-system.md)).

---

## 4. Module trust & sandboxing

Modules are the largest attack surface (third-party code in-process). Controls ([06 §11](06-module-and-extension-system.md), NFR-SEC-3, FR-MOD-8/10):

- **Manifest-declared least privilege** — `network` / `filesystem` / `subprocess` / `secrets` allowlists; anything unlisted is denied by the guarded `host` clients.
- **Trust signaling & consent** — official vs third-party badge; the requested permission set is shown for explicit operator consent at install/enable ([12 §7.8](12-ui-ux-design.md)).
- **Quarantine** — a module that throws on load/registration is disabled and reported, not allowed to crash the host (NFR-REL-2).
- **Auditing** — install, enable/disable, config and permission-grant changes are written to the audit log (§9).
- **Known limitation (honest):** Python cannot perfectly sandbox in-process code — the allowlists are *least-privilege-by-contract plus auditing*, not a hard jail.
  - **Trust boundary for shared/public instances:** an instance exposed to guests/the public must run **only official/trusted modules**; installing third-party modules is an **admin action for the operator's own machine**.
  - **Extension space (future hardening):** true isolation of untrusted modules (subprocess / WASM / container) is the planned upgrade before any "run untrusted modules on a shared instance" use case ([14 risks](14-roadmap-and-milestones.md)).

---

## 5. Privacy & memory threats

The privacy-critical surface; specified in [09](09-feature-multiuser-memory-and-privacy.md).

- **Cross-user memory leak** → structural **namespace isolation** + scope-aware retrieval; a query physically cannot pull another user's entries ([09 §4.2](09-feature-multiuser-memory-and-privacy.md), NFR-PRIV-1).
- **Disclosure on public streams** → **sensitive mode** (retrieval filter primary, prompt instruction, optional output guard), default **ON** for public/streaming; output guard is **best-effort only**, never the primary defense ([09 §5](09-feature-multiuser-memory-and-privacy.md)).
- **Leak via shared character file** → export excludes `user_scoped` memory by default; import quarantines stray user memory ([08 §6.2](08-feature-character-management.md), NFR-PRIV-2).
- **Unbounded guest data** → guest reaping (TTL/inactivity GC of sessions + scoped memory + namespaces) + per-guest rate/resource caps ([09 §6](09-feature-multiuser-memory-and-privacy.md), [04 §8](04-data-model-and-storage.md), FR-MM-12).
- **Right to deletion** → deleting a user hard-deletes their scoped memory + namespaces; conversations deleted/anonymized per policy (NFR-PRIV-3).

---

## 6. Transport & API security

- **Local-first transport** — same-origin in prod (FastAPI serves the SPA); when exposed beyond localhost, TLS is the operator's responsibility (reverse proxy) and is recommended in any networked deployment.
- **WebSocket auth** — session via **HttpOnly cookie** or `Sec-WebSocket-Protocol` bearer; **never** a query-string token (avoids log/history leakage) ([05 §5](05-api-specification.md)).
- **Resource protection** — generative endpoints may be soft-limited per session (`429 rate.limited`); guests are additionally capped (§5). Long work runs as cancellable jobs, not unbounded request threads.
- **Error hygiene** — the error envelope returns a stable `code` + `correlation_id`, **not** stack traces or secret-bearing detail ([05 §3](05-api-specification.md)); provider failures are isolated and surfaced without crashing the request.
- **Idempotency** — replay-safe via `Idempotency-Key` with bounded TTL ([05 §1](05-api-specification.md)).

---

## 7. Supply chain & dependencies

- **Pinned versions** for integrated AI components (LLM/TTS/ASR runtimes) behind the provider contract; provider/API churn is a tracked risk ([14 §5](14-roadmap-and-milestones.md)).
- **License hygiene** — integrated OSS licenses honored and surfaced (e.g. VoxCPM Apache-2.0); **non-MIT** optional renderer modules (Live2D Cubism SDK) ship **separately** so the MIT core stays unencumbered ([14 §7](14-roadmap-and-milestones.md)).
- **Misuse guidance** — upstream voice-cloning/deepfake warnings are preserved in product guidance (NFR-COMP-1/2).
- **No telemetry** — nothing is sent to a third party unless an operator configures a provider/connector that requires it; that surface is visible in observability ([11](11-feature-observability.md), NFR-PRIV-4).

---

## 8. Threat model summary

| Asset | Threat | Primary mitigation | Owner |
|---|---|---|---|
| Other users' memories | Cross-user leak in conversation | Namespace isolation + scope-aware retrieval; sensitive mode | [09 §4–5](09-feature-multiuser-memory-and-privacy.md) |
| Advanced operations | Guest privilege escalation | Server-side permission matrix on every request/WS action | [09 §3](09-feature-multiuser-memory-and-privacy.md) |
| Credentials | Theft / leak via logs/URLs/repo | Env/OS-store secrets, redaction, masked UI, never committed | §3.3, [13 §4](13-runtime-and-deployment.md) |
| Host machine / data | Malicious or buggy module | Manifest least-privilege + guarded host + consent + quarantine; trusted-only on shared instances | §4, [06 §11](06-module-and-extension-system.md) |
| Local accounts | Password compromise | Argon2id hashing; no plaintext; revocable sessions | [05 §2](05-api-specification.md) |
| Shared character file | Embedded user data | Export strips `user_scoped` by default; import quarantine | [08 §6](08-feature-character-management.md) |
| Local resources | DoS via guest generation | Per-guest rate/resource caps; guest reaping | §5, [09 §6](09-feature-multiuser-memory-and-privacy.md) |
| Model output | Prompt-injection coaxing disclosure | Data exclusion is primary (info absent); prompt + optional output guard add depth | [09 §5/§7](09-feature-multiuser-memory-and-privacy.md) |
| Session token | Interception (networked deploy) | HttpOnly/Secure cookie or subprotocol; operator TLS; never in query string | §6 |

---

## 9. Auditing & traceability

- **Audit log** records security-relevant actions — permission changes, sensitive-mode toggles, memory deletions, module enable/disable & permission grants ([04 §5.8](04-data-model-and-storage.md), NFR-SEC-2), distinct from operational logs.
- **Correlation IDs** thread request → WS turn → jobs → usage/log records for after-the-fact tracing ([05 §1](05-api-specification.md), [11 §4](11-feature-observability.md)).
- **Redaction** applies uniformly to core and module loggers; user message content is not logged at info level by default.

---

## 10. Known limitations & extension space

Explicitly **deferred / best-effort** (reserved for later hardening — not silent gaps):

- **In-process module isolation** — process/WASM/container sandbox is future work; today's model is least-privilege-by-contract + audit + trusted-only-on-shared-instances (§4).
- **Sensitive-mode output guard** — best-effort identifier scrub; the load-bearing control is data exclusion at retrieval ([09 §5.2](09-feature-multiuser-memory-and-privacy.md)).
- **TLS / network exposure** — not configured by default (local-first); the operator adds a TLS-terminating proxy for any networked deployment (§6).
- **Unimplemented external-service fields** — capability flags let the app degrade gracefully when a provider lacks a feature; such fields are **reserved extension space**, not security guarantees.

---

## 11. Requirements coverage

| Requirement | Where addressed |
|---|---|
| NFR-SEC-1 (server-side authz) | §2, §3.2 |
| NFR-SEC-2 (secret handling, redaction) | §3.3, §9 |
| NFR-SEC-3 (module permissions; no auto-login) | §3.1, §4 |
| NFR-SEC-4 (log redaction) | §3.3, §9 |
| NFR-PRIV-1 (data-layer enforcement) | §2, §5 |
| NFR-PRIV-2 (no leak on export) | §5 |
| NFR-PRIV-3 (deletion) | §5 |
| NFR-PRIV-4 (local-first, no telemetry) | §2, §7 |
| FR-MM-11 (permission matrix) | §3.2 |
| FR-MM-12 (guest lifecycle/caps) | §5 |
| FR-MOD-8/10 (module gating/permissions) | §4 |
