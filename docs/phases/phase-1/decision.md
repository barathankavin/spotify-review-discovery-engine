# Phase 1 Decisions — Ingestion & Normalization

Baseline: [DEC-002 Plain Python ingestion](../../decision.md#dec-002--plain-python-ingestion-no-n8napifyzapier).

---

## Decisions

### DEC-009 — Lookback window (weeks)

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06-21 |
| **Category** | Business |

**Decision:** `LOOKBACK_WEEKS=10` (env / CLI `--lookback-weeks`).

---

### DEC-010 — Language detection library and threshold

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06-21 |
| **Category** | Tech |

**Decision:** `langdetect`; drop if detected language != `en`. Texts under 20 chars assumed English.

---

### DEC-011 — Dedupe strategy

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06-21 |
| **Category** | Tech |

**Decision:** Normalize body whitespace + lowercase hash; collapse duplicates within 24 hours.

---

### DEC-012 — `review_id` generation

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06-21 |
| **Category** | Tech |

**Decision:** Use Google Play `reviewId` when present; fallback SHA-256 of content + timestamp.

---

## Index (this phase)

| ID | Title | Status |
|---|---|---|
| DEC-009 | Lookback window | Accepted |
| DEC-010 | Language detection | Accepted |
| DEC-011 | Dedupe strategy | Accepted |
| DEC-012 | review_id generation | Accepted |
