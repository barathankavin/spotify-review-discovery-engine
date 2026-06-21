# Phase 0 Decisions — Repo Scaffold

Cross-cutting baseline decisions: [docs/decision.md](../../decision.md).

Record **phase-0-specific** decisions below. Copy the template for each entry; when
accepted, add a row to the index in `docs/decision.md`.

---

## Template

### DEC-0XX — Title

| Field | Value |
|---|---|
| **Status** | Proposed / Accepted / Superseded |
| **Date** | |
| **Category** | Tech / Business / Ops |

**Context:**

**Decision:**

**Alternatives considered:**

**Consequences:**

---

## Decisions

### DEC-007 — Python version and venv tooling

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | |
| **Category** | Tech |

**Context:** Phase 0 requires a supported Python for all dependencies.

**Decision:** _e.g. Python 3.11.x via `python -m venv .venv`_

**Alternatives considered:** pyenv; conda; 3.12 if all wheels available.

**Consequences:** Document in README or eval.md for other contributors.

---

### DEC-008 — Dependency pinning strategy

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | |
| **Category** | Tech |

**Context:** Unpinned `requirements.txt` can break reproducibility across machines.

**Decision:** _e.g. minimum versions only vs fully pinned with `pip freeze`_

**Alternatives considered:** poetry/uv lockfile.

**Consequences:** Affects CI and Streamlit Cloud deploy reproducibility.

---

## Index (this phase)

| ID | Title | Status |
|---|---|---|
| DEC-007 | Python version and venv tooling | Proposed |
| DEC-008 | Dependency pinning strategy | Proposed |
