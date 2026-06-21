# Phase 3 — Groq Analysis, Validation & Artifacts

**Goal:** Transform a stratified review sample into validated theme clusters, unmet needs,
and inferred segment tags — all grounded in `review_id`s — using Groq with quota-safe
batching and checkpointing.

**Architecture reference:** `architecture.md` §5.3, §5.4, §9, §10 (#4–8, #10, #14)

---

## Prerequisites

- Phase 1 complete: `normalized_reviews.json`.
- Phase 2 complete: vector store (optional for sampling; analysis reads JSON directly).
- `GROQ_API_KEY` in `.env`.
- Current rate limits verified at `console.groq.com/docs/rate-limits`.

---

## Scope

### In scope

- Stratified sampling (rating tier × ISO week) **before** any LLM call.
- Groq Stages A–D with JSON outputs.
- Deterministic validation layer (structure, word limits, provenance, PII).
- Bounded repair retries on validation failure.
- Per-batch checkpointing for rate-limit resume.
- Persist: `themes.json`, `unmet_needs.json`, `segments.json`, `run_metadata.json`.

### Out of scope

- Dashboard rendering (Phase 4).
- Chatbot (Phase 5).
- Sending the **full** corpus to Groq — sampling is mandatory.

---

## Stage sequence

```
Stratified sample (rating tier × ISO week, seed logged)
        │
        ▼
Stage A — Theme discovery (Groq)
  Output: ≤5 ThemeClusters with labels, descriptions, supporting review_ids
        │
        ▼
Stage B — Quotes + summary per theme (Groq)
  Output: ≤250-word narrative + 3 verbatim quotes per theme
        │
        ▼
Stage C — Unmet needs (Groq)
  Output: ranked list (~5 max), each with supporting review_ids
        │
        ▼
Stage D — Segment heuristics (rules + optional Groq)
  Output: SegmentTags — always "inferred"
        │
        ▼
Validation layer → accept or bounded retry
        │
        ▼
Write data/processed/*.json
```

### Sampling rules

| Rating tier | Stars | Sampling note |
|---|---|---|
| Negative | ≤2 | Oversample — actionable signal |
| Neutral | 3 | Moderate cap |
| Positive | 4–5 | Lower cap per tier-week |

- Stratify by **ISO week** so one anomaly week cannot dominate.
- Cap per tier-week (configurable).
- Log: seed, caps, final sample size in `run_metadata.json`.

### Groq quota planning (confirmed 2026-06-21)

`llama-3.3-70b-versatile` limits: **30 RPM · 1K RPD · 12K TPM · 100K TPD**.

**TPD is the binding constraint.** Recommended locked budget (see `architecture.md` §9):

| Parameter | Value |
|---|---|
| Stage A sample | **450** reviews (stratified) |
| Stage C input | **300** discovery-scoped reviews (subset of sample) |
| Reviews per batch | **20** |
| Sleep between calls | **2.5 s** (raise to 10 s on TPM 429) |
| Est. chat calls / run | **~44** |
| Est. tokens / run | **~86–93K** (reserve **~15K** for chatbot same day) |

Do **not** use a 900-review sample on this tier — Stage A + C together would exceed 100K TPD.

---

## Validation checks (deterministic)

| Check | Rule |
|---|---|
| Theme count | ≤ 5 |
| Summary length | ≤ 250 words per theme (fixed counting policy) |
| Provenance | Every quote/cited `review_id` exists in corpus; text matches (substring or normalized whitespace) |
| PII | Block emails, phones, handles in all LLM output |
| JSON structure | Valid schema per stage; required fields present |

On failure: bounded retry with stricter prompt → abort and keep last-known-good if still invalid.

---

## Suggested module structure

```
src/analysis/
├── __init__.py
├── sampler.py          # stratified sample
├── groq_client.py      # batched calls, backoff, checkpointing
├── stages/
│   ├── stage_a_themes.py
│   ├── stage_b_summaries.py
│   ├── stage_c_unmet.py
│   └── stage_d_segments.py
├── validators.py       # provenance, PII, word count, theme cap
├── prompts/            # versioned system prompts (v1, v2, ...)
└── run.py              # orchestrate A→D + validate + persist
```

---

## Output artifacts

| File | Contents |
|---|---|
| `data/processed/themes.json` | ThemeClusters + WeeklyPulse summaries/quotes |
| `data/processed/unmet_needs.json` | Ranked UnmetNeed list |
| `data/processed/segments.json` | SegmentTags per review_id |
| `data/processed/run_metadata.json` | run_id, seed, model_id, prompt_version, Groq call counts |

---

## Cursor agent prompts

### Step 3a — Lock quota budget

```
Read @docs/architecture.md section 9 and @docs/phases/phase-3/implementationplan.md.
Check current Groq rate limits for llama-3.3-70b-versatile at console.groq.com/docs/rate-limits.
Propose batch size, sleep/backoff, sample cap, and checkpointing so a full Phase 3 run
never exceeds RPM/RPD/TPM/TPD. Update docs/architecture.md section 9 with the final
numbers you will implement against.
```

### Step 3b — Implement pipeline

```
Implement Phase 3 — Groq Analysis from @docs/architecture.md sections 5.3 and 5.4 and
@docs/phases/phase-3/implementationplan.md.

Stages A-D on a stratified sample (rating tier x ISO week) from normalized_reviews.json:
- Stage A: discover <=5 discovery/recommendation themes via Groq (JSON output)
- Stage B: per theme, verbatim quotes + <=250-word summary
- Stage C: ranked unmet needs list (max ~5) from "I wish / I want / why can't" language
- Stage D: inferred segment heuristics (rating tier, app_version, premium/free/ads keywords)

Implement validators: theme count, word limits, quote provenance, PII scan.
Bounded repair retry on validation failure.
Per-batch checkpointing so rate-limit errors mid-run can resume.

Persist themes.json, unmet_needs.json, segments.json, run_metadata.json under data/processed/.
Log model id and prompt version per Groq call.
Never send the full normalized corpus — sample only.
```

---

## Manual verification

1. Run: `python -m src.analysis.run`
2. Confirm theme count ≤ 5; labels relate to discovery/recommendations.
3. Spot-check 3 quotes — text appears verbatim in `normalized_reviews.json`.
4. Word-count each theme summary — all ≤ 250.
5. Scan outputs for email/phone patterns — none.
6. Kill mid-run and resume — checkpoint should continue, not restart from zero.

---

## Exit criteria

- [ ] All four output JSON files exist and parse cleanly.
- [ ] ≤ 5 themes; each has summary, quotes, supporting `review_id`s.
- [ ] Unmet needs ranked with provenance.
- [ ] Segments tagged with `inferred` flag in metadata.
- [ ] Validation runs automatically; failed output triggers retry or abort.
- [ ] `run_metadata.json` logs seed, model, prompt version, call counts.
- [ ] No full-corpus Groq calls — sample size logged and reasonable.

---

## Edge cases

| Case | Handling |
|---|---|
| Review-bombing week | Flag in metadata; don't let one week dominate sample |
| 5★ with complaint text | Theme from text, not rating alone |
| Off-topic reviews | Route to "Other" bucket; exclude from headline themes |
| Invalid JSON from Groq | Bounded retry with stricter prompt |
| Rate limit mid-run | Backoff + checkpoint resume |

---

## After this phase

1. Complete [eval.md](eval.md) — validator tests, theme table, checkpoint test, sign-off.
2. Accept decisions in [decision.md](decision.md) (Groq budget, sample caps, prompt version).
3. Commit code; optionally commit processed JSON for reproducibility.
4. Proceed to [Phase 4](../phase-4/implementationplan.md) only if eval **Pass**.

---

## Common pitfalls

- Letting Groq invent quotes not in corpus — provenance validator must catch this.
- Hard-coding 5 theme names — themes must emerge from data in Stage A.
- Skipping checkpointing — a rate limit at minute 20 wastes quota and time.
