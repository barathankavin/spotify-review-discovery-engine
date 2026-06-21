# Phase 6 — Deployment, Refresh & Operations

**Goal:** Deploy the full Streamlit app (dashboard + chatbot) to a hosted environment,
document the operational playbook, and establish a weekly refresh cadence.

**Architecture reference:** `architecture.md` §12 (deployment protocol), §11 (failure/retry)

---

## Prerequisites

- Phases 0–5 complete and passing exit criteria locally.
- GitHub repo with code pushed.
- Groq API key ready for platform secrets (not in repo).

---

## Scope

### In scope

- Deployment plan document: `docs/deployment_plan.md`.
- Streamlit Community Cloud deployment (primary path).
- Strategy for ephemeral disk / Chroma rebuild on cold start.
- Weekly refresh procedure (manual or GitHub Action outline).
- Smoke test checklist on live URL.
- Monitoring and rollback guidance.

### Out of scope

- Production-grade SLA, autoscaling, or multi-region hosting.
- Migrating to hosted vector DB (document as future option only).

---

## Hosting decision

| Option | Pros | Cons | Chroma strategy |
|---|---|---|---|
| **Streamlit Community Cloud** (recommended) | Free, fast setup, native Streamlit | Ephemeral disk | Rebuild from JSON on startup OR commit small snapshot |
| Render / Railway | Persistent disk | Paid tier for disk | Persist `vector_store/` on volume |
| Local only | Full control | Not shareable with stakeholders | N/A |

**Default recommendation:** Streamlit Community Cloud for demo/PM access.

---

## Cold-start vector store strategy

Streamlit Cloud disk is ephemeral. Pick one:

1. **Rebuild on startup (recommended for MVP):** App checks for Chroma; if missing, embed
   from `data/processed/normalized_reviews.json` (add startup hook — may slow first load).
2. **Commit snapshot:** Include a small pre-built `vector_store/` in repo (only if size
   acceptable; usually gitignore otherwise).
3. **Hosted vector DB:** Pinecone/Weaviate later — out of scope for initial deploy.

Document chosen strategy in `docs/deployment_plan.md`.

---

## Deployment steps

| Step | Action |
|---|---|
| 6.1 | Generate `docs/deployment_plan.md` (see Cursor prompt below) |
| 6.2 | Ensure `requirements.txt` complete; add `packages.txt` if system deps needed |
| 6.3 | Push to GitHub `main` (or deploy branch) |
| 6.4 | Connect repo on [share.streamlit.io](https://share.streamlit.io) |
| 6.5 | Set Secrets: `GROQ_API_KEY` |
| 6.6 | Set main file: `src/dashboard/app.py` |
| 6.7 | Deploy and wait for build |
| 6.8 | Run live smoke test (checklist below) |

---

## Cursor agent prompt

```
Generate Phase 6 deployment plan per @docs/architecture.md section 12 and
@docs/phases/phase-6/implementationplan.md.

Create docs/deployment_plan.md covering:
1. Streamlit Community Cloud setup (repo connect, secrets, main file path)
2. Chroma vector store strategy for ephemeral disk (rebuild on startup vs snapshot)
3. Weekly refresh procedure: re-run Phases 1-3, validate, update data/processed/*.json
4. Optional GitHub Action cron outline for automated weekly refresh
5. Monitoring: ingest counts, Groq errors, chatbot query volume (no PII in logs)
6. Rollback: version artifacts by run_id/date; keep last-known-good on validation failure
7. Smoke test checklist for all five dashboard tabs on live URL

Also add any startup hook code needed for Chroma rebuild if that is the chosen strategy.
```

---

## Live smoke test checklist

| # | Check | Pass? |
|---|---|---|
| 1 | App loads at public URL without 500 error | |
| 2 | Overview tab: themes and charts render | |
| 3 | Theme Deep-Dive: select theme, quotes visible | |
| 4 | Segments: disclaimer banner present | |
| 5 | Unmet Needs: ranked list renders | |
| 6 | Chatbot: grounded question returns citations | |
| 7 | Chatbot: out-of-scope question refused | |
| 8 | No PII visible on any tab | |
| 9 | Cold start (if applicable): vector store rebuilds or loads | |

---

## Weekly refresh playbook

```
1. Run: python -m src.ingestion.run
2. Run: python -m src.embeddings.run
3. Run: python -m src.analysis.run
4. Verify validation passed (check run_metadata.json)
5. If valid: replace data/processed/*.json (keep prior run as backup)
6. If invalid: keep last-known-good; investigate logs
7. Redeploy or restart Streamlit app to pick up new artifacts
8. Re-run smoke test items 2–7
```

Optional automation: GitHub Action on weekly cron → run pipeline → commit JSON if validation
passes → trigger redeploy.

---

## Monitoring (minimum viable)

| Signal | Where | Alert threshold |
|---|---|---|
| Ingest row count | ingestion report / logs | Drop &gt;50% week-over-week |
| Groq 429 errors | analysis/chat logs | Any sustained 429 |
| Validation failures | run_metadata | Any failure → no overwrite |
| Chatbot refusal rate | query log | Informational only |
| Vector store size | embed logs | Zero after startup = rebuild failed |

---

## Rollback procedure

1. Artifacts versioned by `run_id` and date in filename or subdirectory
   (e.g. `data/processed/2025-06-21/themes.json`).
2. On validation failure, dashboard reads last-known-good (Phase 4 loader).
3. To rollback manually: copy previous valid JSON set to `data/processed/` active paths.
4. Redeploy or restart app.

---

## Exit criteria

- [ ] `docs/deployment_plan.md` exists and matches chosen hosting strategy.
- [ ] App deployed to public Streamlit URL (or documented alternative).
- [ ] `GROQ_API_KEY` set in platform secrets only — not in repo.
- [ ] All five tabs pass live smoke test.
- [ ] Chroma strategy documented and verified on cold start.
- [ ] Weekly refresh steps documented (manual minimum).
- [ ] Rollback / last-known-good behavior verified.

---

## After this phase

1. Complete [eval.md](eval.md) — live smoke test, security/ops checks, build completion checklist.
2. Accept decisions in [decision.md](decision.md) (hosting, Chroma cold-start, refresh cadence).
3. Final commit: `docs: add deployment plan and ops playbook`.
4. **Build complete** when eval **Pass** — enter recurring weekly refresh (Phases 1→3).

---

## Future enhancements (not required now)

- GitHub Action for automated weekly pipeline + deploy.
- Hosted vector DB for faster cold starts at scale.
- Separate Groq API key/project for chat vs batch analysis.
- Next.js frontend replacing Streamlit.

---

## Common pitfalls

- Committing `.env` or API keys to GitHub — use Streamlit Secrets.
- Deploying without processed JSON in repo and without rebuild hook — chatbot has empty corpus.
- Overwriting good artifacts with a failed LLM run — always validate before promote.
