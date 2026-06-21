# Phase 4 Evaluation — Streamlit Dashboard

**Plan:** [implementationplan.md](implementationplan.md)  
**Evaluated by:** _name_  
**Date:** _YYYY-MM-DD_  
**Result:** ☐ Pass  ☐ Fail  ☐ Pass with notes

---

## 1. Test environment

| Item | Value |
|---|---|
| Command | `streamlit run src/dashboard/app.py` |
| Browser | |
| Phase 3 artifacts present | ☐ Yes |
| Branch / commit | |

---

## 2. Tab smoke tests

| # | Tab | Action | Expected | Pass? |
|---|---|---|---|---|
| T4.1 | Overview | Open app | Loads without error; charts visible | ☐ |
| T4.2 | Overview | Check theme chart | ≤5 themes shown | ☐ |
| T4.3 | Overview | Trend / anomaly | At least one trend view; anomaly flag if applicable | ☐ |
| T4.4 | Overview | Run metadata | Sample size, model, date visible | ☐ |
| T4.5 | Theme Deep-Dive | Select each theme | Summary + quotes render | ☐ |
| T4.6 | Theme Deep-Dive | Word count | Each summary ≤250 words | ☐ |
| T4.7 | Segments | Open tab | Disclaimer banner visible | ☐ |
| T4.8 | Segments | Read disclaimer | Contains "inferred" and "not verified" | ☐ |
| T4.9 | Unmet Needs | Open tab | Ranked list in order | ☐ |
| T4.10 | Unmet Needs | Quotes | Supporting quotes per item | ☐ |

---

## 3. Privacy and constraint tests

| # | Test | Steps | Pass? |
|---|---|---|---|
| T4.11 | No PII in UI | Scan all tabs for email/phone patterns | ☐ |
| T4.12 | No reviewer identity | Confirm only internal `review_id` shown | ☐ |
| T4.13 | 250w render guard | If summary at limit in JSON | Displays without exceeding cap ☐ |

---

## 4. Failure-mode tests

| # | Test | Steps | Expected | Pass? |
|---|---|---|---|---|
| T4.14 | Missing `themes.json` | Rename file temporarily | Clear error or last-known-good + warning | ☐ |
| T4.15 | Invalid JSON | Corrupt file temporarily | No uncaught exception; user message | ☐ |
| T4.16 | Last-known-good | Restore backup artifact path | Dashboard shows backup with warning | ☐ |

---

## 5. Exit criteria

| # | Criterion | Pass? | Evidence |
|---|---|---|---|
| E4.1 | `streamlit run` launches locally | ☐ | |
| E4.2 | Four tabs functional with Phase 3 data | ☐ | |
| E4.3 | Theme summaries ≤250 words in UI | ☐ | |
| E4.4 | Segment disclaimer visible | ☐ | |
| E4.5 | No reviewer-identifying fields | ☐ | |
| E4.6 | Theme distribution + ≥1 trend chart | ☐ | |
| E4.7 | Graceful missing-artifact handling | ☐ | |

---

## 6. Decisions recorded this phase

| DEC ID | Title | Accepted? |
|---|---|---|
| DEC-006 | Segments inferred disclaimer | ☐ |
| | Chart library choice | ☐ |
| | Last-known-good path | ☐ |

---

## 7. UI checklist (optional screenshots)

| Tab | Screenshot / notes | OK? |
|---|---|---|
| Overview | | ☐ |
| Theme Deep-Dive | | ☐ |
| Segments | | ☐ |
| Unmet Needs | | ☐ |

---

## 8. Issues and follow-ups

| ID | Issue | Severity | Resolution |
|---|---|---|---|
| | | | |

---

## 9. Sign-off

**Phase 4 complete:** ☐ Yes — proceed to [Phase 5](../phase-5/implementationplan.md)

**Notes:**
