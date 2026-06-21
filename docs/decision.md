# Decision Log — Spotify Review Discovery Engine

Record **tech and business decisions** that affect implementation, scope, or operations.
Each entry is immutable once accepted — if a decision changes, add a new entry that
supersedes the old one.

## How to use

| When | Action |
|---|---|
| Before or during a phase | Add a draft entry under the phase section or create `docs/phases/phase-N/decision.md` |
| Decision is final | Set status to **Accepted**, fill consequences, link from phase `eval.md` if it affects exit criteria |
| Decision is reversed | Mark old entry **Superseded**; add new entry with `Supersedes: DEC-XXX` |

### Entry template

```markdown
### DEC-XXX — Short title

| Field | Value |
|---|---|
| **Status** | Proposed / Accepted / Superseded |
| **Date** | YYYY-MM-DD |
| **Phase** | 0–6 or Cross-cutting |
| **Category** | Tech / Business / Ops / Privacy |

**Context** — What problem or fork prompted this?

**Decision** — What we chose.

**Alternatives considered** — What we did not choose and why.

**Consequences** — Trade-offs, follow-ups, impact on other phases.
```

---

## Cross-cutting decisions (baseline)

These are pre-established by `problemStatement.md` and `architecture.md`. Mark **Accepted**
unless you explicitly change them during build — then add a new DEC entry.

### DEC-001 — Dashboard as delivery surface (no MCP/Gmail/Docs)

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2025-06-21 |
| **Phase** | Cross-cutting |
| **Category** | Business |

**Context** — Reference milestone used Gmail/Docs MCP for insight delivery.

**Decision** — Streamlit dashboard + embedded chatbot is the only output surface. No MCP,
Gmail, or Google Docs integration.

**Alternatives considered** — Static PDF report; email digest; Notion export.

**Consequences** — PMs interact live with data; no external write integrations to maintain.

---

### DEC-002 — Plain Python ingestion (no n8n/Apify/Zapier)

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2025-06-21 |
| **Phase** | 1 |
| **Category** | Tech |

**Context** — Ingestion could use workflow automation or scraping-as-a-service platforms.

**Decision** — `google-play-scraper` in `src/ingestion/`, run in-process by Cursor/operator.

**Alternatives considered** — n8n workflow; Apify actor; Zapier zap.

**Consequences** — Single codebase and dependency tree; operator runs CLI locally or in CI.

---

### DEC-003 — Groq for embeddings and generation

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06-21 |
| **Phase** | 2, 3, 5 |
| **Category** | Tech |

**Context** — Embeddings could use a local model or Groq; generation already uses Groq.

**Decision** — Use **Groq Embeddings API** (`nomic-embed-text-v1.5`) for Phase 2 corpus
indexing and Phase 5 query encoding. Use Groq chat completions for Phase 3 analysis and
Phase 5 answer generation.

**Alternatives considered** — Local `sentence-transformers/all-MiniLM-L6-v2` (prior plan);
OpenAI embeddings.

**Consequences** — Single vendor and API key; must budget embedding RPM/TPM for ~27k
reviews on first index; `GROQ_API_KEY` required from Phase 2 onward.

---

### DEC-004 — Chroma local vector store

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2025-06-21 |
| **Phase** | 2 |
| **Category** | Tech |

**Context** — Vector storage could be hosted (Pinecone, Weaviate) or local.

**Decision** — File-persisted Chroma under `vector_store/`, keyed by `review_id`.

**Alternatives considered** — Hosted vector DB; FAISS-only without metadata.

**Consequences** — Ephemeral disk on Streamlit Cloud requires rebuild or snapshot strategy (Phase 6).

---

### DEC-005 — Max 5 discovery/recommendation themes

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2025-06-21 |
| **Phase** | 3 |
| **Category** | Business |

**Context** — Unbounded clustering produces unreadable PM output.

**Decision** — Stage A discovers ≤5 themes scoped to discovery/recommendation friction.

**Alternatives considered** — 10 themes; hierarchical taxonomy; unsupervised cluster count via elbow method.

**Consequences** — Validator enforces cap; off-topic reviews routed to "Other" bucket.

---

### DEC-006 — Segments are inferred, not verified

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2025-06-21 |
| **Phase** | 3, 4, 5 |
| **Category** | Business |

**Context** — Play Store reviews lack premium/demographic ground truth.

**Decision** — Segment tags derived from text heuristics; UI and chatbot must label as inferred.

**Alternatives considered** — Omit segments; claim demographic personas from text.

**Consequences** — Required disclaimer on Segments tab; no persona language in chatbot answers.

---

## Phase-specific decisions

Add entries below or in the linked phase `decision.md` files as you build.

| Phase | Decision file | Entries |
|---|---|---|
| 0 | [phases/phase-0/decision.md](phases/phase-0/decision.md) | Python version, repo layout, dependency pins |
| 1 | [phases/phase-1/decision.md](phases/phase-1/decision.md) | Lookback weeks, language filter, dedupe strategy |
| 2 | [phases/phase-2/decision.md](phases/phase-2/decision.md) | Embedding model, similarity metric, upsert hash |
| 3 | [phases/phase-3/decision.md](phases/phase-3/decision.md) | Groq model, batch size, sample caps, prompt version |
| 4 | [phases/phase-4/decision.md](phases/phase-4/decision.md) | Chart library, last-known-good paths, UI copy |
| 5 | [phases/phase-5/decision.md](phases/phase-5/decision.md) | top-k, similarity threshold, refusal message |
| 6 | [phases/phase-6/decision.md](phases/phase-6/decision.md) | Host, Chroma cold-start, refresh cadence |

---

## Index (append as you add decisions)

| ID | Title | Status | Phase |
|---|---|---|---|
| DEC-001 | Dashboard as delivery surface | Accepted | Cross-cutting |
| DEC-002 | Plain Python ingestion | Accepted | 1 |
| DEC-003 | Groq for embeddings and generation | Accepted | 2, 3, 5 |
| DEC-004 | Chroma local vector store | Accepted | 2 |
| DEC-005 | Max 5 themes | Accepted | 3 |
| DEC-006 | Segments inferred not verified | Accepted | 3, 4, 5 |

<!-- Add new rows above this line -->
