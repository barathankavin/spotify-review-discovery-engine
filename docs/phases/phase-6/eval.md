# Phase 6 Evaluation — Deployment & Operations

**Plan:** [implementationplan.md](implementationplan.md)  
**Evaluated by:** _name_  
**Date:** _YYYY-MM-DD_  
**Result:** ☐ Pass  ☐ Fail  ☐ Pass with notes

---

## 1. Deployment record

| Item | Value |
|---|---|
| Hosting platform | |
| Live URL | |
| GitHub repo / branch | |
| Main module path | `src/dashboard/app.py` |
| Secrets configured | ☐ `GROQ_API_KEY` in platform secrets only |
| `docs/deployment_plan.md` | ☐ exists |

---

## 2. Live smoke test (all five tabs)

| # | Check | Pass? | Notes |
|---|---|---|---|
| T6.1 | App loads at public URL (no 500) | ☐ | |
| T6.2 | Overview: themes and charts | ☐ | |
| T6.3 | Theme Deep-Dive: quotes visible | ☐ | |
| T6.4 | Segments: disclaimer present | ☐ | |
| T6.5 | Unmet Needs: ranked list | ☐ | |
| T6.6 | Chatbot: grounded Q → citations | ☐ | question used: |
| T6.7 | Chatbot: out-of-scope → refusal | ☐ | question used: |
| T6.8 | No PII on any tab | ☐ | |
| T6.9 | Cold start / Chroma strategy works | ☐ | strategy: |

---

## 3. Security checks

| # | Test | Pass? |
|---|---|---|
| T6.10 | No API key in repo history / public files | ☐ |
| T6.11 | `.env` not deployed | ☐ |
| T6.12 | Logs contain no raw reviewer PII | ☐ |

---

## 4. Operations tests

| # | Test | Steps | Pass? |
|---|---|---|---|
| T6.13 | Weekly refresh doc | Follow `deployment_plan.md` steps 1–8 on paper or dry run | ☐ |
| T6.14 | Rollback | Restore previous `themes.json` backup | Dashboard shows last-good ☐ |
| T6.15 | Validation failure path | Document behavior when Phase 3 fails | No overwrite of good data ☐ |
| T6.16 | Monitoring | Confirm ingest/Groq/error logs accessible | ☐ |

---

## 5. Cold-start / Chroma verification

| Scenario | Expected | Actual | Pass? |
|---|---|---|---|
| Fresh deploy (empty disk) | Rebuild or load snapshot per DEC | | ☐ |
| Time to first chatbot answer | Acceptable for demo (<_N_ min) | | ☐ |
| Vector count after startup | Matches normalized review count | | ☐ |

---

## 6. Exit criteria

| # | Criterion | Pass? | Evidence |
|---|---|---|---|
| E6.1 | `deployment_plan.md` matches hosting strategy | ☐ | |
| E6.2 | Public deploy URL working | ☐ | URL: |
| E6.3 | Secrets only on platform | ☐ | |
| E6.4 | All five tabs pass live smoke test | ☐ | |
| E6.5 | Chroma cold-start verified | ☐ | |
| E6.6 | Weekly refresh documented | ☐ | |
| E6.7 | Rollback / last-known-good verified | ☐ | |

---

## 7. Decisions recorded this phase

| DEC ID | Title | Accepted? |
|---|---|---|
| | Hosting platform | ☐ |
| | Chroma cold-start strategy | ☐ |
| | Refresh cadence (manual vs cron) | ☐ |

---

## 8. Build completion checklist

| Milestone | Done? |
|---|---|
| Phases 0–5 eval.md all Pass | ☐ |
| Phase 6 eval Pass | ☐ |
| Stakeholder demo URL shared | ☐ |
| Recurring weekly run owner assigned | ☐ |

---

## 9. Issues and follow-ups

| ID | Issue | Severity | Resolution |
|---|---|---|---|
| | | | |

---

## 10. Sign-off

**Phase 6 complete / build done:** ☐ Yes — enter recurring weekly refresh (Phases 1→3)

**Notes:**
