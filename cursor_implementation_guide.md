# Step-by-Step Guide: Building the Spotify Review Discovery Engine in Cursor

This is the execution sequence for `docs/problemStatement.md` + `docs/architecture.md`.
Each phase below is a Cursor agent prompt you can paste close to verbatim, anchored to the
spec docs so the agent doesn't improvise scope.

**Detailed phase plans:** see `docs/implementationplan.md` and
`docs/phases/phase-N/implementationplan.md` for scope, module structure, exit criteria,
and edge cases beyond these copy-paste prompts.

**Note on scraping approach**: Phase 1 below has Cursor write a plain Python ingestion
module that calls `google-play-scraper` directly. There is no n8n workflow, no Apify
actor, and no Zapier zap anywhere in this build — ingestion is just code in your repo,
matching the reference milestone's "non-MCP" ingestion pattern (see `architecture.md`
§5.1). If you ever do want a no-code scraper later, that's a separate decision — it isn't
part of this build.

## 0. Before you open Cursor

- Get a Groq API key at console.groq.com. Check **current** rate limits at
  `console.groq.com/docs/rate-limits` for the model you'll use — they change, and
  `architecture.md` §9 only has example numbers to plan against.
- Create a GitHub repo, clone it, open the folder in Cursor.
- Model assignment per task (mirrors the pattern in the reference milestone):
  - **Architecture/planning/edge-case review** → a frontier reasoning model — use this to
    refine `architecture.md` itself if Groq's real limits differ from the example numbers.
  - **Actual implementation** (ingestion, embeddings, Streamlit pages, RAG wiring) →
    Sonnet-class model in Cursor's agent mode.
  - **Repetitive test runs / git commits / lint fixes** → the fastest/cheapest model
    available in Cursor.

## 1. Repo scaffold

```
Create a Python project scaffold for an AI-powered review discovery engine.
Folders: docs/, src/ingestion/, src/embeddings/, src/analysis/, src/dashboard/,
data/raw/, data/processed/, vector_store/.
Add requirements.txt with: google-play-scraper, groq, chromadb, sentence-transformers,
streamlit, langdetect, python-dotenv, pandas.
Add .gitignore excluding .env, data/raw/, vector_store/.
Add .env.example with GROQ_API_KEY=
```

## 2. Add the docs as agent context

Spec docs live in `docs/` (`problemStatement.md`, `architecture.md`, `implementationplan.md`,
and `phases/phase-N/implementationplan.md`). From here on, every prompt references
`@docs/problemStatement.md`, `@docs/architecture.md`, and the current phase plan so the
agent has full context instead of guessing.

## 3. Phase 1 — Ingestion & normalization

```
Implement "Phase 1 — Ingestion & Normalization" from @docs/architecture.md section 5.1.
Write this as a plain Python module — do not use n8n, Apify, Zapier, or any workflow
automation tool. Use google-play-scraper to pull Spotify Play Store reviews (package name
com.spotify.music) for the last 8-12 weeks. Normalize into the NormalizedReview schema
from architecture.md section 7. Drop reviews under 6 words, drop emoji-only reviews,
keep English only via langdetect, dedupe near-identical bodies, scrub PII patterns
(emails/phone numbers) from review bodies. Save to data/processed/normalized_reviews.json
and print an ingestion report (raw count, filtered count, deduped count, date range).
```

Run it. Inspect the ingestion report before moving on — confirm row counts and date range
look right for 8–12 weeks of Spotify reviews.

## 4. Phase 2 — Embedding & vector store

```
Implement "Embedding & vector store" from @docs/architecture.md section 5.2. Embed
data/processed/normalized_reviews.json with sentence-transformers/all-MiniLM-L6-v2 and
upsert into a persistent Chroma collection at vector_store/, keyed by review_id so
re-running this script only embeds new/changed reviews. Add a CLI sanity check that takes
a free-text query and prints the top 5 most similar reviews with similarity scores.
```

Run the sanity check with a query like `"why does it keep playing the same songs"` and
confirm the retrieved reviews are actually relevant before trusting the chatbot on top of
this later.

## 5. Phase 3 — Lock in the Groq budget, then implement analysis

First, confirm real quota numbers:

```
Read @docs/architecture.md section 9 (Groq quota planning). Check the current rate
limits for <your chosen model> at console.groq.com/docs/rate-limits. Propose a batch
size, sleep/backoff strategy, and checkpointing approach so a full Phase 3 run never
exceeds RPM/RPD/TPM/TPD. Update architecture.md section 9 with the final numbers you'll
implement against.
```

Then implement:

```
Implement "Analysis (LLM-centric, Groq)" from @docs/architecture.md section 5.3, Stages
A-D. Stratify-sample normalized_reviews.json by rating tier x ISO week per the rules in
that section. Stage A: discover <=5 themes via Groq. Stage B: per theme, pull verbatim
supporting quotes and a <=250-word summary. Stage C: extract a ranked unmet-needs list
(max ~5). Stage D: tag reviews with inferred segment heuristics (rating tier, app
version, premium/free/ads keyword hits). Persist themes.json, unmet_needs.json, and
segments.json under data/processed/. Implement per-batch checkpointing so a rate-limit
error mid-run can resume instead of restarting.
```

Run it, then check outputs against `architecture.md` section 6 (validation rules): theme
count ≤5, quote provenance traces to the corpus, word counts ≤250, no PII anywhere.

## 6. Phase 4 — Dashboard

```
Implement the dashboard from @docs/architecture.md section 5.5 as a Streamlit app at
src/dashboard/app.py with four tabs: Overview, Theme Deep-Dive, Segments, Unmet Needs —
reading from data/processed/themes.json, unmet_needs.json, and segments.json. Keep each
theme's narrative card under 250 words. Never render any reviewer-identifying field.
Label segment cuts as "inferred from review text, not verified."
```

Run with:

```
streamlit run src/dashboard/app.py
```

## 7. Phase 5 — RAG chatbot tab

```
Implement the RAG chatbot from @docs/architecture.md section 5.6 as a fifth "Chatbot" tab
in the same Streamlit app. Embed the user's question with the same embedding model used
in Phase 2, retrieve the top-k reviews from the Chroma store, and if max similarity is
below a configurable threshold return "not enough signal in the reviews to answer that"
without calling Groq. Otherwise call Groq with a system prompt that restricts it to
answering only from the retrieved excerpts, citing review_id for every claim. Run the
answer through the same PII/provenance checks used in Phase 3 before rendering.
```

Test it against the six core research questions in `problemStatement.md` section 2, plus
one deliberately out-of-scope question (e.g. "what's Spotify's stock price?") to confirm
both grounded answers and the fallback path work.

## 8. Phase 6 — Deployment

```
Generate a deployment plan for this Streamlit app on Streamlit Community Cloud, per
@docs/architecture.md section 12 (deployment protocol). Cover how to handle the Chroma
vector store given Streamlit Cloud's ephemeral disk, and how the weekly refresh job
should run. Save the plan to docs/deployment_plan.md.
```

Then follow that plan: push to GitHub, connect the repo on Streamlit Community Cloud, add
`GROQ_API_KEY` under the app's Secrets, deploy, and smoke-test all five tabs end to end on
the live URL.

## 9. Recurring weekly run

Re-run Phases 1→3 weekly (manually, or via a scheduled GitHub Action) to refresh
`data/processed/*.json` and the vector store, then redeploy or trigger a re-fetch in the
running app. Keep prior artifacts around (per `architecture.md` §11) so a bad run doesn't
silently overwrite the last good dashboard state.

## General Cursor tips for this build

- Anchor every implementation prompt to `@docs/architecture.md` and
  `@docs/problemStatement.md` so the agent doesn't add scope this build explicitly doesn't
  need (no Gmail/Docs MCP, no external write surfaces).
- After each phase, complete `docs/phases/phase-N/eval.md` (tests + exit criteria sign-off)
  and record decisions in `docs/phases/phase-N/decision.md` / `docs/decision.md` — this
  keeps "done" honest rather than "looks done."
- Commit after each phase passes its own checks, not at the end of the day — small commits
  make it cheap to roll back if a Stage 3 prompt drifts and starts hallucinating themes.
