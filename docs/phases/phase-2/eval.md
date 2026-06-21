# Phase 2 Evaluation — Embedding & Vector Store

**Plan:** [implementationplan.md](implementationplan.md)  
**Evaluated by:** _name_  
**Date:** _YYYY-MM-DD_  
**Result:** ☐ Pass  ☐ Fail  ☐ Pass with notes

---

## 1. Test environment

| Item | Value |
|---|---|
| Normalized review count (Phase 1) | |
| Embedding model | |
| Chroma path | `vector_store/` |
| Branch / commit | |

---

## 2. Embed run metrics

| Metric | Run 1 | Run 2 (re-run) | Pass? |
|---|---|---|---|
| Reviews embedded | | | ☐ |
| Newly added | | | ☐ |
| Skipped (unchanged) | N/A | | ☐ (Run 2 should skip most) |
| Groq API calls (embeddings) | logged | logged | ☐ |
| Duration | | | |

---

## 3. Functional tests

| # | Test | Command / steps | Expected | Pass? |
|---|---|---|---|---|
| T2.1 | Full embed | `python -m src.embeddings.run` | Exit 0; Chroma files under `vector_store/` | ☐ |
| T2.2 | Collection size | Query collection count | Equals normalized review count | ☐ |
| T2.3 | Upsert idempotency | Run embed twice | No duplicates; Run 2 skips unchanged | ☐ |
| T2.4 | Metadata safety | Inspect Chroma metadata sample | `review_id`, `rating`, `date`, `app_version` only — no PII | ☐ |
| T2.5 | Query CLI | `--query "..."` | Returns 5 results with scores | ☐ |

---

## 4. Retrieval quality tests (required)

Run query CLI for each row. Record top-1 `review_id` and whether text is on-theme.

| # | Query | Top-1 relevant? | Top-3 all on-theme? | Pass? |
|---|---|---|---|---|
| T2.6 | "why does it keep playing the same songs" | ☐ | ☐ | ☐ |
| T2.7 | "discover weekly never updates" | ☐ | ☐ | ☐ |
| T2.8 | "can't find music for working out" | ☐ | ☐ | ☐ |

**Top-1 review snippets (paste brief evidence):**

| Query | review_id | snippet |
|---|---|---|
| T2.6 | | |
| T2.7 | | |
| T2.8 | | |

---

## 5. Exit criteria

| # | Criterion | Pass? | Evidence |
|---|---|---|---|
| E2.1 | One Chroma entry per normalized review | ☐ | count: |
| E2.2 | Upsert by `review_id`; no full rebuild on re-run | ☐ | |
| E2.3 | Query CLI returns 5 results with scores | ☐ | |
| E2.4 | ≥3 test queries semantically relevant | ☐ | |
| E2.5 | Embeddings via Groq API (`nomic-embed-text-v1.5`) | ☐ | |
| E2.6 | Batch checkpointing and rate-limit backoff | ☐ | |

---

## 6. Decisions recorded this phase

| DEC ID | Title | Accepted? |
|---|---|---|
| DEC-003 | Local embeddings | ☐ (baseline) |
| DEC-004 | Chroma vector store | ☐ (baseline) |
| | | |

---

## 7. Issues and follow-ups

| ID | Issue | Severity | Resolution |
|---|---|---|---|
| | | | |

---

## 8. Sign-off

**Phase 2 complete:** ☐ Yes — proceed to [Phase 3](../phase-3/implementationplan.md)

**Notes:**
