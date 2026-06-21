"""Groq analysis pipeline — Stages A through D."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.analysis.groq_client import AnalysisGroqClient
from src.analysis.sampler import SampleResult, discovery_subset, stratified_sample
from src.analysis.tags import rating_tier, segment_hints
from src.analysis.validators import validate_themes, validate_unmet_needs
from src.config import (
    ANALYSIS_BATCH_SIZE,
    ANALYSIS_SAMPLE_CAP,
    PROCESSED_DIR,
    UNMET_NEEDS_SAMPLE_CAP,
)
from src.ingestion.schema import NormalizedReview

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v1"
SCOPE_SYSTEM = (
    "You analyze Spotify Play Store reviews about music DISCOVERY and RECOMMENDATIONS only. "
    "Ignore crashes, login, billing-only complaints unless they directly affect finding music. "
    "Respond with valid JSON only. Never invent review text. Cite only review_ids from input."
)


def review_payload(review: NormalizedReview) -> dict[str, Any]:
    return {
        "review_id": review.review_id,
        "rating": review.rating,
        "date": review.date,
        "body": review.body,
    }


def batch_reviews(reviews: list[NormalizedReview], size: int) -> list[list[NormalizedReview]]:
    return [reviews[i : i + size] for i in range(0, len(reviews), size)]


def stage_a_discover_themes(
    client: AnalysisGroqClient,
    sample: list[NormalizedReview],
    batch_size: int,
) -> list[dict]:
    batch_findings: list[dict] = []
    for batch in batch_reviews(sample, batch_size):
        payload = [review_payload(r) for r in batch]
        result = client.chat_json(
            SCOPE_SYSTEM,
            (
                "From these reviews, identify discovery/recommendation pain themes. "
                'Return JSON: {"batch_themes":[{"label":"...","description":"...",'
                '"review_ids":["..."]}]} with 0-3 themes max per batch.'
                f"\n\nReviews:\n{json.dumps(payload, ensure_ascii=False)}"
            ),
        )
        batch_findings.extend(result.get("batch_themes", []))

    merge_input = json.dumps(batch_findings, ensure_ascii=False)
    merged = client.chat_json(
        SCOPE_SYSTEM,
        (
            "Consolidate these batch-level discovery/recommendation themes into AT MOST 5 themes. "
            'Return JSON: {"themes":[{"theme_id":"t1","label":"...","description":"...",'
            '"supporting_review_ids":["..."]}]}. '
            "Use only review_ids that appeared in batch data. Scope: discovery & recommendations only."
            f"\n\nBatch themes:\n{merge_input}"
        ),
    )
    return merged.get("themes", [])


def stage_b_summaries(
    client: AnalysisGroqClient,
    themes: list[dict],
    corpus: dict[str, NormalizedReview],
) -> list[dict]:
    enriched = []
    for theme in themes:
        rids = theme.get("supporting_review_ids", [])
        excerpts = [
            review_payload(corpus[rid])
            for rid in rids
            if rid in corpus
        ][:25]
        result = client.chat_json(
            SCOPE_SYSTEM,
            (
                f"Theme: {theme.get('label')}\n"
                f"Description: {theme.get('description')}\n\n"
                "Write a PM-readable summary (MAX 250 words) and exactly 3 verbatim quotes from the reviews. "
                'Return JSON: {"summary":"...","quotes":[{"review_id":"...","text":"exact substring"}]}'
                f"\n\nReviews:\n{json.dumps(excerpts, ensure_ascii=False)}"
            ),
        )
        enriched.append(
            {
                **theme,
                "summary": result.get("summary", ""),
                "quotes": result.get("quotes", []),
                "word_count": len(result.get("summary", "").split()),
            }
        )
    return enriched


def stage_c_unmet_needs(
    client: AnalysisGroqClient,
    subset: list[NormalizedReview],
    batch_size: int,
) -> list[dict]:
    batch_needs: list[dict] = []
    for batch in batch_reviews(subset, batch_size):
        payload = [review_payload(r) for r in batch]
        result = client.chat_json(
            SCOPE_SYSTEM,
            (
                "Extract unmet needs using language like 'I wish', 'I want', 'why can't', 'bring back'. "
                'Return JSON: {"needs":[{"statement":"...","review_ids":["..."]}]} max 3 per batch.'
                f"\n\nReviews:\n{json.dumps(payload, ensure_ascii=False)}"
            ),
        )
        batch_needs.extend(result.get("needs", []))

    merged = client.chat_json(
        SCOPE_SYSTEM,
        (
            "Rank and deduplicate into AT MOST 5 unmet needs about discovery/recommendations. "
            'Return JSON: {"unmet_needs":[{"rank":1,"statement":"...",'
            '"supporting_review_ids":["..."]}]}'
            f"\n\nBatch needs:\n{json.dumps(batch_needs, ensure_ascii=False)}"
        ),
    )
    return merged.get("unmet_needs", [])


def stage_d_segments(sample: list[NormalizedReview]) -> list[dict]:
    tags = []
    for review in sample:
        hints = segment_hints(review.body)
        tags.append(
            {
                "review_id": review.review_id,
                "rating_tier": rating_tier(review.rating),
                "app_version": review.app_version,
                "inferred_segment": _infer_segment(review, hints),
                "inferred": True,
                "confidence": "heuristic",
            }
        )
    return tags


def _infer_segment(review: NormalizedReview, hints: dict[str, bool]) -> str:
    if hints["mentions_premium"]:
        return "mentions_premium"
    if hints["mentions_ads"]:
        return "mentions_ads"
    if hints["mentions_free"]:
        return "mentions_free"
    return f"rating_{rating_tier(review.rating)}"


def run_pipeline(
    reviews: list[NormalizedReview],
    seed: int = 42,
    sample_cap: int | None = None,
    unmet_cap: int | None = None,
    skip_unmet: bool = False,
) -> dict[str, Any]:
    client = AnalysisGroqClient()
    corpus = {r.review_id: r for r in reviews}

    cap = sample_cap if sample_cap is not None else ANALYSIS_SAMPLE_CAP
    unmet_limit = unmet_cap if unmet_cap is not None else UNMET_NEEDS_SAMPLE_CAP

    sample_result: SampleResult = stratified_sample(
        reviews, total_cap=cap, seed=seed
    )
    sample = sample_result.reviews
    sample_corpus = {r.review_id: r for r in sample}

    logger.info("Sample size: %s", len(sample))

    themes_raw = stage_a_discover_themes(client, sample, ANALYSIS_BATCH_SIZE)
    themes = stage_b_summaries(client, themes_raw, sample_corpus)

    theme_validation = validate_themes(themes, sample_corpus)
    if not theme_validation.ok:
        logger.warning("Theme validation issues: %s", theme_validation.errors)

    unmet_subset = discovery_subset(sample, cap=unmet_limit)
    if skip_unmet:
        unmet_needs: list[dict] = []
        unmet_validation = validate_unmet_needs(unmet_needs, sample_corpus)
    else:
        unmet_needs = stage_c_unmet_needs(client, unmet_subset, ANALYSIS_BATCH_SIZE)
        unmet_validation = validate_unmet_needs(unmet_needs, sample_corpus)

    segments = stage_d_segments(sample)

    run_metadata = {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "prompt_version": PROMPT_VERSION,
        "model_id": client.model,
        "seed": seed,
        "sample_size": len(sample),
        "unmet_subset_size": len(unmet_subset),
        "groq_call_count": client.call_count,
        "estimated_tokens": client.estimated_tokens,
        "cell_counts": sample_result.cell_counts,
        "theme_validation_ok": theme_validation.ok,
        "theme_validation_errors": theme_validation.errors,
        "unmet_validation_ok": unmet_validation.ok,
        "unmet_validation_errors": unmet_validation.errors,
    }

    return {
        "themes": themes,
        "unmet_needs": unmet_needs,
        "segments": segments,
        "run_metadata": run_metadata,
    }


def save_artifacts(result: dict[str, Any], output_dir: Path | None = None) -> None:
    out = output_dir or PROCESSED_DIR
    out.mkdir(parents=True, exist_ok=True)
    (out / "themes.json").write_text(
        json.dumps(result["themes"], indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out / "unmet_needs.json").write_text(
        json.dumps(result["unmet_needs"], indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out / "segments.json").write_text(
        json.dumps(result["segments"], indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out / "run_metadata.json").write_text(
        json.dumps(result["run_metadata"], indent=2), encoding="utf-8"
    )
