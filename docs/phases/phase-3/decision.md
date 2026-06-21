# Phase 3 Decisions — Groq Analysis & Validation

Baseline: [DEC-003](../../decision.md), [DEC-005](../../decision.md), [DEC-006](../../decision.md).

---

## Decisions

### DEC-016 — Groq model and quota budget

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06-21 |
| **Category** | Tech |

**Context:** Rate limits confirmed for `llama-3.3-70b-versatile`.

**Decision:** **30 RPM · 1K RPD · 12K TPM · 100K TPD.** Stage A sample **450**; Stage C
**300** discovery-scoped; **20** reviews/batch; **2.5 s** sleep; ~**44** calls/run;
~**90K** tokens/run; reserve **~15K TPD** for chatbot.

**Alternatives considered:** 900-review sample (rejected — exceeds 100K TPD).

**Consequences:** Documented in `architecture.md` §9; enforce in `src/analysis/` sampler.

---

### DEC-017 — Stratified sample caps

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06-21 |
| **Category** | Business |

**Context:** 100K TPD caps total LLM input across Stages A + C.

**Decision:** Total Stage A cap **450**; per-cell caps per `pre_llm_strategy.md` §5.2;
oversample negative + discovery_candidate.

**Alternatives considered:** Random sample; 900-review sample.

**Consequences:** Document seed + caps in `run_metadata.json`.

---

### DEC-018 — Prompt versioning

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | |
| **Category** | Tech |

**Context:** Reproducibility and repair retries need version tracking.

**Decision:** _e.g. prompts in `src/analysis/prompts/v1/`; log `prompt_version: "v1"`_

**Alternatives considered:** Inline strings only.

**Consequences:** Bump version when changing system prompts; note in eval.md per run.

---

### DEC-019 — Word-count policy for theme summaries

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | |
| **Category** | Business |

**Context:** Validator must match dashboard display cap (≤250 words).

**Decision:** _e.g. split on whitespace; exclude markdown; truncate vs reject over limit_

**Alternatives considered:** Character count; reject vs auto-truncate.

**Consequences:** Same policy in validator and Streamlit render guard (Phase 4).

---

## Index (this phase)

| ID | Title | Status |
|---|---|---|
| DEC-016 | Groq model and quota budget | Accepted |
| DEC-017 | Stratified sample caps | Accepted |
| DEC-018 | Prompt versioning | Proposed |
| DEC-019 | Word-count policy | Proposed |
