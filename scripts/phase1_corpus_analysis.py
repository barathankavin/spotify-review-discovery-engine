"""Exploratory analysis of Phase 1 corpus for pre-LLM strategy planning."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REVIEWS_PATH = PROJECT_ROOT / "data" / "processed" / "normalized_reviews.json"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "phases" / "phase-1" / "corpus_analysis.json"

DISCOVERY_PATTERN = re.compile(
    r"recommend|discover|playlist|algorithm|same song|radio|search|browse|"
    r"shuffle|personaliz|for you|daily mix|discover weekly|release radar",
    re.I,
)
OFF_TOPIC_PATTERN = re.compile(
    r"crash|login|log in|password|billing|payment|customer service|"
    r"update broke|won.t open|install|uninstall|bluetooth|car play|android auto",
    re.I,
)
UNMET_PATTERNS = {
    "i_wish": re.compile(r"\bi wish\b", re.I),
    "i_want": re.compile(r"\bi want\b", re.I),
    "why_cant": re.compile(r"why can'?t", re.I),
    "please_add": re.compile(r"please add|should add|need to add", re.I),
    "bring_back": re.compile(r"bring back|used to", re.I),
}
KEYWORD_GROUPS = {
    "recommendation": re.compile(r"recommend", re.I),
    "discover": re.compile(r"discover", re.I),
    "playlist": re.compile(r"playlist", re.I),
    "repetition": re.compile(r"same song|same songs|repeat|over and over|stuck", re.I),
    "discover_weekly": re.compile(r"discover weekly", re.I),
    "search_browse": re.compile(r"search|browse", re.I),
    "personalization": re.compile(r"personaliz|for you|daily mix|made for me", re.I),
    "premium_free": re.compile(r"premium|subscription|free trial|ads\b|without premium", re.I),
}


def iso_week(date_str: str) -> str:
    dt = date.fromisoformat(date_str)
    y, w, _ = dt.isocalendar()
    return f"{y}-W{w:02d}"


def rating_tier(rating: int) -> str:
    if rating <= 2:
        return "negative"
    if rating == 3:
        return "neutral"
    return "positive"


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text))


def main() -> None:
    reviews = json.loads(REVIEWS_PATH.read_text(encoding="utf-8"))
    n = len(reviews)

    ratings = Counter(r["rating"] for r in reviews)
    weeks = Counter(iso_week(r["date"]) for r in reviews)
    wcs = sorted(word_count(r["body"]) for r in reviews)

    keyword_hits = {k: sum(1 for r in reviews if p.search(r["body"])) for k, p in KEYWORD_GROUPS.items()}
    on_scope = sum(1 for r in reviews if DISCOVERY_PATTERN.search(r["body"]))
    off_topic_only = sum(
        1
        for r in reviews
        if OFF_TOPIC_PATTERN.search(r["body"]) and not DISCOVERY_PATTERN.search(r["body"])
    )
    unmet = {k: sum(1 for r in reviews if p.search(r["body"])) for k, p in UNMET_PATTERNS.items()}

    tier_week = Counter((rating_tier(r["rating"]), iso_week(r["date"])) for r in reviews)
    tier_counts = Counter(rating_tier(r["rating"]) for r in reviews)

    neg = [r for r in reviews if r["rating"] <= 2]
    neg_disc = [r for r in neg if DISCOVERY_PATTERN.search(r["body"])]

    mismatch = sum(
        1
        for r in reviews
        if r["rating"] >= 4 and re.search(r"terrible|awful|worst|hate|annoy|fix this|bug", r["body"], re.I)
    )

    # Example snippets for theme planning
    examples: dict[str, list[dict]] = defaultdict(list)
    example_specs = [
        ("repetition", KEYWORD_GROUPS["repetition"]),
        ("discover_weekly", KEYWORD_GROUPS["discover_weekly"]),
        ("recommendation", KEYWORD_GROUPS["recommendation"]),
        ("search_browse", KEYWORD_GROUPS["search_browse"]),
        ("premium_free", KEYWORD_GROUPS["premium_free"]),
    ]
    for label, pattern in example_specs:
        for r in reviews:
            if pattern.search(r["body"]) and len(examples[label]) < 3:
                examples[label].append(
                    {
                        "review_id": r["review_id"],
                        "rating": r["rating"],
                        "date": r["date"],
                        "snippet": r["body"][:180],
                    }
                )

    weekly_sorted = weeks.most_common()
    avg_week = n / len(weeks)
    anomaly_weeks = [
        {"week": w, "count": c, "z_approx": round((c - avg_week) / (avg_week**0.5), 2)}
        for w, c in weekly_sorted
        if c > avg_week * 1.75
    ]

    report = {
        "total_reviews": n,
        "date_min": min(r["date"] for r in reviews),
        "date_max": max(r["date"] for r in reviews),
        "iso_weeks": len(weeks),
        "ratings": dict(sorted(ratings.items())),
        "rating_tiers": dict(tier_counts),
        "word_count": {
            "median": wcs[len(wcs) // 2],
            "p90": wcs[int(len(wcs) * 0.9)],
            "max": wcs[-1],
        },
        "keyword_hits": keyword_hits,
        "keyword_pct": {k: round(100 * v / n, 2) for k, v in keyword_hits.items()},
        "discovery_scope_estimate": {"count": on_scope, "pct": round(100 * on_scope / n, 2)},
        "off_topic_only_estimate": {"count": off_topic_only, "pct": round(100 * off_topic_only / n, 2)},
        "unmet_language": unmet,
        "negative_reviews": len(neg),
        "negative_with_discovery_signal": len(neg_disc),
        "high_star_with_complaint_language": mismatch,
        "tier_week_cells": len(tier_week),
        "cells_over_200": sum(1 for c in tier_week.values() if c > 200),
        "anomaly_weeks": anomaly_weeks,
        "top_weeks_by_volume": weekly_sorted[:5],
        "example_snippets": dict(examples),
    }

    OUTPUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
