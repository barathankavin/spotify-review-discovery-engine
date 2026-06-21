# Phase 5 Evaluation — RAG Chatbot

**Plan:** [implementationplan.md](implementationplan.md)  
**Evaluated by:** _name_  
**Date:** _YYYY-MM-DD_  
**Result:** ☐ Pass  ☐ Fail  ☐ Pass with notes

---

## 1. Test environment

| Item | Value |
|---|---|
| Embedding model (must match Phase 2) | |
| `TOP_K` | |
| `SIMILARITY_THRESHOLD` | |
| Groq model | |
| Branch / commit | |

---

## 2. Grounded question tests (required)

Each must return an answer with ≥1 `review_id` citation; cited text must support the claim.

| # | Question | Got answer? | Citations? | Provenance OK? | PII free? | Pass? |
|---|---|---|---|---|---|---|
| T5.1 | Why do users struggle to discover new music? | ☐ | ☐ | ☐ | ☐ | ☐ |
| T5.2 | What are the most common frustrations with recommendations? | ☐ | ☐ | ☐ | ☐ | ☐ |
| T5.3 | What listening behaviors are users trying to achieve? | ☐ | ☐ | ☐ | ☐ | ☐ |
| T5.4 | What causes users to repeatedly listen to the same content? | ☐ | ☐ | ☐ | ☐ | ☐ |
| T5.5 | Which user segments experience different discovery challenges? | ☐ | ☐ | ☐ | ☐ | ☐ |
| T5.6 | What unmet needs emerge consistently across reviews? | ☐ | ☐ | ☐ | ☐ | ☐ |

**Citation spot-check (paste one example per question):**

| Question | review_id cited | supports claim? |
|---|---|---|
| T5.1 | | ☐ |
| T5.2 | | | |

---

## 3. Refusal tests (required)

Must return explicit "not enough signal" (or equivalent) — **no** general-knowledge answer.

| # | Question | Refused? | Groq called? (should be No if low sim) | Pass? |
|---|---|---|---|---|
| T5.7 | What's Spotify's stock price? | ☐ | ☐ | ☐ |
| T5.8 | Will Spotify launch a lossless tier in Europe next year? | ☐ | ☐ | ☐ |
| T5.9 | Who is the CEO of Spotify's competitor Apple Music? | ☐ | ☐ | ☐ |

---

## 4. Functional / safety tests

| # | Test | Steps | Expected | Pass? |
|---|---|---|---|---|
| T5.10 | Tab loads | Open Chatbot tab | No error | ☐ |
| T5.11 | Source excerpts | Expand citation | Shows review_id, rating, date — no username | ☐ |
| T5.12 | Validator on answer | Trigger answer with PII in mock retrieval | Blocked or redacted | ☐ |
| T5.13 | Low-similarity gate | Nonsense query / empty store edge | Refusal without Groq | ☐ |
| T5.14 | Groq logging | Ask 3 questions | Calls logged; no infinite loop | ☐ |
| T5.15 | Same embedding model | Compare model id to Phase 2 DEC | Match | ☐ |

---

## 5. Exit criteria

| # | Criterion | Pass? | Evidence |
|---|---|---|---|
| E5.1 | Chatbot tab in Streamlit app | ☐ | |
| E5.2 | 6 grounded questions answered with citations | ☐ | |
| E5.3 | 3 refusal questions handled correctly | ☐ | |
| E5.4 | Low-similarity skips Groq | ☐ | |
| E5.5 | Validators on every answer | ☐ | |
| E5.6 | Expandable sources; no reviewer identity | ☐ | |
| E5.7 | Chat Groq calls logged | ☐ | |

---

## 6. Decisions recorded this phase

| DEC ID | Title | Accepted? |
|---|---|---|
| | TOP_K | ☐ |
| | SIMILARITY_THRESHOLD | ☐ |
| | Refusal message copy | ☐ |

---

## 7. Issues and follow-ups

| ID | Issue | Severity | Resolution |
|---|---|---|---|
| | | | |

---

## 8. Sign-off

**Phase 5 complete:** ☐ Yes — proceed to [Phase 6](../phase-6/implementationplan.md)

**Notes:**
