# Phase 3 Evaluation — Groq Analysis & Validation

**Plan:** [implementationplan.md](implementationplan.md)  
**Evaluated by:** _name_  
**Date:** _YYYY-MM-DD_  
**Result:** ☐ Pass  ☐ Fail  ☐ Pass with notes

---

## 1. Test environment

| Item | Value |
|---|---|
| Groq model | |
| Sample size (stratified) | |
| Sample seed | |
| Prompt version | |
| `run_id` | |
| Branch / commit | |

---

## 2. Run metadata (`run_metadata.json`)

| Field | Value | Expected |
|---|---|---|
| `run_id` | | present |
| `seed` | | logged |
| `model_id` | | matches DEC |
| `prompt_version` | | logged |
| Groq call count | | within quota plan |
| Sample size | | hundreds–~1000, not full corpus |
| Validation status | | passed |

---

## 3. Artifact checks

| File | Exists | Valid JSON | Pass? |
|---|---|---|---|
| `themes.json` | ☐ | ☐ | ☐ |
| `unmet_needs.json` | ☐ | ☐ | ☐ |
| `segments.json` | ☐ | ☐ | ☐ |
| `run_metadata.json` | ☐ | ☐ | ☐ |

---

## 4. Functional tests

| # | Test | Steps | Expected | Pass? |
|---|---|---|---|---|
| T3.1 | Full pipeline | `python -m src.analysis.run` | Exit 0; all artifacts written | ☐ |
| T3.2 | Theme count | Count themes in output | ≤ 5 | ☐ |
| T3.3 | Theme scope | Read theme labels | Discovery/recommendation related | ☐ |
| T3.4 | Summary word count | Count words per theme summary | All ≤ 250 | ☐ |
| T3.5 | Quote provenance | Spot-check 3 quotes vs `normalized_reviews.json` | Verbatim substring match | ☐ |
| T3.6 | PII scan | Regex on all LLM outputs | No email/phone/handles | ☐ |
| T3.7 | Segment inferred flag | Inspect `segments.json` | `inferred` or equivalent | ☐ |
| T3.8 | Unmet needs rank | Inspect list | Ordered rank 1..N, max ~5 | ☐ |
| T3.9 | No full corpus to Groq | Compare sample size vs normalized count | sample << corpus | ☐ |

---

## 5. Validator tests

| # | Test | How | Pass? |
|---|---|---|---|
| T3.10 | Reject >5 themes | Inject bad artifact or unit test | Validator rejects ☐ |
| T3.11 | Reject overlong summary | Unit test / mock | Rejects ☐ |
| T3.12 | Reject bad provenance | Quote not in corpus | Rejects ☐ |
| T3.13 | Bounded retry | Force invalid JSON once | Retries then succeeds or aborts ☐ |

---

## 6. Resilience tests

| # | Test | Steps | Pass? |
|---|---|---|---|
| T3.14 | Checkpoint resume | Kill mid-run; re-run | Resumes from checkpoint, not from zero ☐ |
| T3.15 | Rate limit handling | _Simulate or observe 429_ | Backoff + resume ☐ |

---

## 7. Themes discovered (record for stakeholders)

| # | Theme label | Supporting review count | On-scope? |
|---|---|---|---|
| 1 | | | ☐ |
| 2 | | | ☐ |
| 3 | | | ☐ |
| 4 | | | ☐ |
| 5 | | | ☐ |

---

## 8. Exit criteria

| # | Criterion | Pass? | Evidence |
|---|---|---|---|
| E3.1 | All four JSON outputs exist and parse | ☐ | |
| E3.2 | ≤5 themes with summary, quotes, `review_id`s | ☐ | |
| E3.3 | Unmet needs ranked with provenance | ☐ | |
| E3.4 | Segments tagged as inferred | ☐ | |
| E3.5 | Validation auto-runs; failure → retry or abort | ☐ | |
| E3.6 | `run_metadata.json` complete | ☐ | |
| E3.7 | No full-corpus Groq calls | ☐ | |

---

## 9. Decisions recorded this phase

| DEC ID | Title | Accepted? |
|---|---|---|
| DEC-005 | Max 5 themes | ☐ |
| DEC-006 | Segments inferred | ☐ |
| | Groq batch size / quota | ☐ |

---

## 10. Issues and follow-ups

| ID | Issue | Severity | Resolution |
|---|---|---|---|
| | | | |

---

## 11. Sign-off

**Phase 3 complete:** ☐ Yes — proceed to [Phase 4](../phase-4/implementationplan.md)

**Notes:**
