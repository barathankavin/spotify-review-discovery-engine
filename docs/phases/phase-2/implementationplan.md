# Phase 2 — Embedding & Vector Store

**Goal:** Embed every normalized review via **Groq** and persist to Chroma keyed by
`review_id`, enabling semantic retrieval for the Phase 5 chatbot.

**Architecture reference:** `architecture.md` §5.2, §9 (embedding quota), §10 (#9)

---

## Prerequisites

- Phase 1 complete: `data/processed/normalized_reviews.json` exists.
- `GROQ_API_KEY` in `.env` (same key as Phases 3 & 5).
- `groq` Python SDK installed (`pip install groq`).

---

## Scope

### In scope

- Embeddings via **Groq Embeddings API** — model `nomic-embed-text-v1.5` (or current
  Groq equivalent; verify at `console.groq.com/docs/models`).
- Chroma collection persisted under `vector_store/`.
- Upsert by `review_id` — incremental on re-run, not full rebuild.
- Batched API calls with sleep/backoff and checkpointing on rate limits.
- CLI sanity check: query → top-5 similar reviews with scores.

### Out of scope

- Local `sentence-transformers` / on-device embedding models.
- Analysis or dashboard (Phases 3–4).
- Hosted vector DB (local Chroma only for now).

---

## Design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Embedding provider | Groq API (`client.embeddings.create`) | Single LLM vendor across pipeline |
| Embedding model | `nomic-embed-text-v1.5` | Groq-supported; strong semantic retrieval |
| Vector store | Chroma (file-persisted) | Zero infra; swappable later |
| Document text | `title + body` concatenation | Richer retrieval signal |
| Batch size | 64–128 texts per API call | Balance throughput vs rate limits |
| Metadata stored | `review_id`, `rating`, `date`, `app_version`, content hash | Filter/display; skip unchanged |
| Key | `review_id` | Enables upsert on weekly refresh |

**Important:** The chatbot retrieval pool is the **full normalized corpus**, not the
analysis sample used in Phase 3. Phase 5 **must** use the **same Groq embedding model**
for query encoding.

---

## Suggested module structure

```
src/embeddings/
├── __init__.py
├── groq_embedder.py  # Groq client, batch embed, backoff
├── store.py          # Chroma collection CRUD, upsert logic
└── run.py            # CLI: embed all + optional query mode

# Query sanity check:
# python -m src.embeddings.run --query "why does it keep playing the same songs"
```

---

## Processing flow

```
Read normalized_reviews.json
        │
        ▼
For each review: compose text = title + " " + body
        │
        ▼
Batch encode via Groq embeddings API (nomic-embed-text-v1.5)
  • batches of 64–128; sleep/backoff on 429; checkpoint per batch
        │
        ▼
Upsert into Chroma (id = review_id, skip unchanged if hash matches)
        │
        ▼
Log: total embedded, newly added, skipped unchanged, Groq call count
```

---

## Cursor agent prompt

```
Implement Phase 2 — Embedding & Vector Store from @docs/architecture.md section 5.2 and
@docs/phases/phase-2/implementationplan.md.

Embed data/processed/normalized_reviews.json using the Groq Embeddings API
(client.embeddings.create) with model nomic-embed-text-v1.5 (or current Groq equivalent).
Load GROQ_API_KEY from .env.

Upsert into a persistent Chroma collection at vector_store/, keyed by review_id.

Requirements:
- Store metadata: review_id, rating, date, app_version, content_hash (no PII)
- Document text = title + body
- Batch 64–128 texts per Groq request; exponential backoff + checkpoint on rate limits
- Re-running should only embed new/changed reviews (compare content hash or missing ids)
- Do NOT use sentence-transformers or other local embedding models

Add CLI:
- python -m src.embeddings.run              # embed/upsert all
- python -m src.embeddings.run --query "..."  # embed query via Groq, print top 5 similar reviews + scores
```

---

## Manual verification

1. Set `GROQ_API_KEY` in `.env`.
2. Run full embed: `python -m src.embeddings.run`
3. Confirm `vector_store/` directory created with Chroma persistence files.
4. Run query sanity check:
   ```
   python -m src.embeddings.run --query "why does it keep playing the same songs"
   ```
5. Top results should mention repetition, Discover Weekly, or recommendation fatigue.
6. Re-run embed — log should show skips for unchanged reviews (no full rebuild).

---

## Exit criteria

- [ ] Chroma collection contains one entry per normalized review.
- [ ] Upsert-by-`review_id` works; second run does not duplicate or full-rebuild.
- [ ] Query CLI returns 5 results with similarity scores.
- [ ] Retrieval results are semantically relevant for at least 3 test queries.
- [ ] Embeddings produced via Groq API (logged model id + call count).
- [ ] Rate-limit backoff and batch checkpointing implemented.

### Suggested test queries

| Query | Expected retrieval theme |
|---|---|
| "why does it keep playing the same songs" | Algorithm repetition |
| "discover weekly never updates" | Playlist fatigue |
| "can't find music for working out" | Genre/mood gaps |

---

## After this phase

1. Complete [eval.md](eval.md) — embed metrics, Groq call counts, 3 query tests, sign-off.
2. Accept decisions in [decision.md](decision.md) (Groq model, batch size, upsert hash).
3. Commit code; `vector_store/` stays gitignored.
4. Proceed to [Phase 3](../phase-3/implementationplan.md) only if eval **Pass**.

---

## Common pitfalls

- Embedding the analysis sample only — must embed **all** normalized reviews.
- Storing reviewer names in Chroma metadata — forbidden.
- Full rebuild every run — breaks weekly refresh efficiency and wastes Groq quota.
- Using a different embedding model in Phase 5 than Phase 2 — breaks retrieval quality.
- No checkpointing on ~27k reviews — a mid-run 429 forces expensive restart.
