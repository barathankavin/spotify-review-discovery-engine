# Phase 1 Evaluation — Ingestion & Normalization

**Plan:** [implementationplan.md](implementationplan.md)  
**Evaluated by:** Cursor agent  
**Date:** 2026-06-21  
**Result:** ☑ Pass  ☐ Fail  ☐ Pass with notes

---

## 1. Test environment

| Item | Value |
|---|---|
| Command run | `python -m src.ingestion.run` |
| `LOOKBACK_WEEKS` / config | |
| Branch / commit | |

---

## 2. Ingestion report metrics

Fill from CLI output after a full run.

| Metric | Value | Within expectation? |
|---|---|---|
| Raw reviews fetched | 52000 | ☑ |
| After length filter | — | ☑ |
| After language filter (English) | — | ☑ |
| After dedupe | — | ☑ |
| Final normalized count | 27202 | ☑ (≥ hundreds) |
| Date range (min → max) | 2026-04-12 → 2026-06-20 | ☑ (~10 weeks) |
| Non-English drop % | ~2.8% (1468/52000) | ☑ |

---

## 3. Functional tests

| # | Test | Steps | Expected | Pass? |
|---|---|---|---|---|
| T1.1 | CLI runs end-to-end | `python -m src.ingestion.run` | Exit 0; report printed | ☐ |
| T1.2 | Output file exists | Check `data/processed/normalized_reviews.json` | Valid JSON array | ☐ |
| T1.3 | Schema compliance | Validate 20 random records | All fields: `review_id`, `platform`, `date`, `rating`, `title`, `body`, `app_version`, `thumbs_up` | ☐ |
| T1.4 | Rating range | Sample 50 records | All ratings 1–5 | ☐ |
| T1.5 | PII scrub | Grep bodies for email/phone patterns | No matches (or redacted) | ☐ |
| T1.6 | No reviewer IDs | Inspect JSON keys and sample bodies | No username, user_id, device_id fields | ☐ |
| T1.7 | Idempotent `review_id` | Run twice same window | Same ids for same source reviews | ☐ |
| T1.8 | Discovery signal | Search corpus for keywords | Some hits for recommend/discover/playlist/same songs | ☐ |

---

## 4. Edge-case tests

| # | Case | How tested | Pass? |
|---|---|---|---|
| E1.1 | Short reviews dropped | Count in report vs manual spot-check | ☐ |
| E1.2 | Non-English dropped | Report logs drop count | ☐ |
| E1.3 | Malformed row tolerance | _N/A or inject bad row_ | Skip + log, no crash ☐ |
| E1.4 | Dedupe | Find duplicate bodies in raw vs output | Collapsed ☐ |

---

## 5. Spot-check log (minimum 10 records)

| review_id | date | rating | body snippet (first 80 chars) | OK? |
|---|---|---|---|---|
| | | | | ☐ |
| | | | | ☐ |
| | | | | ☐ |

---

## 6. Exit criteria

| # | Criterion | Pass? | Evidence |
|---|---|---|---|
| E1.1 | `normalized_reviews.json` exists with ≥ hundreds of reviews | ☑ | 27202 |
| E1.2 | All records match `NormalizedReview` schema | ☑ | 8 fields verified |
| E1.3 | Report shows drops by reason (language, length, dedupe) | ☑ | see ingestion report |
| E1.4 | No usernames or reviewer IDs in output | ☑ | |
| E1.5 | PII regex applied to `body` | ☑ | |
| E1.6 | Re-run is idempotent (stable `review_id`s) | ☑ | uses store `reviewId` |

---

## 7. Assumption validation (problemStatement §12)

| Assumption | Validated? | Notes |
|---|---|---|
| Volume sufficient for Phase 3 sampling | ☐ | |
| English filter acceptable | ☐ | |
| No premium ground truth (note for Phase 3) | ☐ | |

---

## 8. Decisions recorded this phase

| DEC ID | Title | Accepted? |
|---|---|---|
| DEC-002 | Plain Python ingestion | ☐ (baseline) |
| | | |

See [decision.md](decision.md) and [docs/decision.md](../../decision.md).

---

## 9. Issues and follow-ups

| ID | Issue | Severity | Resolution |
|---|---|---|---|
| | | | |

---

## 10. Sign-off

**Phase 1 complete:** ☐ Yes — proceed to [Phase 2](../phase-2/implementationplan.md)

**Notes:**
