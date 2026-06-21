# Phase 6 Decisions — Deployment & Operations

---

## Decisions

### DEC-027 — Hosting platform

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | |
| **Category** | Ops |

**Context:** Need shareable URL for PM/stakeholder access.

**Decision:** _e.g. Streamlit Community Cloud (primary)_

**Alternatives considered:** Render with persistent disk; local-only demo.

**Consequences:** Ephemeral disk → requires DEC-028; document in `deployment_plan.md`.

---

### DEC-028 — Chroma cold-start strategy

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | |
| **Category** | Tech |

**Context:** Streamlit Cloud disk is ephemeral.

**Decision:** _e.g. rebuild from committed `normalized_reviews.json` on app startup_

**Alternatives considered:** Commit small vector snapshot; hosted Pinecone.

**Consequences:** Startup latency; may need `@st.cache_resource` or progress UI.

---

### DEC-029 — Weekly refresh cadence and ownership

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | |
| **Category** | Business |

**Context:** Review signal goes stale without refresh.

**Decision:** _e.g. manual every Monday; optional GitHub Action cron later_

**Alternatives considered:** Daily scrape; no refresh until requested.

**Consequences:** Document in `deployment_plan.md`; assign operator in eval.md.

---

### DEC-030 — Commit processed JSON to git?

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | |
| **Category** | Ops |

**Context:** Deploy without re-running Groq on every cold start.

**Decision:** _e.g. commit validated `data/processed/*.json` for demo snapshot; gitignore raw_

**Alternatives considered:** Regenerate all artifacts in CI only.

**Consequences:** Repo size; ensure no PII in committed JSON.

---

## Index (this phase)

| ID | Title | Status |
|---|---|---|
| DEC-027 | Hosting platform | Proposed |
| DEC-028 | Chroma cold-start strategy | Proposed |
| DEC-029 | Weekly refresh cadence | Proposed |
| DEC-030 | Commit processed JSON | Proposed |
