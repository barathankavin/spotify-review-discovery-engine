# Phase 1 Corpus Analysis & Pre-LLM Strategy

**Purpose:** Understand the normalized review corpus *before* Phase 3 Groq calls so theme
discovery, summaries, and unmet-needs extraction are grounded in data shape — not guesswork.

**Data source:** `data/processed/normalized_reviews.json` (Phase 1 output)  
**Machine-readable stats:** [corpus_analysis.json](corpus_analysis.json)  
**Generated:** 2026-06-21

---

## 1. Executive summary

| Finding | Implication for LLM strategy |
|---|---|
| **27,222 reviews** over **11 weeks** — too large to send wholesale to Groq | Mandatory **stratified sample** (**~450** for Stage A on 100K TPD tier) |
| Only **~16%** match discovery/recommendation keywords explicitly | Add a **pre-LLM relevance tag**; route off-topic to an "Other" bucket |
| **41%** are 1–2★ (strong pain signal) | **Oversample negative** reviews, especially negative + discovery-scoped |
| **33%** mention premium/ads/free — often *pricing*, not discovery | Use as **segment metadata**, not as a headline theme unless tied to discovery |
| Median review length **18 words** (p90 = 62) | Batch **20–25 reviews** per Groq call is safe for TPM |
| **880** "I want" + **620** "bring back" phrases | Stage C (unmet needs) will have rich signal in a filtered subset |
| No extreme anomaly weeks detected | Weekly stratification still required so one week doesn't dominate |

**Bottom line:** Do **not** ask Groq to "find themes" in 27k raw reviews. Run a deterministic
**pre-filter → stratified sample → 4-stage pipeline** (architecture §5.3) with discovery scope
enforced in the system prompt.

---

## 2. Corpus snapshot

### 2.1 Volume and time

| Metric | Value |
|---|---|
| Total normalized reviews | 27,222 |
| Date range | 2026-04-12 → 2026-06-20 |
| ISO weeks covered | 11 |
| Avg reviews / week | ~2,475 |
| Anomaly weeks (volume spike >1.75× avg) | None flagged |

Weekly volume is stable (~2.7k–3.5k/week). Stratify by ISO week so a single week cannot
swamp theme discovery.

### 2.2 Rating distribution

| Stars | Count | % | Tier |
|---|---|---|---|
| 1★ | 8,876 | 32.6% | negative |
| 2★ | 2,273 | 8.4% | negative |
| 3★ | 2,307 | 8.5% | neutral |
| 4★ | 3,117 | 11.5% | positive |
| 5★ | 10,649 | 39.1% | positive |

| Tier | Count | % |
|---|---|---|
| Negative (≤2★) | 11,149 | 41.0% |
| Neutral (3★) | 2,307 | 8.5% |
| Positive (4–5★) | 13,766 | 50.6% |

**608** reviews are 4–5★ but contain complaint language ("hate", "bug", "fix this", etc.).
Stage A must **theme from text**, not star rating alone.

### 2.3 Text length

| Stat | Words |
|---|---|
| Median | 18 |
| 90th percentile | 62 |
| Max | 112 |

Short reviews dominate. Theme summaries should cite **verbatim quotes** (often one sentence)
rather than expecting long narratives from users.

---

## 3. Discovery / recommendation signal in the corpus

Keyword hits (not mutually exclusive — one review can match multiple):

| Signal | Reviews | % of corpus |
|---|---|---|
| playlist | 2,347 | 8.6% |
| premium / free / ads | 8,852 | 32.5% |
| recommendation | 1,072 | 3.9% |
| repetition / same songs / stuck | 604 | 2.2% |
| search / browse | 541 | 2.0% |
| personalization / For You / Daily Mix | 315 | 1.2% |
| discover (general) | 222 | 0.8% |
| Discover Weekly (explicit) | 47 | 0.2% |

**Discovery-scoped estimate** (any of: recommend, discover, playlist, algorithm, same song,
radio, search, browse, shuffle, personalization, Discover Weekly, Release Radar):

- **4,470 reviews (16.4%)** — primary pool for theme discovery sampling.

**Off-topic-only estimate** (crash, login, billing, install, CarPlay, etc. *without*
discovery keywords):

- **1,512 reviews (5.6%)** — exclude from headline themes; optional "Other" bucket.

**Negative + discovery-scoped:** **2,143 reviews** — highest-value subset for pain themes.

### 3.1 What users actually talk about (example snippets)

Real patterns from the corpus (see `corpus_analysis.json` for `review_id`s):

| Pattern | Example user language |
|---|---|
| **Algorithm / playlist injection** | *"stop injecting your music into my playlist"* |
| **Recommendation fatigue** | *"remove recommendations from liked songs"* |
| **Repetition / shuffle** | *"same issue over and over… can't turn off Shuffle"* |
| **Premium gating discovery** | *"can't rewind the same song… without buying premium"* |
| **Search friction** | *"can't even search anything"* after premium |
| **Positive discovery** | *"Discover Weekly reads my mind"* (5★ — still valid signal) |

Premium/ads complaints often **overlap** discovery (e.g. skip limits, shuffle, search) —
themes should describe the **discovery behavior**, not just "premium bad."

---

## 4. Unmet-needs language (Stage C preview)

| Phrase pattern | Count | Use in Stage C |
|---|---|---|
| "I want" | 880 | Primary unmet-needs scan |
| "bring back" / "used to" | 620 | Regression / feature-removal needs |
| "I wish" | 196 | Wish-statement clustering |
| "why can't" | 72 | Friction statements |
| "please add" / "should add" | 75 | Feature requests |

Run Stage C on the **same stratified sample** (or discovery-scoped subset) with explicit
instruction to extract only statements traceable to review text.

---

## 5. Recommended pre-LLM pipeline (before any Groq call)

```
normalized_reviews.json (27,222)
        │
        ▼
Step 0 — Deterministic tags (no LLM)
  • rating_tier: negative | neutral | positive
  • iso_week
  • discovery_candidate: bool (regex, see §5.1)
  • off_topic: bool (optional)
  • segment_hints: premium_mention, ads_mention, free_trial_mention (regex)
        │
        ▼
Step 1 — Stratified sample (~450 for Stage A; ~300 for Stage C subset)
  • Cells: rating_tier × iso_week
  • Caps per cell (see §5.2)
  • Oversample: discovery_candidate AND negative
        │
        ▼
Step 2 — Groq Stage A: discover ≤5 themes (JSON + review_ids)
        │
        ▼
Step 3 — Groq Stage B: per theme ≤250w summary + 3 verbatim quotes
        │
        ▼
Step 4 — Groq Stage C: ranked unmet needs (~5 max)
        │
        ▼
Step 5 — Stage D: segment tags (rules first; optional Groq label)
        │
        ▼
Validators → themes.json, unmet_needs.json, segments.json
```

### 5.1 Discovery candidate regex (Step 0)

Use the same scope as analysis script (`scripts/phase1_corpus_analysis.py`):

```
recommend | discover | playlist | algorithm | same song | radio |
search | browse | shuffle | personaliz | for you | daily mix |
discover weekly | release radar
```

Reviews that fail this filter should **not** drive headline themes (route to "Other" or
exclude from Stage A input).

### 5.2 Recommended sample caps

Target **~450 reviews** for Stage A (locked for `llama-3.3-70b-versatile` at **100K TPD**).
Stage C runs on **~300** discovery-scoped reviews from the same pool.

| Cell priority | Rule | Suggested cap / cell |
|---|---|---|
| **P1** | negative + discovery_candidate | up to **15** |
| **P2** | neutral + discovery_candidate | up to **8** |
| **P3** | positive + discovery_candidate | up to **5** |
| **P4** | negative + NOT discovery (fill gaps) | up to **3** |
| **P5** | neutral/positive non-discovery | up to **1** |

- **33** tier×week cells exist; not all fill to cap → actual sample ≈ **400–500**.
- Use fixed **random seed** (log in `run_metadata.json`).
- **Never exceed 500 reviews** in Stage A on the 100K TPD free tier.

### 5.3 What to send Groq per review (minimal payload)

Keep tokens low — send only:

```json
{
  "review_id": "...",
  "rating": 3,
  "date": "2026-06-20",
  "body": "..."
}
```

Do **not** send: usernames, app version (unless Stage D), thumbs_up, or full corpus metadata.

---

## 6. Theme generation strategy (Stage A → B)

### 6.1 Stage A — Theme discovery

**Input:** Stratified sample (~450 reviews), JSON array.  
**Prompt intent:**

- "Identify **at most 5** themes about **music discovery and recommendations** only."
- "Each theme must cite **supporting review_ids** from the input."
- "If a review is about crashes, login, or billing only, ignore it."
- "Do not invent themes about premium/pricing unless the text ties to discovery behavior
  (shuffle, skips, search, recommendations)."

**Expected themes from data** (labels emerge from LLM — these are *hypotheses* to validate):

| # | Likely theme (from corpus) | Evidence strength |
|---|---|---|
| 1 | **Playlist / library injection** — unwanted songs in user playlists | Strong (playlist + recommendation keywords) |
| 2 | **Recommendation quality** — bad or irrelevant suggestions | Strong (1,072 recommendation hits) |
| 3 | **Repetition / shuffle / stuck in a loop** | Moderate (604 repetition hits) |
| 4 | **Search & browse friction** | Moderate (541 search/browse) |
| 5 | **Personalization / For You / Daily Mix** | Moderate (315 personalization hits) |

Discover Weekly may appear as a **sub-quote** within personalization/recommendation themes
(only 47 explicit mentions — too sparse for its own headline theme unless Stage A merges).

### 6.2 Stage B — Summary + quotes (per theme)

For each theme from Stage A:

1. Pull **only** reviews whose `review_id` was listed in Stage A for that theme.
2. Ask Groq for:
   - **≤250-word narrative** (PM-readable, no jargon)
   - **Exactly 3 verbatim quotes** (substring match required by validator)
   - Word count enforced post-hoc

**Summary style guidance:**

- Lead with **what users are trying to do** ("find new music", "control my playlists").
- Describe **failure mode** in user language.
- Note **free vs premium** only when reviews explicitly link them to discovery.
- End with **frequency cue** ("commonly mentioned among 1–2★ reviews this period") — only if
  supported by cited ids.

### 6.3 Stage C — Unmet needs

Scan sample for wish/future/regression language. Rank by frequency in sample:

- Pre-filter bodies containing: `i wish`, `i want`, `why can't`, `bring back`, `please add`.
- Cluster into **≤5 ranked needs**, each with supporting `review_id`s.
- Do not generalize beyond cited text.

### 6.4 Stage D — Segments (mostly rules)

| Segment hint | Rule |
|---|---|
| `rating_negative` | ≤2★ |
| `rating_neutral` | 3★ |
| `rating_positive` | 4–5★ |
| `mentions_premium` | /premium|subscription/i |
| `mentions_ads` | /ads?\b/i |
| `mentions_free` | /free trial|can't afford/i |

Optional Groq pass: one-line **inferred** segment label per theme cluster — always marked
"inferred, not verified" in UI.

---

## 7. Groq call budget estimate (Phase 3)

Confirmed limits: **30 RPM · 1K RPD · 12K TPM · 100K TPD** (`llama-3.3-70b-versatile`).

| Stage | Calls (approx.) | Est. tokens |
|---|---|---|
| A — Theme discovery | 23 | ~37K |
| B — Summaries | 5 | ~10K |
| C — Unmet needs | 15 | ~24K |
| D — Segments | 0–1 | ~0–2K |
| Chatbot reserve | — | ~15–20K |
| **Total** | **~43–44** | **~86–93K** |

Pacing: **2.5 s** sleep between calls; **10 s** backoff on TPM 429; checkpoint every batch.

---

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Themes drift to premium/pricing (32% of corpus) | Pre-filter discovery_candidate; prompt scope; max 5 themes |
| LLM invents quotes | Provenance validator (substring match on corpus) |
| One week dominates | ISO week caps in sampler |
| 5★ praise dilutes pain themes | Oversample negative + discovery; theme from text |
| Discover Weekly underrepresented | Allow as sub-theme under personalization/recommendations |
| Off-topic bugs in themes | "Other" bucket excluded from dashboard headline |

---

## 9. Checklist before implementing Phase 3

- [ ] Run `scripts/phase1_corpus_analysis.py` after each Phase 1 refresh
- [ ] Implement Step 0 deterministic tags in `src/analysis/sampler.py`
- [ ] Lock sample seed + caps in `run_metadata.json`
- [ ] Verify Groq rate limits at console.groq.com/docs/rate-limits
- [ ] Stage A prompt scoped to discovery/recommendations only
- [ ] Validators: ≤5 themes, ≤250w, quote provenance, PII scan

---

## 10. Related documents

| Document | Role |
|---|---|
| [implementationplan.md](implementationplan.md) | Phase 1 ingestion spec |
| [eval.md](eval.md) | Phase 1 exit criteria |
| [../phase-3/implementationplan.md](../phase-3/implementationplan.md) | Groq Stages A–D implementation |
| [../../architecture.md](../../architecture.md) §5.3 | Analysis architecture |
| [corpus_analysis.json](corpus_analysis.json) | Raw stats from this analysis |
