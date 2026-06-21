# Phase 4 — Streamlit Analytics Dashboard

**Goal:** Render validated analysis artifacts in a four-tab Streamlit app so PMs and
researchers can explore themes, segments, and unmet needs without running the pipeline.

**Architecture reference:** `architecture.md` §5.5, §11 (last-known-good fallback)

---

## Prerequisites

- Phase 3 complete: `themes.json`, `unmet_needs.json`, `segments.json` exist and passed
  validation.
- Phase 1 complete: `normalized_reviews.json` (for trend charts and quote lookup).

---

## Scope

### In scope

- Streamlit app at `src/dashboard/app.py`.
- Four tabs: **Overview**, **Theme Deep-Dive**, **Segments**, **Unmet Needs**.
- Read-only rendering from `data/processed/*.json`.
- Constraint-safe display: ≤250-word theme cards, no PII, inferred segment labels.
- Anomaly-week flags on Overview (from run metadata or computed).

### Out of scope

- Chatbot tab (Phase 5).
- Pipeline re-run triggers (optional nice-to-have; full refresh is Phase 6).
- Editing or mutating analysis artifacts in UI.

---

## Tab specifications

### Tab 1 — Overview

| Element | Source | Notes |
|---|---|---|
| Theme distribution chart | `themes.json` | Count or % per theme |
| Sentiment trend over time | `normalized_reviews.json` + theme assignments | Weekly avg rating or theme volume |
| Anomaly-week flags | `run_metadata.json` or z-score on weekly volume | Visual warning badge |
| Run metadata | `run_metadata.json` | Date, sample size, model id |

### Tab 2 — Theme Deep-Dive

| Element | Source | Notes |
|---|---|---|
| Theme selector | `themes.json` | Dropdown or sidebar |
| Summary card | Stage B output | ≤250 words, enforced at render |
| Supporting quotes | Stage B output | Verbatim, with internal `review_id` only |
| Frequency trend | Theme `review_id`s × dates | Line chart by week |
| Segment breakdown | `segments.json` filtered by theme | Sub-chart |

### Tab 3 — Segments

| Element | Notes |
|---|---|
| Segment distribution | Bar chart by inferred segment |
| Disclaimer banner | **"Inferred from review text, not verified."** — required |
| Per-theme segment cuts | Cross-tab with selected theme |

### Tab 4 — Unmet Needs

| Element | Source |
|---|---|
| Ranked list | `unmet_needs.json` |
| Supporting quotes | Linked by `review_id` |
| Rank badge | 1 = highest frequency/signal |

---

## Suggested module structure

```
src/dashboard/
├── __init__.py
├── app.py              # Streamlit entry, tab layout
├── components/
│   ├── overview.py
│   ├── themes.py
│   ├── segments.py
│   └── unmet_needs.py
├── data_loader.py      # load JSON, last-known-good fallback
└── constants.py        # disclaimer strings, paths
```

---

## UI rules (non-negotiable)

1. **Never render** reviewer usernames, emails, device IDs, or store profile URLs.
2. **Always show** segment disclaimer on Segments tab.
3. **Truncate or block** theme summaries over 250 words (should not happen if Phase 3 validated).
4. **Last-known-good:** if latest artifacts fail validation load, show previous valid snapshot
   with a warning banner (`architecture.md` §11).
5. Cite quotes by internal `review_id` only — not reviewer identity.

---

## Cursor agent prompt

```
Implement Phase 4 — Streamlit Dashboard from @docs/architecture.md section 5.5 and
@docs/phases/phase-4/implementationplan.md.

Create src/dashboard/app.py with four tabs:
1. Overview — theme distribution, sentiment/volume trend, anomaly-week flags, run metadata
2. Theme Deep-Dive — per-theme summary (<=250 words), quotes, frequency trend, segment breakdown
3. Segments — inferred segment cuts with banner "Inferred from review text, not verified."
4. Unmet Needs — ranked list with supporting quotes

Read from data/processed/themes.json, unmet_needs.json, segments.json, normalized_reviews.json,
run_metadata.json.

Rules:
- Never render reviewer-identifying fields
- Enforce 250-word cap on theme narrative cards at display time
- If artifacts are missing or invalid, show last-known-good with warning (if available)

Run entry: streamlit run src/dashboard/app.py
Do not implement the Chatbot tab yet — that is Phase 5.
```

---

## Manual verification

```bash
streamlit run src/dashboard/app.py
```

1. All four tabs load without error.
2. Overview chart shows ≤5 themes.
3. Theme Deep-Dive: select each theme — summary readable, quotes present.
4. Segments tab shows disclaimer prominently.
5. Unmet Needs list is ordered by rank.
6. No PII visible anywhere in UI.
7. Break `themes.json` temporarily — app should warn and fall back if last-known-good exists.

---

## Exit criteria

- [ ] `streamlit run src/dashboard/app.py` launches locally.
- [ ] Four tabs functional with real Phase 3 data.
- [ ] Theme summaries ≤ 250 words in UI.
- [ ] Segment disclaimer visible on Segments tab.
- [ ] No reviewer-identifying fields rendered.
- [ ] Charts render for theme distribution and at least one trend view.
- [ ] Graceful handling when artifact files are missing (clear error, not crash).

---

## After this phase

1. Complete [eval.md](eval.md) — tab smoke tests, privacy/failure-mode tests, sign-off.
2. Accept decisions in [decision.md](decision.md) (charts, last-known-good, disclaimer copy).
3. Commit dashboard code.
4. Proceed to [Phase 5](../phase-5/implementationplan.md) only if eval **Pass**.

---

## Common pitfalls

- Pulling quotes from LLM memory instead of JSON artifacts — always render from persisted files.
- Omitting the segment disclaimer — required by spec.
- Using star rating alone for sentiment charts — complement with text-derived theme volume.
