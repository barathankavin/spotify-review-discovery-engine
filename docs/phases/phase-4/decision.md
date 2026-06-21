# Phase 4 Decisions — Streamlit Dashboard

---

## Decisions

### DEC-020 — Charting library

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | |
| **Category** | Tech |

**Context:** Overview and theme tabs need distribution and trend charts.

**Decision:** _e.g. Streamlit native charts / Altair / Plotly_

**Alternatives considered:** matplotlib only; external BI embed.

**Consequences:** Adds optional dependency; affects deploy `requirements.txt`.

---

### DEC-021 — Last-known-good artifact paths

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | |
| **Category** | Ops |

**Context:** Failed Phase 3 run must not blank the dashboard (`architecture.md` §11).

**Decision:** _e.g. `data/processed/last_good/themes.json` or dated subdirs_

**Alternatives considered:** Git revert only; no fallback.

**Consequences:** Phase 3 promote step copies to last_good on validation pass.

---

### DEC-022 — Segment disclaimer copy (exact UI text)

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | |
| **Category** | Business |

**Context:** Legal/PM clarity on inferred segments.

**Decision:** _"Inferred from review text, not verified."_

**Alternatives considered:** Longer footnote with methodology link.

**Consequences:** Same string reused in Phase 5 if segments mentioned in chat.

---

## Index (this phase)

| ID | Title | Status |
|---|---|---|
| DEC-020 | Charting library | Proposed |
| DEC-021 | Last-known-good paths | Proposed |
| DEC-022 | Segment disclaimer copy | Proposed |
