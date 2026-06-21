# Spotify Review Discovery Engine

AI-powered pipeline: Play Store reviews → themes, dashboard, RAG chatbot.

## Setup

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
```

## Run locally

```bash
streamlit run streamlit_app.py
# or: streamlit run src/dashboard/app.py
```

Open http://localhost:8501 — five tabs: Overview, Themes, Segments, Unmet Needs, Chatbot.

## Pipeline commands

| Phase | Command |
|---|---|
| 1 Ingestion | `python -m src.ingestion.run --lookback-weeks 10` |
| 2 Embeddings | `python -m src.embeddings.run` |
| 3 Analysis | `python -m src.analysis.run` (or `--rule-baseline` without Groq) |
| 6 Ensure store | `python -m src.ops.run ensure-store` |
| 6 Weekly refresh | `python -m src.ops.run refresh` |
| 6 Smoke test | `python scripts/smoke_test.py` |

## Deploy

See **`docs/deployment_plan.md`** for full instructions and platform comparison.

**Recommended: Hugging Face Spaces** (Streamlit SDK, ~16 GB RAM handles the 27k Chroma rebuild).

1. Push repo to GitHub (commit `data/processed/*.json`, not `.env` or `vector_store/`)
2. New Space (Streamlit SDK) **or** [share.streamlit.io](https://share.streamlit.io) → main file `streamlit_app.py`
3. Set Secrets: `GROQ_API_KEY`, `EMBEDDING_BACKEND=local`
4. Run smoke test checklist from deployment plan

## Project layout

```
src/ingestion/    Phase 1 — fetch & normalize Play Store reviews
src/embeddings/   Phase 2 — local/Groq embeddings + Chroma
src/analysis/     Phase 3 — Groq or rule-based theme analysis
src/dashboard/    Phases 4–5 — Streamlit UI + chatbot
src/ops/          Phase 6 — ensure store, weekly refresh
src/rag/          Phase 5 — retrieval + grounded generation
docs/             Specs, deployment plan, phase eval logs
```

See `docs/implementationplan.md` for the full build sequence.
