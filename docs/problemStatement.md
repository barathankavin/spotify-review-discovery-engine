# Problem Statement: AI-Powered Review Discovery Engine — Spotify

## 0. Project Context

### 0.1 What this build is

This is a **product-insights pipeline**, not a feature pitch. Before proposing any Spotify
product change, you must first build an AI-powered system that analyzes **real user
feedback at scale** to understand music **discovery** and **recommendation** pain points on
Spotify (Android).

The corpus is **Google Play Store reviews** for the Spotify app (`com.spotify.music`).
Reviews are public, unstructured, and high-volume — they carry authentic language about
what frustrates users, what they wish existed, and how they describe being "stuck" with
recommendations. The system's job is to turn that raw signal into **actionable, grounded
insights** a PM or researcher can trust and explore interactively.

### 0.2 Why discovery and recommendations

Spotify's core loop depends on helping users find music they'll love without manual effort.
When discovery breaks down — repetitive playlists, irrelevant Discover Weekly picks, poor
genre/mood coverage, confusing browse/search — users churn, downgrade, or stop exploring.
Play Store reviews are one of the few places users describe these failures in their own
words, often months before those themes show up in structured analytics.

This build is scoped specifically to **discovery and recommendation friction**, not general
app bugs (crashes, login, billing UI) unless they directly affect how users find or receive
music.

### 0.3 Delivery model (how this differs from the reference milestone)

A reference milestone for this pattern routed synthesized insights into **Gmail/Docs via
MCP** — a static doc or email as the output surface.

**This build replaces that delivery layer entirely.** There is:

- **No Gmail, Google Docs, or MCP integration**
- **No n8n, Apify, Zapier, or other workflow-automation / scraping-as-a-service platform**
  for ingestion — scraping is a plain Python module in the repo, run directly (see
  `architecture.md` §5.1)

Instead, insights are delivered through:

1. An **interactive analytics dashboard** (themes, trends, segments, unmet needs).
2. An **embedded conversational chatbot**, powered by **Groq**, that lets a PM/researcher
   ask free-form questions (*"why do users churn after the free trial?"*) and get answers
   **grounded in actual review text** (RAG), with citations back to source reviews.

The dashboard *is* the delivery surface.

### 0.4 How to use this document

| If you are… | Start here | Then read |
|---|---|---|
| Scoping or reviewing requirements | Sections 0–8 | — |
| Implementing in Cursor | Section 9 + `@docs/problemStatement.md` | `architecture.md`, `cursor_implementation_guide.md` |
| Operating a weekly refresh | Section 7 (flow) + Section 11 (limitations) | `architecture.md` §11–12 |

---

## 1. Overview

Build an end-to-end pipeline that:

1. **Ingests** recent public Play Store reviews for Spotify (Android).
2. **Normalizes** and stores them in a canonical schema (no PII).
3. **Embeds** reviews locally and indexes them in a vector store (for RAG retrieval).
4. **Analyzes** the corpus with Groq to discover themes, extract unmet needs, and infer
   segment cuts — all traceable to `review_id`s.
5. **Validates** LLM output against hard constraints (theme caps, word limits, provenance,
   PII) before anything reaches the UI.
6. **Renders** validated artifacts in a Streamlit dashboard.
7. **Answers** ad-hoc questions via an in-dashboard RAG chatbot grounded only in retrieved
   review excerpts.

---

## 2. Goals and Non-Goals

### 2.1 Goals

| # | Goal |
|---|---|
| G1 | Surface **≤5 discovery/recommendation themes** grounded in real review language |
| G2 | Provide **representative verbatim quotes** and trend views per theme |
| G3 | Extract a **ranked unmet-needs list** from recurring "I wish / I want / why can't" language |
| G4 | Offer **directional segment cuts** (rating tier, free/premium mentions, tenure, version) — clearly labeled as inferred |
| G5 | Enable **interactive Q&A** against the full normalized corpus via RAG + Groq, with citations |
| G6 | Enforce **grounding, privacy, and quota discipline** by design — not as afterthoughts |
| G7 | Ship a **repeatable weekly pipeline** an operator can re-run without manual glue work |

### 2.2 Non-Goals

- Authenticated scraping, headless store browsing, or ToS-violating automation.
- External workflow platforms (n8n, Apify, Zapier) for ingestion or orchestration.
- Gmail/Docs MCP or any external "write" surface for insights.
- Open-ended market-research agent behavior beyond the scoped theme/segment/unmet-needs format.
- Statistically representative user segmentation — segments here are **text-inferred
  heuristics**, not verified personas or demographics.
- General-knowledge answers from the chatbot (e.g. stock price, company strategy) — only
  corpus-grounded responses.

---

## 3. Core Research Questions

The system must help answer:

- Why do users struggle to discover new music?
- What are the most common frustrations with recommendations?
- What listening behaviors are users trying to achieve?
- What causes users to repeatedly listen to the same content (recommendation fatigue /
  "stuck in a loop")?
- Which user segments experience different discovery challenges?
- What unmet needs emerge consistently across reviews?

These questions drive the theme taxonomy (Section 6) and the chatbot's retrieval/grounding
strategy (`architecture.md` §5.6, Phase 5 in `cursor_implementation_guide.md`).

---

## 4. Who This Helps

| Audience | Why |
|---|---|
| Product / Growth | Prioritize discovery & recommendation fixes from real signal, not anecdote |
| Design / UX Research | Source verbatim language users use to describe friction |
| Leadership | Ask ad-hoc questions against the corpus instead of waiting on a new analysis |
| Data / Insights teams | Reusable pipeline pattern for any future review corpus |
| Operator (builder) | Repeatable weekly run, clear validation gates, easy redeploy |

---

## 5. Success Criteria (Definition of Done)

The build is **done** when all of the following hold:

### 5.1 Pipeline

- [ ] Ingestion pulls **8–12 weeks** (configurable) of Spotify Play Store reviews via
  `google-play-scraper` — no login bypass, no external workflow tool.
- [ ] Normalization produces `data/processed/normalized_reviews.json` with the
  `NormalizedReview` schema (see Section 10).
- [ ] Embeddings are stored in a persistent local Chroma collection keyed by `review_id`;
  re-runs upsert only new/changed reviews.
- [ ] Analysis Stages A–D complete with stratified sampling, Groq batching/checkpointing,
  and outputs persisted under `data/processed/`.
- [ ] Validation rejects invalid artifacts; dashboard never renders failed validation output
  as final (last-known-good fallback per `architecture.md` §11).

### 5.2 Dashboard (Streamlit)

- [ ] **Overview** tab: theme distribution, sentiment trend, anomaly-week flags.
- [ ] **Theme Deep-Dive** tab: per-theme summary (≤250 words), quotes, frequency trend.
- [ ] **Segments** tab: inferred cuts, explicitly labeled *"inferred from review text, not
  verified."*
- [ ] **Unmet Needs** tab: ranked list with supporting quotes.
- [ ] **Chatbot** tab: RAG-grounded Q&A with `review_id` citations; refusal when retrieval
  is empty or below similarity threshold.
- [ ] No reviewer-identifying fields (usernames, emails, device IDs) rendered anywhere.

### 5.3 Chatbot quality bar

- [ ] Answers the six core research questions (Section 3) with corpus-grounded responses.
- [ ] Refuses out-of-scope questions (e.g. *"what's Spotify's stock price?"*) with an
  explicit *"not enough signal"* message — no open-domain speculation presented as user
  signal.
- [ ] Every factual claim in an answer cites a retrievable `review_id` whose text supports
  the claim.

### 5.4 Operability

- [ ] `GROQ_API_KEY` loaded from `.env` locally; never committed.
- [ ] App runs via `streamlit run src/dashboard/app.py`.
- [ ] Deployment plan exists for Streamlit Community Cloud (or equivalent) with a strategy
  for ephemeral disk / vector store rebuild (`architecture.md` §12).

---

## 6. End-to-End Flow

```
Play Store public reviews
        │
        ▼
Ingest & normalize ──▶ dedupe, English-only, PII scrub, length filter
        │
        ▼
Embed locally (sentence-transformers) ──▶ upsert into Chroma by review_id
        │
        ▼
Stratified sample (rating tier × ISO week) ──▶ Groq Stages A–D
  • A: theme discovery (≤5 themes)
  • B: per-theme quotes + ≤250-word summary
  • C: unmet-needs extraction (ranked, ~5 max)
  • D: inferred segment heuristics
        │
        ▼
Validate (structure, word limits, provenance, PII)
        │
        ▼
Streamlit dashboard ──▶ Overview / Themes / Segments / Unmet Needs / Chatbot
                              │
                              └──▶ RAG chatbot retrieves from full corpus (not just sample)
```

**Critical ordering rules** (from `architecture.md` §4):

- **Sampling precedes every LLM analysis call** — never send the full normalized corpus to
  Groq for theming.
- **Embedding covers the full normalized corpus** — the chatbot retrieval pool is all
  reviews, not the analysis sample.
- **Validation gates rendering** — invalid LLM output is retried (bounded) or blocked.

---

## 7. What You Must Build

| # | Component | Requirements |
|---|---|---|
| 1 | **Ingestion** | Pull ~8–12 weeks of Spotify Play Store reviews: rating, title/text, date, app version, thumbs-up count. Plain Python + `google-play-scraper`. |
| 2 | **Normalization** | Clean text; drop emoji-only and &lt;6-word reviews; English only (`langdetect`); dedupe near-identical bodies; scrub PII patterns. |
| 3 | **Embedding + vector store** | Local `sentence-transformers/all-MiniLM-L6-v2` (or equivalent); Chroma file-persisted; upsert by `review_id`. **No Groq quota for embeddings.** |
| 4 | **Theme discovery** | Cluster into **≤5 themes** relevant to discovery/recommendations (e.g. *Discover Weekly fatigue, algorithm repetition, genre/mood gaps, search & browse friction, personalization onboarding*). |
| 5 | **Segment view** | Approximate segments from review signal (rating tier, free/premium mentions, tenure language, device/version) — see Section 11. |
| 6 | **Unmet needs extraction** | Distill recurring *"I wish / I want / why can't"* statements into a ranked list (~5 max). |
| 7 | **Validation layer** | Deterministic checks on theme count, word limits, quote provenance, PII — applies to analysis **and** chatbot answers. |
| 8 | **Dashboard** | Streamlit app with five tabs per Section 5.2. |
| 9 | **Chatbot** | RAG-grounded Q&A using Groq for generation; citations to `review_id`s; refusal when retrieval is insufficient. |
| 10 | **Privacy** | No usernames, device IDs, or emails in any artifact, log, or UI field. |

---

## 8. Integrations and Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| **LLM (generation)** | Groq — `llama-3.3-70b-versatile` or current equivalent | Theme discovery, summarization, unmet-needs synthesis, chatbot generation |
| **Embeddings** | Local open model — e.g. `sentence-transformers/all-MiniLM-L6-v2` | Entirely off Groq quota |
| **Vector store** | Chroma (local, file-persisted under `vector_store/`) | Swappable for hosted store later |
| **Ingestion** | `google-play-scraper` in-process Python | No n8n / Apify / Zapier |
| **Dashboard** | Streamlit | Fastest path from Cursor; swappable for Next.js later |
| **Language filter** | `langdetect` or similar | Log dropped non-English count |
| **Secrets** | `GROQ_API_KEY` via `.env` / platform secrets | Never committed |
| **Explicitly excluded** | Gmail, Docs, MCP, n8n, Apify, Zapier | Dashboard is the only output surface |

### Groq quota discipline

Groq rate/token limits (RPM/RPD/TPM/TPD) **must** shape batching, sleep/backoff, and
checkpointing. Verify current limits at `console.groq.com/docs/rate-limits` before locking
batch sizes — `architecture.md` §9 has planning guidance and example figures.

---

## 9. Quality Attributes (prioritized)

These apply to the **entire** system, not just the chatbot:

| Priority | Attribute | Meaning |
|---|---|---|
| 1 | **Grounding** | Theme cards and chatbot answers never assert anything not traceable to a `review_id` |
| 2 | **Constraint safety** | Theme caps (≤5), word limits (≤250w per theme card), PII rules enforced before render |
| 3 | **Quota discipline** | Groq RPM/RPD/TPM/TPD respected by design via sampling + batching + checkpointing |
| 4 | **Reproducibility** | Each run logs sample seed, model id, and prompt version |
| 5 | **Operational simplicity** | Few moving parts: ingest → embed → analyze → validate → render |

**Trust principle:** treat all Groq output as **untrusted** until validators pass. Assume
the LLM can hallucinate structure, over-claim from sparse evidence, or leak PII — validators
enforce zero trust for counts, quotes, citations, and PII in both analysis and chat paths.

---

## 10. Data Artifacts (logical contracts)

| Artifact | Key fields | Produced by | Consumed by |
|---|---|---|---|
| `NormalizedReview` | `review_id`, platform, date, rating, title, body, app_version, thumbs_up | Ingestion | Embedding, analysis, chatbot retrieval |
| `ThemeCluster` | theme id/label, description, supporting `review_id`s | Stage A | Dashboard, Stages B/C |
| `WeeklyPulse` (per theme) | summary (≤250w), quotes, word count | Stage B | Dashboard Theme tab |
| `UnmetNeed` | statement, rank, supporting `review_id`s | Stage C | Dashboard Unmet Needs tab |
| `SegmentTag` | `review_id`, inferred segment, confidence flag | Stage D | Dashboard Segments tab |
| `ChatTurn` | question, retrieved `review_id`s, answer, citations | Chatbot | Chatbot UI, logs |

Persisted files (typical paths):

- `data/processed/normalized_reviews.json`
- `data/processed/themes.json`
- `data/processed/unmet_needs.json`
- `data/processed/segments.json`
- `vector_store/` (Chroma persistence)

---

## 11. Key Constraints

- **Source**: Public Play Store review export only — no scraping behind login, no
  ToS-violating automation.
- **Scope filter**: Prioritize discovery/recommendation topics; off-topic reviews route to an
  "Other" bucket excluded from headline themes (`architecture.md` §10 #7).
- **Themes**: Maximum **5** themes for clustering.
- **Summaries**: Each theme's synthesized narrative card ≤ **250 words** (charts/quotes
  excluded from this cap).
- **Privacy**: No usernames, emails, device IDs, or other identifying reviewer data in any
  artifact — cite by internal `review_id` only.
- **Grounding**: Chatbot answers **only** from retrieved review content — no open-domain
  speculation about Spotify presented as user signal.
- **Segments**: Always labeled **inferred, not verified** in the UI.
- **Anomaly weeks**: Flag review-bombing / outage spikes rather than silently blending them
  into evergreen themes.

---

## 12. Known Limitations and Assumptions

Validate these during Phase 1 (ingestion) before trusting downstream analysis:

- Play Store reviews carry **no explicit "free vs premium" flag** — segmentation is inferred
  from text, not ground truth. Treat segment cuts as **directional**, not authoritative.
- **No reviewer demographic data** exists — "segments" means behavioral/text-derived
  clusters, not personas.
- Review volume and sentiment can be **skewed by review-bombing** (outages, price changes) —
  the pipeline should flag anomalous weeks.
- **Star rating vs. text sentiment can mismatch** (e.g. 5★ with a complaint) — theme from
  text content, not rating alone.
- Play Store exports may have **malformed rows or encoding issues** — parser should tolerate
  and log skips rather than crash.
- Groq free-tier limits are **account- and model-specific** and change over time — batch
  sizes in `architecture.md` §9 are planning examples, not guarantees.

---

## 13. Implementation Phases (summary)

Master index: [`docs/implementationplan.md`](implementationplan.md). Each phase has a
detailed plan under `docs/phases/phase-N/implementationplan.md`.

| Phase | Plan | Deliverable |
|---|---|---|
| 0 | [phase-0/implementationplan.md](phases/phase-0/implementationplan.md) | Repo scaffold, `.env.example`, docs in `docs/` |
| 1 | [phase-1/implementationplan.md](phases/phase-1/implementationplan.md) | Ingestion & normalization → `normalized_reviews.json` |
| 2 | [phase-2/implementationplan.md](phases/phase-2/implementationplan.md) | Embedding & Chroma vector store + retrieval sanity check |
| 3 | [phase-3/implementationplan.md](phases/phase-3/implementationplan.md) | Groq analysis Stages A–D → `themes.json`, `unmet_needs.json`, `segments.json` |
| 4 | [phase-4/implementationplan.md](phases/phase-4/implementationplan.md) | Streamlit dashboard (Overview, Themes, Segments, Unmet Needs) |
| 5 | [phase-5/implementationplan.md](phases/phase-5/implementationplan.md) | RAG chatbot tab |
| 6 | [phase-6/implementationplan.md](phases/phase-6/implementationplan.md) | Deployment plan + Streamlit Community Cloud smoke test |
| Recurring | — | Weekly re-run of Phases 1–3; preserve last-known-good artifacts on validation failure |

After each phase:

1. Fill in `docs/phases/phase-N/eval.md` — run all tests, check exit criteria, sign off Pass/Fail.
2. Record tech/business forks in `docs/phases/phase-N/decision.md`; index accepted entries in `docs/decision.md`.

Every Cursor implementation prompt should anchor to `@docs/problemStatement.md`,
`@docs/architecture.md`, and `@docs/phases/phase-N/implementationplan.md`.

---

## 14. Related Documents

| Document | Role |
|---|---|
| `implementationplan.md` | Master phase index, dependency graph, global build rules |
| `phases/phase-N/implementationplan.md` | Per-phase scope, steps, Cursor prompts |
| `phases/phase-N/eval.md` | Per-phase test procedures and exit criteria sign-off |
| `phases/phase-N/decision.md` | Per-phase tech/business decisions |
| `decision.md` | Master decision log (DEC-001…); cross-cutting ADRs |
| `architecture.md` | System design, component specs, edge cases (§10), Groq quota planning (§9), deployment protocol (§12), failure/retry philosophy (§11) |
| `../cursor_implementation_guide.md` | Quick-reference copy-paste prompts (repo root) |

---

## 15. Example Theme Taxonomy (starting point, not prescriptive)

Themes are **discovered from data** in Stage A, not hard-coded. These examples illustrate
the discovery/recommendation scope:

1. **Discover Weekly / playlist fatigue** — same songs, stale picks, doesn't refresh
2. **Algorithm repetition / "stuck in a loop"** — hears the same artists constantly
3. **Genre, mood, or context gaps** — can't find music for a mood, activity, or niche genre
4. **Search and browse friction** — hard to explore beyond home feed recommendations
5. **Personalization and onboarding** — taste profile doesn't improve, cold-start problems

Final theme labels and count (≤5) must emerge from the sampled corpus and pass validation.
