# Docs index — NagiFlow

NagiFlow is organized around **two primary flows** — **script production** (author or import →
render to voiced multimedia) and **live streaming** (dialogue / external input → real-time voice +
animation) — over a shared character / voice / personality / emotion stack and a modular
**provider + skill + connector** substrate ([01 §2.1](01-vision-and-scope.md)). The numbered docs
below are grouped by role; the number is just a stable file id, not a strict reading order.

## Foundations
| Doc | Title |
|---|---|
| 01 | [Vision & Scope](01-vision-and-scope.md) |
| 02 | [Requirements Specification](02-requirements-specification.md) |
| 03 | [System Architecture](03-system-architecture.md) |

## Data & API
| Doc | Title |
|---|---|
| 04 | [Data Model & Storage](04-data-model-and-storage.md) |
| 05 | [API Specification](05-api-specification.md) |

## Extensibility
| Doc | Title |
|---|---|
| 06 | [Module & Extension System](06-module-and-extension-system.md) |

## Feature specs
Mapped to the two primary flows + the supporting layer:

- **Flow 1 · Script production** — [07 Script Management](07-feature-script-management.md); rendering in [11 §3](11-feature-realtime-and-media-generation.md).
- **Flow 2 · Live streaming** — [11 Realtime Interaction & Media Generation §4–6](11-feature-realtime-and-media-generation.md).
- **Supporting layer** — [08 Character Management](08-feature-character-management.md), [09 Multi-User, Memory & Privacy](09-feature-multiuser-memory-and-privacy.md), [10 Emotion & Affect](10-feature-emotion-and-affect.md), [12 Observability](12-feature-observability.md).

| Doc | Title |
|---|---|
| 07 | [Feature — Script Management](07-feature-script-management.md) |
| 08 | [Feature — Character Management](08-feature-character-management.md) |
| 09 | [Feature — Multi-User, Memory & Privacy](09-feature-multiuser-memory-and-privacy.md) |
| 10 | [Feature — Emotion & Affect](10-feature-emotion-and-affect.md) |
| 11 | [Feature — Realtime Interaction & Media Generation](11-feature-realtime-and-media-generation.md) |
| 12 | [Feature — Observability](12-feature-observability.md) |

## Experience
| Doc | Title |
|---|---|
| 13 | [UI / UX Design](13-ui-ux-design.md) |

## Operations
| Doc | Title |
|---|---|
| 14 | [Runtime & Deployment](14-runtime-and-deployment.md) |
| 15 | [Roadmap & Milestones](15-roadmap-and-milestones.md) |
| 16 | [Security & Threat Model](16-security-and-threat-model.md) |

## Reference
| Doc | Title |
|---|---|
| 17 | [Glossary](17-glossary.md) |

## Maintaining these docs
- **Stable numbers.** A doc's number and `Doc ID` (`NF-NN`) are stable. **Add a new doc at the next-highest free number** — do not renumber existing docs to insert one. Reading/topic order is expressed by the grouping above, not by the file number; this keeps cross-references from breaking.
- **Cross-references** use `[NN Title](NN-...md)` (and optional `§x`); keep the number in the link text matching the target file's number.
