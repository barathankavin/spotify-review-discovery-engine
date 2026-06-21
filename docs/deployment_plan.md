# Deployment & Operations Plan

**Project:** Spotify Review Discovery Engine  
**Hosting:** Streamlit Community Cloud (primary)  
**Last updated:** 2026-06-21

---

## 1. Architecture summary

| Layer | Artifact | Deploy strategy |
|---|---|---|
| Phase 1 | `data/processed/normalized_reviews.json` | **Commit to git** (no PII fields) |
| Phase 2 | `vector_store/` (Chroma) | **Gitignored** — rebuild on cold start |
| Phase 3 | `themes.json`, `unmet_needs.json`, `segments.json`, `run_metadata.json` | **Commit to git** (validated snapshot) |
| Phase 4–5 | `src/dashboard/app.py` | Streamlit entry point |
| Secrets | `GROQ_API_KEY`, optional `HF_TOKEN` | Platform secrets only |

---

## 2. Streamlit Community Cloud setup

### 2.1 Prerequisites

- GitHub repository with this codebase pushed to `main`
- Groq API key (for chatbot + optional LLM analysis refresh)
- Processed JSON committed under `data/processed/` (see §4)

### 2.2 Deploy steps

1. Push repo to GitHub (do **not** commit `.env` or `.streamlit/secrets.toml`).
2. Open [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Connect the GitHub repo and branch (`main`).
4. **Main file path:** `src/dashboard/app.py`
5. **App settings → Secrets** — paste TOML (see `.streamlit/secrets.toml.example`):

   ```toml
   GROQ_API_KEY = "gsk_..."
   EMBEDDING_BACKEND = "local"
   LOCAL_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
   RAG_TOP_K = "8"
   RAG_SIMILARITY_THRESHOLD = "0.35"
   ```

6. Deploy and wait for build (~3–5 min first time; longer if Chroma rebuild runs).

### 2.3 Local run (same entry point)

```bash
streamlit run src/dashboard/app.py
```

---

## 3. Chroma cold-start strategy (DEC-028)

**Decision:** Rebuild from committed `normalized_reviews.json` when the vector store is empty.

| Item | Detail |
|---|---|
| Trigger | First Chatbot tab load (via `ensure_vector_store()`) |
| Duration | ~4 min for 27k reviews on 2 vCPU (local benchmark ~225s) |
| UX | Streamlit spinner + info banner after rebuild |
| Code | `src/ops/ensure_vector_store.py` → `src/embeddings/run.run_embed_all` |
| CLI | `python -m src.ops.run ensure-store` |

**Why not commit `vector_store/`?** Size (~100MB+) and gitignore policy; rebuild is acceptable for MVP demo.

**Future:** Hosted vector DB (Pinecone/Weaviate) or Render persistent disk.

---

## 4. Committing processed JSON (DEC-030)

Commit these for deploy without re-running Groq on every cold start:

```
data/processed/normalized_reviews.json
data/processed/themes.json
data/processed/unmet_needs.json
data/processed/segments.json
data/processed/run_metadata.json
data/processed/lkg/          # last-known-good copies
```

Do **not** commit: `data/raw/`, `vector_store/`, `.env`, backups.

Normalized schema strips reviewer identity — only internal `review_id`, rating, date, body.

---

## 5. Weekly refresh playbook (DEC-029)

### Manual (minimum)

```bash
# Full refresh (requires Groq quota for LLM analysis)
python -m src.ops.run refresh

# Or step-by-step:
python -m src.ingestion.run --lookback-weeks 10
python -m src.embeddings.run
python -m src.analysis.run          # Groq LLM themes
# python -m src.analysis.run --rule-baseline   # if Groq quota exhausted

python scripts/smoke_test.py
git add data/processed/*.json data/processed/lkg/
git commit -m "chore: weekly artifact refresh"
git push   # triggers Streamlit redeploy
```

Backups land in `data/processed/backups/<run_id>/` before each refresh.

### Validation gate

- Check `run_metadata.json` → `theme_validation_ok: true`
- If **false**: dashboard keeps last-known-good (`data/processed/lkg/`)
- Do not promote failed artifacts to active paths

### Automated (optional)

GitHub Action: `.github/workflows/weekly-refresh.yml`  
Runs Monday 06:00 UTC or manual dispatch; commits JSON if smoke test passes.

---

## 6. Monitoring (minimum viable)

| Signal | Source | Action |
|---|---|---|
| Ingest row count | `src.ingestion.run` report | Alert if &gt;50% drop WoW |
| Groq 429 / TPD | analysis/chat logs | Pause refresh; use `--rule-baseline` |
| Validation failure | `run_metadata.json` | Do not overwrite; investigate |
| Vector store count | `ensure_vector_store` / embed checkpoint | Zero after startup = rebuild failed |
| Chatbot refusal rate | Streamlit logs | Informational |

No PII in logs — log `review_id` and question text only.

---

## 7. Rollback

1. Each refresh backs up to `data/processed/backups/<run_id>/`.
2. Dashboard loader falls back to `data/processed/lkg/` on validation failure.
3. Manual rollback: copy a backup folder’s JSON files to `data/processed/` and redeploy.
4. Version by `run_id` in `run_metadata.json`.

---

## 8. Live smoke test checklist

Run after every deploy or refresh (`python scripts/smoke_test.py` locally, or manual on live URL):

| # | Check |
|---|---|
| 1 | App loads at public URL without 500 |
| 2 | Overview: themes + charts render |
| 3 | Theme Deep-Dive: summary + quotes |
| 4 | Segments: disclaimer banner visible |
| 5 | Unmet Needs: ranked list |
| 6 | Chatbot: grounded question retrieves sources |
| 7 | Chatbot: stock price / CEO question refused without Groq |
| 8 | No reviewer names or PII on any tab |
| 9 | Cold start: Chatbot builds index if `vector_store/` empty |

---

## 9. Security

- `GROQ_API_KEY` only in Streamlit Secrets / local `.env` (gitignored)
- Optional `HF_TOKEN` for Hugging Face Hub (embeddings download)
- Never commit secrets or raw Play Store exports

---

## 10. Related docs

- `docs/architecture.md` §11–12 — failure philosophy, deployment protocol
- `docs/phases/phase-6/implementationplan.md` — phase scope
- `docs/phases/phase-6/decision.md` — DEC-027 through DEC-030
