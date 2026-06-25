"""On-demand AI executive summary for the analyzed corpus.

Makes a SINGLE Groq call grounded strictly in the already-computed artifacts
(themes, unmet needs, rating mix, inferred segment signals). The dashboard caches
the result per analysis run_id, so re-viewing costs zero extra tokens — a fresh
call only happens when the user clicks the button after a new data refresh.

It never invents personas, trust scores, or statistics that are not in the input.
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from src.analysis.groq_client import AnalysisGroqClient

_SYSTEM = (
    "You are a product research analyst summarizing analysis of Spotify Play Store "
    "reviews about music DISCOVERY and RECOMMENDATIONS. Use ONLY the data provided "
    "(themes, unmet needs, rating-based sentiment mix, inferred segment signals). "
    "Do NOT invent persona names, trust scores, percentages, or facts that are not "
    "in the input. Be concise, concrete, and PM-readable. Return valid JSON only."
)


def _build_payload(data: Any) -> dict[str, Any]:
    reviews = data.reviews
    total = len(reviews) or 1
    tiers: Counter[str] = Counter()
    for r in reviews:
        if r.rating <= 2:
            tiers["negative"] += 1
        elif r.rating == 3:
            tiers["neutral"] += 1
        else:
            tiers["positive"] += 1

    seg_counts = Counter(s.get("inferred_segment", "unknown") for s in data.segments)

    themes = [
        {
            "label": t.get("label", ""),
            "summary": (t.get("summary") or "")[:280],
            "supporting_reviews": len(t.get("supporting_review_ids", [])),
        }
        for t in data.themes
    ]
    needs = [
        {"rank": n.get("rank"), "statement": n.get("statement", "")}
        for n in data.unmet_needs
    ][:6]

    return {
        "total_reviews": len(reviews),
        "rating_sentiment_pct": {k: round(100 * v / total, 1) for k, v in tiers.items()},
        "analysis_sample_size": data.run_metadata.get("sample_size"),
        "themes": themes,
        "unmet_needs": needs,
        "inferred_segment_signal_counts": dict(seg_counts.most_common()),
    }


def generate_executive_summary(data: Any) -> dict[str, Any]:
    """One Groq call → {summary, key_findings[], model, estimated_tokens}."""
    payload = _build_payload(data)
    client = AnalysisGroqClient()
    user = (
        "From this Spotify music-discovery review analysis, write an executive summary "
        "and key findings for a product manager.\n"
        'Return JSON exactly as: {"summary": "<2-4 sentence paragraph>", '
        '"key_findings": ["<finding>", ...]} with at most 6 key findings.\n'
        "Ground every statement in the data. Reference the negative rating share and the "
        "most-supported themes and unmet needs. Do NOT fabricate trust scores or persona "
        "names that are not present in the data.\n\n"
        f"Data:\n{json.dumps(payload, ensure_ascii=False)}"
    )
    result = client.chat_json(_SYSTEM, user, max_retries=4)
    findings = [
        str(x).strip()
        for x in (result.get("key_findings") or [])
        if str(x).strip()
    ][:6]
    return {
        "summary": str(result.get("summary", "")).strip(),
        "key_findings": findings,
        "model": client.model,
        "estimated_tokens": client.estimated_tokens,
    }
