# Phase 0 — Repo Scaffold & Prerequisites

**Goal:** Create a runnable Python project skeleton and place spec docs where the Cursor
agent can reference them.

**Architecture reference:** `architecture.md` §12.1 (local development)

---

## Prerequisites

- Python 3.10+ installed locally.
- Groq API key from [console.groq.com](https://console.groq.com).
- GitHub repo created (optional but recommended before Phase 6).

---

## Scope

### In scope

- Folder structure for ingestion, embeddings, analysis, dashboard, and data artifacts.
- `requirements.txt`, `.gitignore`, `.env.example`.
- Copy or link `problemStatement.md` and `architecture.md` into `docs/`.
- This phase plan and master `docs/implementationplan.md`.

### Out of scope

- Any ingestion, embedding, or LLM code (Phases 1–3).
- Streamlit UI (Phases 4–5).

---

## Target directory layout

```
.
├── docs/
│   ├── problemStatement.md
│   ├── architecture.md
│   ├── implementationplan.md          ← master index
│   └── phases/
│       └── phase-N/
│           ├── implementationplan.md
│           ├── eval.md                ← testing + exit criteria sign-off
│           └── decision.md            ← phase tech/business decisions
├── decision.md                        ← master decision log (DEC-001…)
├── src/
│   ├── ingestion/
│   ├── embeddings/
│   ├── analysis/
│   └── dashboard/
├── data/
│   ├── raw/
│   └── processed/
├── vector_store/                      ← gitignored; created in Phase 2
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Implementation steps

| Step | Task | Owner |
|---|---|---|
| 0.1 | Create virtual environment: `python -m venv .venv` | Operator |
| 0.2 | Scaffold folders listed above | Cursor agent |
| 0.3 | Add `requirements.txt` with pinned minimum versions | Cursor agent |
| 0.4 | Add `.gitignore` for `.env`, `data/raw/`, `vector_store/`, `__pycache__/`, `.venv/` | Cursor agent |
| 0.5 | Add `.env.example` with `GROQ_API_KEY=` placeholder | Cursor agent |
| 0.6 | Place spec docs in `docs/` | Operator or agent |
| 0.7 | `pip install -r requirements.txt` and verify imports | Operator |

### `requirements.txt` (minimum packages)

```
google-play-scraper
groq
chromadb
sentence-transformers
streamlit
langdetect
python-dotenv
pandas
```

---

## Cursor agent prompt

```
Create a Python project scaffold for the Spotify Review Discovery Engine per
@docs/problemStatement.md and @docs/phases/phase-0/implementationplan.md.

Folders: docs/ (already has specs), src/ingestion/, src/embeddings/, src/analysis/,
src/dashboard/, data/raw/, data/processed/, vector_store/.
Add requirements.txt with: google-play-scraper, groq, chromadb, sentence-transformers,
streamlit, langdetect, python-dotenv, pandas.
Add .gitignore excluding .env, data/raw/, vector_store/, .venv/, __pycache__/.
Add .env.example with GROQ_API_KEY=.
Add empty __init__.py files under each src/ subpackage.
Do not implement ingestion or dashboard yet — scaffold only.
```

---

## Exit criteria

- [ ] All folders exist per layout above.
- [ ] `pip install -r requirements.txt` succeeds in a fresh venv.
- [ ] `.env.example` present; `.env` gitignored (create locally with real key — never commit).
- [ ] `docs/problemStatement.md`, `docs/architecture.md`, and phase plans are in repo.
- [ ] No application logic beyond empty package stubs.

---

## After this phase

1. Complete [eval.md](eval.md) — run all T0/S0 tests; check exit criteria; sign off Pass/Fail.
2. Accept decisions in [decision.md](decision.md) (Python version, pinning); index in [docs/decision.md](../../decision.md).
3. Commit: e.g. `chore: scaffold project and docs for review discovery engine`.
4. Proceed to [Phase 1 — Ingestion](../phase-1/implementationplan.md) only if eval **Pass**.

---

## Common pitfalls

- Committing `.env` with a real API key — use `.env.example` only in git.
- Skipping `docs/` — later phases depend on `@docs/` references in Cursor prompts.
