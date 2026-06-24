# Architecture: Spotify Review Discovery Engine (Dashboard + Groq RAG Chatbot)

This document describes how an AI-powered pipeline turns Spotify Play Store reviews into
(a) an analytics dashboard and (b) a grounded conversational chatbot, per
`problemStatement.md`. It replaces the Docs/Gmail-MCP delivery layer from the reference
milestone with a self-hosted Streamlit surface.

## 1. Purpose and Scope

### 1.1 What this system does
1. Ingests recent, public Play Store review exports for Spotify (Android).
2. Synthesizes themes, segment cuts, and unmet needs grounded in real review language.
3. Renders all of the above in an interactive Streamlit dashboard.
4. Answers free-form questions about the corpus via a retrieval-augmented chatbot backed
   by Groq, with citations to source reviews.

### 1.2 Explicit non-goals
- No authenticated scraping, headless store browsing, or gray-area automation against
  storefronts.
- No n8n, Apify, Zapier, or any other workflow-automation / scraping-as-a-service platform
  for ingestion. Matching the reference milestone's "non-MCP" ingestion pattern, scraping
  is a plain Python module in this repo, run by Cursor — not an external low-code workflow
  or a hosted scraping job.
- No Gmail/Docs MCP delivery — the dashboard is the consumption surface.
- No open-ended "market research agent" beyond the scoped theme/segment/unmet-needs
  format (caps on themes, quotes, words).
- No claim of statistically representative segmentation — segments here are
  text-inferred heuristics, clearly labeled as such in the UI.

### 1.3 Quality attributes (prioritized)

| Priority | Attribute | Meaning here |
|---|---|---|
| 1 | Grounding | Chatbot and theme cards never assert anything not traceable to a `review_id` |
| 2 | Constraint safety | Theme caps, word limits, PII rules enforced before render |
| 3 | Quota discipline | Groq RPM/RPD/TPM/TPD respected by design, not by luck |
| 4 | Reproducibility | A run's sample seed, model id, and prompt version are logged |
| 5 | Operational simplicity | Few moving parts: ingest → embed → analyze → validate → render |

## 2. Stakeholders and Consumers

| Role | Interest |
|---|---|
| Product / Growth | Prioritized themes + quotes to justify discovery/recommendation bets |
| UX Research | Verbatim language, ability to interrogate the corpus ad hoc |
| Leadership | One dashboard screen of signal, plus a chatbot for follow-up questions |
| Operator (you) | Repeatable weekly run, clear validation gates, easy redeploy |

## 3. Context Diagram (external actors)

```
External systems                         Your pipeline
─────────────────                         ─────────────
Play Store public review pages   ──────▶  Ingestion & Normalization
                                                 │
Local embeddings (MiniLM)        ◀──────  Embedding (Phase 2)
  (all-MiniLM-L6-v2, 384-dim)                    │
                                                 ▼
                                           Chroma vector store
                                                 │
Groq LLM API (chat completions)  ◀──────  Stage A/B/C/D analysis
                                                 │
                                           Validation layer
                                                 │
                                           Streamlit Dashboard ──▶ Operator/PM (browser)
                                                 │
Groq LLM API (chat completions)  ◀──────  RAG Chatbot tab
Local embeddings (MiniLM)        ◀──────  (query embedding, same model as Phase 2)
```

Embeddings run **locally** with `sentence-transformers/all-MiniLM-L6-v2` (Phase 2 indexing +
Phase 5 query encoding) — see DEC-003a, which superseded the original Groq-embeddings plan
(DEC-003). Your orchestration talks to **Groq** only for chat completions (Phase 5 chatbot
generation, and optional Phase 3 analysis), and to a local Chroma vector store for similarity
search. There is no external write surface (no Docs/Gmail) — the dashboard *is* the output.

## 4. High-Level Pipeline

```
Inputs
  Play Store export
      │
      ▼
Ingest & normalize ──▶ Dedupe / language filter / PII scrub
      │
      ▼
Embed (local MiniLM) ──▶ Upsert into Chroma (keyed by review_id)
      │
      ▼
Stratified sample (rating tier × week)
      │
      ▼
Stage A: theme discovery (Groq, ≤5 themes)
      │
      ▼
Stage B: per-theme quotes + summary (Groq)
      │
      ▼
Stage C: unmet-needs extraction (Groq)
      │
      ▼
Stage D: segment heuristics (rule-based + Groq tag-along)
      │
      ▼
Validate constraints (counts, word limits, provenance, PII)
      │
      ▼
Render: Streamlit dashboard (Overview / Themes / Segments / Unmet Needs / Chatbot)
```

**Ordering rules**
- Sampling precedes every LLM call — never send the full normalized corpus directly.
- Embedding happens once per review (upsert by id), independent of the sampling used for
  theme analysis — the chatbot's retrieval pool is the *full* normalized corpus, not the
  sample.
- Validation gates rendering. If validation fails, the dashboard must not present a stage's
  output as final (a "last known good" artifact is shown instead — see §11).

## 5. Logical Components

### 5.1 Review ingestion (non-MCP)
**Responsibility**: Turn the Play Store export into a canonical representation.

**Tooling decision**: implemented as a single Python module (`src/ingestion/`) authored
and run directly by the Cursor agent — calling a permitted public library
(`google-play-scraper`) in-process. No n8n, Apify, Zapier, or any other workflow-automation
/ scraping-as-a-service platform is involved. Rationale: keeps the entire pipeline in one
codebase with one set of dependencies, avoids a second platform to authenticate against or
pay for, and mirrors the reference architecture's explicit "non-MCP" labeling for this
stage — ingestion is plumbing, not an integration surface.

**Inputs**: Files/records produced by that script pulling from the public reviews
endpoint — no login, no ToS-violating automation.

**Processing concepts**:
- *Parsing*: tolerate missing optional fields, encoding issues.
- *Normalization*: shared schema — `review_id, platform, date, rating, title, body,
  app_version, thumbs_up`.
- *Time windowing*: retain only the configured 8–12 week lookback.
- *Language filter*: keep English only (`langdetect`/`fasttext`); log how many were
  dropped and why.
- *Length filter*: drop reviews under ~6 words and emoji-only bodies.
- *Deduping*: collapse duplicates (same body + close timestamp).
- *PII scrubbing*: regex pass for emails/phone numbers/handles accidentally pasted into
  review bodies, even though the source is "public."

**Output**: `data/processed/normalized_reviews.json` — consumed by embedding and analysis.

**Failure modes**: unreadable export → actionable error; partial export → ingest what's
valid, surface a warning with row counts.

### 5.2 Embedding & vector store
**Responsibility**: Make every normalized review retrievable by meaning, for the chatbot.

- **Embedding provider**: **local** `sentence-transformers` (CPU), via `LocalEmbedder`
  (`EMBEDDING_BACKEND=local`). See DEC-003a — this superseded the original Groq-embeddings
  plan. A `GroqEmbedder` backend still exists in the code but is not the default.
- **Embedding model**: `sentence-transformers/all-MiniLM-L6-v2` (384-dim). The same local
  model is used for Phase 2 corpus indexing **and** Phase 5 chatbot query embedding.
- **Auth**: no key needed for embeddings (local). `HF_TOKEN` is optional (quiet model
  downloads). `GROQ_API_KEY` is required only for generation (Phase 5 chat / optional Phase 3).
- **Batching**: embed reviews in local batches (`EMBED_BATCH_SIZE`, default 128); checkpoint
  progress so an interrupted run resumes instead of restarting.
- **Store**: Chroma, file-persisted under `vector_store/` (committed for fast deploys).
- **Upsert keyed by `review_id`** so re-running ingestion only embeds new/changed reviews
  (no full rebuild each week). Skip unchanged bodies via content-hash metadata.
- **Document text**: `title + body` concatenation (title often empty for Play Store).
- This pool feeds **both** the chatbot's retrieval and, optionally, the Stage A/B sampling
  (sampling still draws from the full normalized set, embeddings are just a side index).

**Quota note**: embeddings consume **no API tokens** (they run locally on CPU). Only the
Groq chat-completion quota (§9) matters, and it's reserved for the RAG chat.

### 5.3 Analysis (LLM-centric, Groq)
**Responsibility**: Transform normalized reviews into theming, summaries, unmet needs, and
segment tags.

**Pre-LLM sampling**: stratified by rating tier (negative ≤2★, neutral 3★, positive 4–5★)
× ISO week, oversampling negative reviews (carry the actionable signal), capped per
tier-week so no single week dominates. Seed + caps logged in run metadata.

**Stage sequence**:
1. **Stage A — Theme discovery** (Groq): sample → JSON list of ≤5 themes, each with a
   label, one-line description, and supporting `review_id`s.
2. **Stage B — Quotes + summary**: per theme, pull verbatim supporting quotes and a short
   (≤250-word) narrative.
3. **Stage C — Unmet needs**: scan for "I wish / I want / why can't" language across the
   sample, cluster into a ranked list (max ~5 unmet needs), each with supporting
   `review_id`s.
4. **Stage D — Segment heuristics**: rule-based tagging first (rating tier, version,
   keyword hits for "premium"/"free trial"/"ads"), then an optional Groq pass to label
   each cluster's dominant segment language — always rendered as **"inferred"**.

A bounded repair retry is permitted at any stage if validation rejects the output (e.g.
quote provenance fails, theme count > 5, word count over limit).

### 5.4 Validation layer (deterministic)
**Responsibility**: Contract enforcer between creative LLM output and the dashboard/chatbot.

Checks:
- **Structural**: theme count ≤5, quotes/actions counts match spec.
- **Length**: each theme card ≤250 words under a fixed counting policy.
- **Provenance**: every quote/cited `review_id` traces to the normalized corpus
  (substring or normalized-whitespace match).
- **PII**: block patterns for emails, phone numbers, handles in any rendered artifact —
  including chatbot answers, not just analysis output.

Output: accept (hand off to dashboard/chat) or reject with reasons for retry/operator
review.

### 5.5 Dashboard (Streamlit)
**Responsibility**: Render validated artifacts for human consumption.

Tabs:
- **Overview** — theme distribution, sentiment trend over time, anomaly-week flags.
- **Theme Deep-Dive** — per theme: summary card (≤250 words), supporting quotes,
  frequency trend, segment breakdown.
- **Segments** — inferred segment cuts per theme, explicitly labeled "inferred from review
  text, not verified."
- **Unmet Needs** — ranked list with supporting quotes.
- **Chatbot** — see 5.6.

### 5.6 RAG Chatbot
**Responsibility**: Answer free-form questions grounded only in the review corpus.

Flow:
1. Embed the user's question with the configured embedding model (local MiniLM by default,
   same model family used in Phase 2).
2. Pull a candidate pool of `RAG_FETCH_K` (default 40) most similar reviews from Chroma,
   then re-select `RAG_TOP_K` (default 12, capped ≤13 for the context budget) using
   **Maximal Marginal Relevance (MMR, `RAG_MMR_LAMBDA=0.7`)**. MMR balances query relevance
   against inter-result diversity, so the LLM sees a broader, less duplicative evidence set
   instead of several near-identical reviews. MMR falls back to plain similarity order if
   candidate embeddings are unavailable.
3. If max similarity is below a configured threshold → return "not enough signal in the
   reviews to answer that" instead of calling Groq.
4. Otherwise, call Groq with a system prompt restricting it to the retrieved excerpts only,
   requiring a `review_id` citation for every claim.
5. Run the answer through the same PII/provenance validators as analysis output before
   rendering. The UI emphasises the insight text and renders `[review_id: …]` citations as
   compact, de-emphasised id pills.

**In-app "Refresh pipeline" button**: always clears the artifact cache and reloads the
latest processed artifacts from disk. When `GH_DISPATCH_TOKEN` + `GH_REPO` are configured
(via `.env` or platform Secrets), the button additionally fires a `workflow_dispatch` for
the `weekly-refresh.yml` GitHub Actions workflow over the REST API, re-running the pipeline
remotely; the committed artifacts then auto-deploy. Without those secrets it degrades
gracefully to the local reload only.

### 5.7 Orchestration, configuration, observability
- **Configuration** (non-secret): lookback weeks, sample caps, theme limit, similarity
  threshold, embedding batch size, retry counts.
- **Secrets**: `GROQ_API_KEY` via `.env` locally / platform secrets in deployment — never
  committed. Used for embeddings (Phase 2), analysis (Phase 3), and chat (Phase 5).
- **Observability** (minimum viable): run id, ingest counts, validation outcomes, Groq
  embedding + chat call counts/latency/errors, vector store size, chatbot query log
  (questions + retrieved ids only — no PII, no full answer text needed for logs).

## 6. Trust Boundaries and Privacy

| Boundary | Inside | Must not leak outward |
|---|---|---|
| Export → Normalization | Raw export rows | Unredacted reviewer identifiers into logs |
| Normalization → Embedding/Analysis | Review text needed for theming | Fields you promised to strip |
| LLM (Groq) → Validators | Draft theme/quote/answer | Treat as untrusted until validated |
| Validators → Dashboard/Chat UI | Validated content only | Anything that failed validation |

**Principle**: assume the LLM can hallucinate structure or over-claim from sparse
evidence; validators assume zero trust for counts, quotes, citations, and PII — in both the
analysis pipeline *and* the chatbot.

## 7. Data Contracts (logical model)

| Artifact | Carries | Consumers |
|---|---|---|
| `NormalizedReview` | `review_id`, platform, date, rating, title, body, app_version | Embedding, analysis, chatbot retrieval |
| `ThemeCluster` | theme id/label, description, supporting `review_id`s | Dashboard, Stage B/C |
| `WeeklyPulse` (per theme) | summary (≤250w), 3 quotes, word count | Dashboard |
| `UnmetNeed` | statement, rank, supporting `review_id`s | Dashboard |
| `SegmentTag` | review_id, inferred segment, confidence flag | Dashboard segment cuts |
| `ChatTurn` | question, retrieved `review_id`s, answer, citations | Chatbot UI, logs |

Versioning: when any artifact shape changes, bump an internal schema version and note the
change in this document's changelog (or a `decision.md` if you choose to keep one).

## 8. Sequence: Happy Path

```
Operator → Orchestrator: start weekly run
Orchestrator → Ingestion: load export
Ingestion → Orchestrator: normalized reviews
Orchestrator → Embedding: upsert by review_id (local MiniLM embeddings)
Orchestrator → Sampler: stratified sample (rating × week)
Sampler → Groq: Stage A theme discovery
Groq → Orchestrator: ThemeCluster[]
Orchestrator → Groq: Stage B quotes + summary, Stage C unmet needs, Stage D segments
Groq → Validators: candidate artifacts
alt valid:
  Validators → Dashboard: accepted artifacts → render
alt invalid:
  Validators → Orchestrator: errors → bounded repair retry → re-validate
Operator → Chatbot tab: ask question
Chatbot → LocalEmbedder: embed question (same MiniLM model as Phase 2)
Chatbot → VectorStore: retrieve top-k
Chatbot → Groq: grounded generation (or skip if low similarity)
Chatbot → Validators: citation/PII check
Chatbot → Operator: answer with citations
```

## 9. Groq Quota Planning

**Confirmed limits** for `llama-3.3-70b-versatile` (operator account, 2026-06-21):

| Limit | Value |
|---|---|
| Requests per minute (RPM) | **30** |
| Requests per day (RPD) | **1,000** |
| Tokens per minute (TPM) | **12,000** |
| Tokens per day (TPD) | **100,000** |

Re-verify at `console.groq.com/docs/rate-limits` if limits change.

### Chat completions (Phases 3 & 5) — locked budget

**Binding constraint:** **100K TPD**, not RPD. A naïve plan (900-review sample × Stage A +
Stage C batched) can exceed **~170K tokens** in one run. Use the budget below instead.

#### Per-call estimates (20 reviews per batch)

| Component | Tokens (typical) |
|---|---|
| System + instruction overhead | ~300–500 |
| 20 review bodies (median ~18 words each) | ~400–700 |
| Stage A output (theme JSON) | ~400–800 |
| Stage B output (summary + quotes) | ~600–1,000 |
| **Total per Stage A/C batch call** | **~1,400–1,800** |
| **Total per Stage B call (one theme)** | **~1,500–2,500** |

#### Recommended Phase 3 run (fits one day on free tier)

| Stage | Input | Batch / calls | Est. tokens |
|---|---|---|---|
| **A** Theme discovery | **450** reviews (stratified) | 20/batch → **23 calls** | ~37K |
| **B** Summaries + quotes | 5 themes | **5 calls** (1/theme) | ~10K |
| **C** Unmet needs | **300** discovery-scoped reviews* | 20/batch → **15 calls** | ~24K |
| **D** Segments | rules-first | **0–1** Groq calls | ~0–2K |
| **Chatbot reserve** | interactive Q&A | — | **~15–20K** |
| **Total** | | **~43–44 calls** | **~86–93K** |

\*Stage C uses the discovery_candidate subset from the same stratified sample — not a
second full pass over 450 unrelated reviews.

**Do not exceed ~500 reviews** in Stage A on this tier. Prior `~900` sample guidance is
too large when both Stage A and Stage C batch the full set.

#### Rate pacing

| Limit | Rule | Implementation |
|---|---|---|
| **RPM (30)** | ≥ **2.1 s** sleep between chat completion calls | `time.sleep(2.5)` default |
| **TPM (12K)** | ~**6–7** max calls/min at 1,800 tokens/call | If 429 TPM, backoff to **10 s** |
| **RPD (1K)** | ~44 calls/run leaves headroom | Log call count in `run_metadata.json` |
| **TPD (100K)** | Stop analysis run if logged tokens **> 80K**; reserve rest for chat | Checkpoint + operator warning |

Always **checkpoint after each batch** so a mid-run 429 resumes instead of restarting.

### Embeddings (Phase 2 & 5 query encoding)

Model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim), run **locally on CPU** (DEC-003a).
**No API rate limits or tokens** apply — embeddings are free and offline.

Given ~27k normalized reviews:
- Local batches of `EMBED_BATCH_SIZE` (default 128) → ~213 batches; first full index ~225s
  on a dev CPU.
- Embeddings do **not** touch the Groq chat TPD cap — the full Groq budget is for chat.
- Weekly refresh: hash-skip unchanged reviews so only the new delta is embedded.

### Shared discipline (all Groq calls)

- Log `model_id`, prompt version, call count, and estimated tokens per run.
- Never silently switch models or API keys without logging it.
- Chatbot and batch analysis share **the same** chat TPD — run Phase 3 during off-hours
  or accept fewer chat queries on analysis days.

## 10. Edge Cases

| # | Edge case | Handling |
|---|---|---|
| 1 | Non-English / mixed-language reviews | Language-detect, keep English only, log dropped count |
| 2 | Emoji-only or very short (<6 word) reviews | Drop at normalization, per length filter |
| 3 | Duplicate/copy-paste spam reviews | Hash + fuzzy-match dedupe before sampling |
| 4 | Review-bombing / anomaly weeks (outage, price hike) | Z-score volume/sentiment spike detection; flag the week rather than blending it into evergreen themes |
| 5 | Star rating vs. text sentiment mismatch (5★ with a complaint) | Theme from text content, not rating alone; flag mismatches for spot-check |
| 6 | PII pasted into an otherwise public review (email, phone) | Regex PII scrub before storage, before embedding, before any Groq call |
| 7 | Off-topic reviews (competitor mentions, unrelated bugs) | Keyword/relevance filter scoped to discovery/recommendation topics; route to an "Other" bucket excluded from headline themes |
| 8 | Same complaint persists across app versions | Tag reviews with `app_version`; allow trend-by-version drill-down instead of treating as a new theme each time |
| 9 | Vector store staleness on weekly refresh | Upsert by `review_id`, never full rebuild |
| 10 | Groq rate-limit/timeout mid-run | Exponential backoff + per-batch checkpointing (chat/analysis; embeddings are local and unaffected) |
| 11 | Chatbot hallucinating beyond retrieved reviews | Strict "answer only from provided excerpts" system prompt + post-hoc citation validation against corpus text |
| 12 | Chatbot question outside corpus scope (e.g. "what's Spotify's stock price?") | Low retrieval similarity → explicit fallback message, never a general-knowledge answer |
| 13 | Over-confident segment claims | Always label inferred segments as "inferred, not verified" in the UI |
| 14 | Review volume too large for the sample/quota budget to scale | Stratified caps per rating-tier × week, tunable as a config value |
| 15 | Malformed export rows / encoding issues | Tolerant parser — skip and log malformed rows rather than crash ingestion |

## 11. Failure and Retry Philosophy

| Failure | Desired behavior |
|---|---|
| Malformed export | Stop early with a readable diagnostic; partial ingest only if explicitly supported |
| Groq Stage A/B/C invalid JSON | Bounded retries with a stricter system prompt; abort and surface if still invalid |
| Validation rejects an artifact | Dashboard shows the last known-good artifact, not a partial/invalid one |
| Embedding/vector store error | Retry with backoff; never silently skip reviews from the retrieval pool |
| Chatbot retrieval returns nothing relevant | Explicit "not enough signal" response, no silent fallback to ungrounded generation |
| Groq auth/quota exhaustion | Operator-visible message; no silent fallback to a different key/model without logging it |

## 12. Deployment Protocol

### 12.1 Local development (Cursor)
- Python virtual environment, `requirements.txt` (google-play-scraper, groq, chromadb,
  streamlit, langdetect, python-dotenv, pandas, sentence-transformers). `sentence-transformers`
  **is required** — embeddings run locally (DEC-003a), not via Groq.
- `.env` (not committed) with `GROQ_API_KEY=...` (required for chat generation / optional
  Phase 3 analysis; **not** needed for embeddings).
- Phase 2 CLI: `python -m src.embeddings.run`
- Dashboard: `streamlit run src/dashboard/app.py`.

### 12.2 Source control
- `.gitignore` excludes `.env`, `data/raw/`, and `vector_store/` (regenerable artifacts).
- Commit `data/processed/*.json` only if you want a graded snapshot reproducible without
  re-running Groq calls.

### 12.3 Hosting
- **Streamlit Community Cloud** is the lowest-friction path: connect the GitHub repo, add
  `GROQ_API_KEY` under the app's Secrets, deploy. Note its disk is **ephemeral** — the
  Chroma store must either be rebuilt on cold start from `data/processed/normalized_reviews.json`,
  or committed as a small snapshot, or moved to a hosted vector DB if it grows large.
- **Render/Railway** are alternatives if you want a persistent disk for the vector store
  without rebuilding on every cold start.

### 12.4 Refresh cadence
- Default: manual "Refresh data" action that re-runs ingestion → embedding upsert →
  Stages A–D → validation, then reruns the dashboard against new artifacts.
- Optional: a scheduled GitHub Action (weekly cron) that runs the same pipeline and commits
  updated `data/processed/*.json`, triggering a redeploy.

### 12.5 Monitoring
- Log ingestion counts, Groq call counts/latency/errors, vector store size, and chatbot
  query volume (questions + retrieved ids, not full PII-free answers needed, but fine to
  keep if scrubbed).

### 12.6 Rollback
- Version processed artifacts by `run_id`/date so a bad LLM run doesn't overwrite the last
  validated dashboard state until the new run passes validation.

## 13. Related Documents

| Document | Role |
|---|---|
| `problemStatement.md` | Requirements and constraints |
| `implementationplan.md` | Master phase index for building the AI agent pipeline |
| `phases/phase-N/implementationplan.md` | Per-phase implementation scope, prompts, and exit criteria |
| `phases/phase-N/eval.md` | Per-phase test procedures and exit criteria sign-off |
| `phases/phase-N/decision.md` | Per-phase tech/business decisions |
| `decision.md` | Master decision log (DEC-001…); cross-cutting ADRs |
| `../cursor_implementation_guide.md` | Quick-reference copy-paste prompts (repo root) |
