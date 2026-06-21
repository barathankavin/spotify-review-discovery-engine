# Phase 2 Decisions — Embedding & Vector Store

Baseline: [DEC-003 Groq for embeddings and generation](../../decision.md#dec-003--groq-for-embeddings-and-generation),
[DEC-004](../../decision.md#dec-004--chroma-local-vector-store).

---

## Decisions

### DEC-013 — Groq embedding model and document text

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06-21 |
| **Category** | Tech |

**Context:** Retrieval quality depends on model and what text is embedded.

**Decision:** Groq `nomic-embed-text-v1.5`; document = `title + " " + body`.

**Alternatives considered:** Local MiniLM; other Groq embedding models.

**Consequences:** Phase 5 must use **same** Groq model for query embedding.

---

### DEC-014 — Upsert / change detection

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | |
| **Category** | Tech |

**Context:** Weekly refresh should not re-embed unchanged reviews (saves Groq quota).

**Decision:** _e.g. content hash in Chroma metadata; skip if hash unchanged_

**Alternatives considered:** Always re-embed all; timestamp-only skip.

**Consequences:** Log new/skipped counts and Groq call count in embed CLI for eval.md.

---

### DEC-015 — Embedding batch size and backoff

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | |
| **Category** | Tech |

**Context:** ~27k reviews require hundreds of Groq embedding requests.

**Decision:** _e.g. batch 128 texts; 1s sleep between batches; checkpoint every batch_

**Alternatives considered:** batch 32 (safer); batch 256 (faster, riskier).

**Consequences:** Document in `architecture.md` §9; tune against console rate limits.

---

### DEC-016 — Similarity metric and score display

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | |
| **Category** | Tech |

**Context:** Phase 5 threshold depends on how similarity is computed.

**Decision:** _e.g. cosine similarity via Chroma; scores 0–1 higher = more similar_

**Alternatives considered:** L2 distance (invert for threshold).

**Consequences:** Document in Phase 5 decision for threshold tuning.

---

## Index (this phase)

| ID | Title | Status |
|---|---|---|
| DEC-013 | Groq embedding model and document text | Accepted |
| DEC-014 | Upsert / change detection | Proposed |
| DEC-015 | Embedding batch size and backoff | Proposed |
| DEC-016 | Similarity metric | Proposed |
