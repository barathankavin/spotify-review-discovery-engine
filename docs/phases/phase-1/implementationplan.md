# Phase 1 — Ingestion & Normalization

**Goal:** Pull 8–12 weeks of public Spotify Play Store reviews and produce a clean,
PII-scrubbed `normalized_reviews.json` ready for embedding and analysis.

**Architecture reference:** `architecture.md` §5.1, §7 (`NormalizedReview`), §10 (#1–3, #6, #15)

---

## Prerequisites

- Phase 0 complete (scaffold, venv, dependencies installed).
- Network access for `google-play-scraper`.

---

## Scope

### In scope

- Plain Python module in `src/ingestion/` using `google-play-scraper`.
- Package: `com.spotify.music`, configurable 8–12 week lookback.
- Normalization pipeline: parse → filter → dedupe → PII scrub → persist.
- Ingestion report printed to stdout (counts, date range, drop reasons).

### Out of scope

- n8n, Apify, Zapier, or any workflow-automation platform.
- Login/authenticated scraping or ToS-violating automation.
- Embeddings or Groq calls (Phases 2–3).

---

## Data contract: `NormalizedReview`

Each record in `data/processed/normalized_reviews.json`:

| Field | Type | Notes |
|---|---|---|
| `review_id` | string | Stable hash or store id |
| `platform` | string | `"google_play"` |
| `date` | ISO date string | Review timestamp |
| `rating` | int | 1–5 stars |
| `title` | string | May be empty |
| `body` | string | PII-scrubbed review text |
| `app_version` | string | Optional; empty if missing |
| `thumbs_up` | int | Helpful count if available |

---

## Processing pipeline

```
google-play-scraper (com.spotify.music)
        │
        ▼
Parse & tolerate malformed rows
        │
        ▼
Time window filter (8–12 weeks, configurable)
        │
        ▼
Length filter (drop < 6 words, emoji-only)
        │
        ▼
Language filter (English only via langdetect; log drops)
        │
        ▼
Dedupe (same body + near timestamp)
        │
        ▼
PII scrub (emails, phone numbers in body text)
        │
        ▼
Write data/processed/normalized_reviews.json + report
```

---

## Suggested module structure

```
src/ingestion/
├── __init__.py
├── fetch.py          # google-play-scraper wrapper, pagination, lookback
├── normalize.py      # filters, dedupe, PII scrub
├── schema.py         # NormalizedReview dataclass / TypedDict
└── run.py            # CLI entry: python -m src.ingestion.run
```

---

## Configuration (non-secret)

| Parameter | Default | Purpose |
|---|---|---|
| `LOOKBACK_WEEKS` | 10 | How far back to fetch |
| `MIN_WORD_COUNT` | 6 | Drop very short reviews |
| `PACKAGE_NAME` | `com.spotify.music` | Spotify Android app |

---

## Cursor agent prompt

```
Implement Phase 1 — Ingestion & Normalization from @docs/architecture.md section 5.1 and
@docs/phases/phase-1/implementationplan.md.

Write a plain Python module under src/ingestion/ — do NOT use n8n, Apify, Zapier, or any
workflow automation tool. Use google-play-scraper to pull Spotify Play Store reviews
(package com.spotify.music) for the last 8-12 weeks (configurable).

Normalize into the NormalizedReview schema from architecture.md section 7:
review_id, platform, date, rating, title, body, app_version, thumbs_up.

Processing:
- Drop reviews under 6 words and emoji-only bodies
- Keep English only via langdetect; log non-English drop count
- Dedupe near-identical bodies with close timestamps
- Scrub PII patterns (emails, phone numbers) from review bodies
- Tolerate malformed rows — skip and log, don't crash

Save to data/processed/normalized_reviews.json.
Print an ingestion report: raw count, filtered counts by reason, deduped count, date range.

Add CLI: python -m src.ingestion.run
```

---

## Manual verification

1. Run ingestion: `python -m src.ingestion.run`
2. Inspect report — expect thousands of raw rows; filtered count reasonable for English + length.
3. Spot-check 10 random records in JSON: valid dates, ratings 1–5, no obvious PII.
4. Confirm date range spans ~8–12 weeks.
5. Search for discovery-related language (*recommend*, *discover*, *playlist*, *same songs*).

---

## Exit criteria

- [ ] `data/processed/normalized_reviews.json` exists with ≥ hundreds of reviews (Spotify volume).
- [ ] All records match `NormalizedReview` schema.
- [ ] Ingestion report shows breakdown of drops (language, length, dedupe).
- [ ] No usernames or reviewer IDs stored in output.
- [ ] PII regex pass applied to `body` fields.
- [ ] Re-run is idempotent (same input window → stable `review_id`s).

---

## Edge cases to handle

| Case | Handling |
|---|---|
| Non-English reviews | Drop; log count |
| Emoji-only / &lt;6 words | Drop |
| Duplicate spam | Hash/fuzzy dedupe |
| Malformed API rows | Skip + log |
| Partial fetch failure | Ingest valid rows; warn with counts |

---

## After this phase

1. Complete [eval.md](eval.md) — ingestion metrics, functional/edge tests, exit criteria sign-off.
2. Accept decisions in [decision.md](decision.md) (lookback, dedupe, review_id); index in [docs/decision.md](../../decision.md).
3. Commit processed JSON only if you want a reproducible snapshot without re-scraping.
4. Proceed to [Phase 2](../phase-2/implementationplan.md) only if eval **Pass**.

---

## Validates assumptions from problemStatement §12

- Review volume and date range are sufficient for downstream sampling.
- English-only filter drop rate is acceptable (not &gt;80% unless expected).
- No ground-truth premium flag exists — note for Phase 3 segment heuristics.

---

## Post-ingestion analysis (before Phase 3)

After Phase 1 completes, run corpus analysis and read the pre-LLM strategy:

```bash
python scripts/phase1_corpus_analysis.py
```

| Artifact | Purpose |
|---|---|
| [corpus_analysis.json](corpus_analysis.json) | Machine-readable stats |
| [pre_llm_strategy.md](pre_llm_strategy.md) | How to sample and generate themes/summaries before Groq |
