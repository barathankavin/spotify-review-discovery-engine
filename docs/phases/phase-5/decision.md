# Phase 5 Decisions — RAG Chatbot

Baseline: grounding and refusal requirements from `problemStatement.md` §5.3.

---

## Decisions

### DEC-023 — Retrieval parameters (top-k and threshold)

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | |
| **Category** | Tech |

**Context:** Balance recall vs noise; threshold prevents ungrounded Groq calls.

**Decision:** _e.g. TOP_K=8; SIMILARITY_THRESHOLD=0.40 (cosine)_

**Alternatives considered:** k=5; threshold 0.35 (more answers) vs 0.50 (stricter).

**Consequences:** Record tuned values in eval.md; must align with DEC-015 metric.

---

### DEC-024 — Refusal message (exact copy)

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | |
| **Category** | Business |

**Context:** Users must distinguish "no signal in corpus" from errors.

**Decision:** _"Not enough signal in the reviews to answer that."_

**Alternatives considered:** Suggest rephrasing; show retrieval scores to user.

**Consequences:** Use consistently; do not fall back to general knowledge.

---

### DEC-025 — Chat system prompt version

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | |
| **Category** | Tech |

**Context:** Citation format and grounding rules must be stable and logged.

**Decision:** _e.g. `chat_prompt_v1`; cite as `[review_id: abc123]` per claim_

**Alternatives considered:** Footnote-style citations.

**Consequences:** Bump version when changing citation rules; re-run Phase 5 eval.

---

### DEC-026 — Chat history in UI

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | |
| **Category** | Business |

**Context:** Session memory vs simplicity.

**Decision:** _e.g. Streamlit session state only; no DB persistence for MVP_

**Alternatives considered:** Persist turns to log file (questions + retrieved ids only).

**Consequences:** Refresh clears history; optional query log without PII.

---

## Index (this phase)

| ID | Title | Status |
|---|---|---|
| DEC-023 | Retrieval top-k and threshold | Proposed |
| DEC-024 | Refusal message copy | Proposed |
| DEC-025 | Chat system prompt version | Proposed |
| DEC-026 | Chat history in UI | Proposed |
