# Problem Statement: AI-Powered Review Discovery Engine — Spotify

## 1. Overview

Before proposing any product solution, build an AI-powered system that analyzes real user
feedback at scale to understand music **discovery** and **recommendation** pain points on
Spotify (Android).

This build is scoped to **Google Play Store reviews** for the Spotify app. The system
ingests reviews, clusters them into themes, surfaces grounded user quotes, and — instead of
routing the synthesis into a static doc/email via MCP — surfaces everything through:

1. An **interactive analytics dashboard** (themes, trends, segments, unmet needs).
2. An **embedded conversational chatbot**, powered by **Groq**, that lets a PM/researcher
   ask free-form questions (*"why do users churn after the free trial?"*) and get answers
   grounded in actual review text (RAG), with citations back to source reviews.

There is no Gmail/Docs MCP integration in this build — the dashboard *is* the delivery
surface.

## 2. Core Research Questions

The system must be able to help answer:

- Why do users struggle to discover new music?
- What are the most common frustrations with recommendations?
- What listening behaviors are users trying to achieve?
- What causes users to repeatedly listen to the same content (recommendation fatigue /
  "stuck in a loop")?
- Which user segments experience different discovery challenges?
- What unmet needs emerge consistently across reviews?

These questions drive both the theme taxonomy (Section 5) and the chatbot's grounding
strategy (see `architecture.md`, Phase 5).

## 3. Who This Helps

| Audience | Why |
|---|---|
| Product / Growth | Prioritize discovery & recommendation fixes from real signal, not anecdote |
| Design / UX Research | Source verbatim language users use to describe friction |
| Leadership | Ask ad-hoc questions against the corpus instead of waiting on a new analysis |
| Data / Insights teams | Reusable pipeline pattern for any future review corpus |

## 4. End-to-End Flow ("done" looks like)

1. Pull recent Play Store reviews for Spotify (public export/scrape — no login bypass).
2. Normalize, dedupe, language-filter, and store reviews.
3. Embed reviews and build a vector index (for RAG).
4. Run theme discovery + segment + unmet-needs analysis via Groq.
5. Render everything in a Streamlit dashboard: themes, trends, quotes, segments, unmet
   needs.
6. Expose a chatbot inside the same dashboard that retrieves relevant reviews and answers
   questions via Groq, with citations.

## 5. What You Must Build

1. **Ingestion** — Pull ~8–12 weeks (configurable) of Spotify Play Store reviews: rating,
   title/text, date, app version, thumbs-up count (whatever the export provides).
2. **Normalization** — Clean text, drop emoji-only/very short reviews, keep English only
   (or flag language), dedupe near-identical reviews.
3. **Embedding + Vector Store** — Embed normalized reviews locally (no Groq quota spent on
   embeddings) and persist to a vector store.
4. **Theme discovery** — Cluster reviews into **max 5 themes** relevant to
   discovery/recommendations (e.g. *Discover Weekly fatigue, algorithm repetition,
   genre/mood gaps, search & browse friction, personalization onboarding*).
5. **Segment view** — Approximate user segments from review signal (rating tier,
   free/premium mentions, tenure language, device/version) — see Section 8 for limitations.
6. **Unmet needs extraction** — Distill recurring "I wish / I want / why can't" statements
   into a ranked list.
7. **Dashboard** — Streamlit app with theme breakdown, trend-over-time, representative
   quotes, segment cuts, unmet-needs list.
8. **Chatbot** — RAG-grounded Q&A widget inside the dashboard, using Groq for generation,
   with citations to source `review_id`s, and a refusal / "not enough signal" behavior when
   retrieval is empty.
9. **No PII** in any artifact — no usernames, device IDs, or emails.

## 6. Integrations

- **LLM**: Groq (`llama-3.3-70b-versatile` or current equivalent) for theme discovery,
  summarization, unmet-needs synthesis, and chatbot generation.
- **Embeddings**: a local/open embedding model (e.g.
  `sentence-transformers/all-MiniLM-L6-v2`) — kept entirely off Groq's quota.
- **Vector store**: Chroma (local, file-persisted) — swappable later for a hosted store.
- **Dashboard**: Streamlit (fastest path to ship from Cursor; swappable for Next.js later).
- **No MCP / Gmail / Docs** integration in this build.

## 7. Key Constraints

- **Source**: Public Play Store review export only — no scraping behind login, no
  ToS-violating automation.
- **Themes**: Max 5 themes for clustering.
- **Privacy**: No usernames, emails, device IDs, or other identifying reviewer data in any
  artifact, including chatbot answers and citations (cite by internal `review_id` only).
- **Grounding**: The chatbot answers **only** from retrieved review content — no
  open-domain speculation about Spotify presented as user signal.
- **Quota discipline**: Groq's rate/token limits (RPM/RPD/TPM/TPD) must shape batching —
  see `architecture.md` §9.
- **Scannability**: Each theme's synthesized narrative card ≤ 250 words (charts/quotes are
  separate from this cap).

## 8. Known Limitations / Assumptions (validate during Phase 1)

- Play Store reviews carry no explicit "free vs premium" flag — segmentation is **inferred
  from text**, not ground truth. Treat segment cuts as directional, not authoritative.
- No reviewer demographic data exists — "segments" means *behavioral/text-derived
  clusters*, not personas.
- Review volume and sentiment can be skewed by review-bombing events (outages, price
  changes) — the pipeline should flag anomalous weeks rather than silently blend them into
  evergreen "themes."

## 9. Related Documents

| Document | Role |
|---|---|
| `architecture.md` | System design, phases, edge cases, deployment protocol |
| `cursor_implementation_guide.md` | Step-by-step build sequence + prompts to run in Cursor |
