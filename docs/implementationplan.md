# Implementation Plan: Spotify Review Discovery Engine (AI Agent)

This document is the **master index** for building the AI-powered review discovery engine
phase by phase in Cursor. Each phase has its own detailed plan under `docs/phases/`.

## What you are building

An end-to-end **AI agent pipeline** that:

1. Ingests public Spotify Play Store reviews (plain Python — no n8n/Apify/MCP).
2. Normalizes, embeds, and indexes them for semantic retrieval.
3. Runs Groq-powered analysis (themes, unmet needs, inferred segments) with validation.
4. Renders insights in a Streamlit dashboard.
5. Answers ad-hoc questions via an embedded RAG chatbot grounded in review text.

The dashboard is the delivery surface — not Gmail, Docs, or any external write integration.

## Required reading (agent context)

Anchor every Cursor prompt to these files:

| Document | Path |
|---|---|
| Problem statement | `@docs/problemStatement.md` |
| System architecture | `@docs/architecture.md` |
| This plan (current phase) | `@docs/phases/phase-N/implementationplan.md` |
| Phase evaluation (fill after build) | `@docs/phases/phase-N/eval.md` |
| Phase decisions | `@docs/phases/phase-N/decision.md` + `@docs/decision.md` |
| Decision log (master index) | `@docs/decision.md` |

Optional quick-reference: `cursor_implementation_guide.md` at repo root (copy-paste prompts).

## Phase map

| Phase | Name | Plan | Eval | Decisions | Primary output |
|---|---|---|---|---|---|
| **0** | Repo scaffold | [plan](phases/phase-0/implementationplan.md) | [eval](phases/phase-0/eval.md) | [decisions](phases/phase-0/decision.md) | Project skeleton, docs |
| **1** | Ingestion | [plan](phases/phase-1/implementationplan.md) | [eval](phases/phase-1/eval.md) | [decisions](phases/phase-1/decision.md) | `normalized_reviews.json` |
| **2** | Embedding | [plan](phases/phase-2/implementationplan.md) | [eval](phases/phase-2/eval.md) | [decisions](phases/phase-2/decision.md) | Chroma + retrieval CLI |
| **3** | Analysis | [plan](phases/phase-3/implementationplan.md) | [eval](phases/phase-3/eval.md) | [decisions](phases/phase-3/decision.md) | `themes.json`, etc. |
| **4** | Dashboard | [plan](phases/phase-4/implementationplan.md) | [eval](phases/phase-4/eval.md) | [decisions](phases/phase-4/decision.md) | Four analytics tabs |
| **5** | Chatbot | [plan](phases/phase-5/implementationplan.md) | [eval](phases/phase-5/eval.md) | [decisions](phases/phase-5/decision.md) | RAG Chatbot tab |
| **6** | Deployment | [plan](phases/phase-6/implementationplan.md) | [eval](phases/phase-6/eval.md) | [decisions](phases/phase-6/decision.md) | Live URL, deployment plan |

**Recurring (post Phase 6):** Re-run Phases 1→3 weekly; preserve last-known-good artifacts
on validation failure (`architecture.md` §11).

## Dependency graph

```
Phase 0 (scaffold)
    │
    ▼
Phase 1 (ingest) ──▶ Phase 2 (embed) ──▶ Phase 3 (analyze)
                              │                  │
                              │                  ▼
                              └──────────▶ Phase 4 (dashboard)
                                              │
                                              ▼
                                         Phase 5 (chatbot)
                                              │
                                              ▼
                                         Phase 6 (deploy)
```

- Phases 1→2→3 are sequential pipeline stages.
- Phase 4 needs Phase 3 artifacts; Phase 5 needs Phases 2 and 4.
- Phase 6 wraps the full stack.

## How to run a phase in Cursor

1. Open the phase plan: `@docs/phases/phase-N/implementationplan.md`.
2. Confirm the **prior phase `eval.md`** is signed off Pass (or note blockers).
3. Record any new forks in `@docs/phases/phase-N/decision.md`; link accepted entries in
   `@docs/decision.md`.
4. Paste the **Cursor agent prompt** from the plan (or `cursor_implementation_guide.md`).
5. Implement and run the **tests** listed in `@docs/phases/phase-N/eval.md`.
6. Fill in `eval.md`: check every test row and exit criterion; set **Pass / Fail** and sign-off.
7. Commit when eval is Pass — do not wait until the end of the build.

## Evaluation and decision files

Each phase folder contains three docs:

| File | Purpose | When |
|---|---|---|
| `implementationplan.md` | What to build, agent prompt, scope | Before/during implementation |
| `eval.md` | Test procedures, metrics tables, exit criteria sign-off | After implementation |
| `decision.md` | Tech/business choices for that phase | Any time a fork affects the build |

**`docs/decision.md`** is the master decision log (DEC-001…). It holds cross-cutting
baseline decisions plus an index of all phase entries. When a decision is **Accepted**,
add its row to the master index.

## Model assignment (recommended)

| Task type | Cursor model |
|---|---|
| Architecture, quota planning, edge-case review | Frontier reasoning model |
| Implementation (Python, Streamlit, RAG wiring) | Sonnet-class agent model |
| Test runs, lint fixes, commits | Fastest/cheapest model |

## Global rules (every phase)

- **No scope creep:** no Gmail/Docs MCP, n8n, Apify, Zapier, or authenticated scraping.
- **Grounding:** every insight traceable to `review_id`; LLM output is untrusted until validated.
- **Privacy:** no reviewer usernames, emails, or device IDs in artifacts or UI.
- **Quota:** Groq used only for generation; embeddings stay local. Verify limits at
  `console.groq.com/docs/rate-limits` before Phase 3.
- **Sampling before LLM:** analysis uses a stratified sample; chatbot retrieval uses the
  **full** normalized corpus.

## Definition of done (full build)

See `@docs/problemStatement.md` §5. All seven phase exit criteria must pass, plus a live
smoke test on Streamlit Community Cloud (Phase 6).
