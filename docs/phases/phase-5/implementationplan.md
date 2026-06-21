# Phase 5 — RAG Chatbot (Grounded Q&A Agent)

**Goal:** Add a fifth **Chatbot** tab that answers free-form questions using retrieval from
the full review corpus and Groq generation — with citations, validation, and explicit refusal
when signal is insufficient.

**Architecture reference:** `architecture.md` §5.6, §10 (#11–12), `problemStatement.md` §3

---

## Prerequisites

- Phase 2 complete: Chroma vector store with full corpus embedded.
- Phase 4 complete: Streamlit app with four analytics tabs.
- Phase 3 complete: validators module reusable for chat answers.
- `GROQ_API_KEY` in `.env`.

---

## Scope

### In scope

- Fifth tab **Chatbot** in existing Streamlit app.
- RAG flow: embed question → retrieve top-k → threshold gate → Groq → validate → render.
- Citations to `review_id` for every factual claim.
- Refusal path when max similarity below threshold (no Groq call).
- Same PII/provenance validators as Phase 3.

### Out of scope

- General-knowledge answers (stock price, company strategy, etc.).
- Chat history persistence across sessions (optional nice-to-have).
- Separate Groq project/key (optional optimization).

---

## RAG agent flow

```
User question (Streamlit chat input)
        │
        ▼
Embed question (same local model as Phase 2)
        │
        ▼
Retrieve top-k reviews from Chroma (default k=8)
        │
        ▼
max(similarity) < threshold?
   YES ──▶ Return "Not enough signal in the reviews to answer that." (no Groq)
   NO  ──▶ Continue
        │
        ▼
Groq chat completion
  System prompt: answer ONLY from provided excerpts; cite review_id per claim
        │
        ▼
Validators: PII scan + citation provenance check
        │
        ▼
Render answer + expandable source excerpts (review_id, rating, date snippet)
```

---

## Configuration

| Parameter | Suggested default | Purpose |
|---|---|---|
| `TOP_K` | 8 | Reviews retrieved per question |
| `SIMILARITY_THRESHOLD` | 0.35–0.45 (tune on dev) | Below → refuse |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Same as Phase 3 |
| `MAX_ANSWER_TOKENS` | 512 | Keep responses concise |

---

## System prompt principles

The Groq system prompt must enforce:

1. Answer **only** from the retrieved review excerpts provided in context.
2. Cite `[review_id: ...]` for every factual claim about user behavior or sentiment.
3. If excerpts are ambiguous or contradictory, say so — do not synthesize beyond evidence.
4. Do not use general knowledge about Spotify, music industry, or product roadmap.
5. Do not include reviewer names or PII in the answer.

---

## Suggested module structure

```
src/dashboard/
├── components/
│   └── chatbot.py      # UI + orchestration
src/analysis/
└── validators.py       # reuse validate_answer(), validate_citations()

# Or shared:
src/rag/
├── __init__.py
├── retriever.py        # embed query, Chroma search
├── generator.py        # Groq call + prompt assembly
└── gate.py             # similarity threshold check
```

---

## Cursor agent prompt

```
Implement Phase 5 — RAG Chatbot from @docs/architecture.md section 5.6 and
@docs/phases/phase-5/implementationplan.md.

Add a fifth "Chatbot" tab to src/dashboard/app.py.

Flow:
1. Embed user question with the same sentence-transformers model from Phase 2
2. Retrieve top-k (default 8) reviews from Chroma vector store
3. If max similarity is below configurable threshold, return
   "Not enough signal in the reviews to answer that." WITHOUT calling Groq
4. Otherwise call Groq with system prompt restricting answers to retrieved excerpts only;
   require review_id citation for every claim
5. Run answer through the same PII and provenance validators from Phase 3 before rendering
6. Show answer plus expandable source excerpts (review_id, rating, date — no reviewer names)

Reuse src/analysis/validators.py where possible.
Do not answer general-knowledge questions from model weights alone.
```

---

## Test plan (required)

### Grounded questions (must answer with citations)

From `problemStatement.md` §3:

1. "Why do users struggle to discover new music?"
2. "What are the most common frustrations with recommendations?"
3. "What listening behaviors are users trying to achieve?"
4. "What causes users to repeatedly listen to the same content?"
5. "Which user segments experience different discovery challenges?"
6. "What unmet needs emerge consistently across reviews?"

### Refusal questions (must NOT call Groq or must refuse)

1. "What's Spotify's stock price?"
2. "Will Spotify launch a lossless tier in Europe next year?"
3. "Who is the CEO of Spotify's competitor Apple Music?"

### Quality checks per grounded answer

- [ ] At least one `review_id` citation present.
- [ ] Cited review text supports the claim (manual spot-check).
- [ ] No PII in answer.
- [ ] No obvious hallucination beyond retrieved excerpts.

---

## Exit criteria

- [ ] Chatbot tab loads inside existing Streamlit app.
- [ ] Grounded questions return answers with `review_id` citations.
- [ ] Out-of-scope questions return explicit "not enough signal" (or equivalent refusal).
- [ ] Low-similarity queries skip Groq entirely.
- [ ] Validators run on every answer before display.
- [ ] Source excerpts expandable; show rating/date but no reviewer identity.
- [ ] Groq quota: chat calls logged; no unbounded loop on repeated questions.

---

## After this phase

1. Complete [eval.md](eval.md) — 6 grounded + 3 refusal tests, safety checks, sign-off.
2. Accept decisions in [decision.md](decision.md) (top-k, threshold, refusal copy).
3. Commit chatbot code.
4. Proceed to [Phase 6](../phase-6/implementationplan.md) only if eval **Pass**.

---

## Common pitfalls

- Calling Groq even when retrieval is empty — wastes quota and invites hallucination.
- Citing `review_id`s that don't support the claim — provenance validator must catch.
- Using a different embedding model than Phase 2 — retrieval quality breaks silently.
- Presenting inferred segments as verified facts in chat answers.
