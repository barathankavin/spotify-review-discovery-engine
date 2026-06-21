"""Stratified sampling for Groq analysis."""

from __future__ import annotations

import random
from dataclasses import dataclass

from src.analysis.tags import is_discovery_candidate, iso_week, rating_tier
from src.ingestion.schema import NormalizedReview


CELL_CAPS = {
    ("negative", True): 15,
    ("neutral", True): 8,
    ("positive", True): 5,
    ("negative", False): 3,
    ("neutral", False): 1,
    ("positive", False): 1,
}


@dataclass
class SampleResult:
    reviews: list[NormalizedReview]
    seed: int
    total_cap: int
    cell_counts: dict[str, int]


def stratified_sample(
    reviews: list[NormalizedReview],
    total_cap: int = 450,
    seed: int = 42,
) -> SampleResult:
    rng = random.Random(seed)
    buckets: dict[tuple[str, bool, str], list[NormalizedReview]] = {}

    for review in reviews:
        disc = is_discovery_candidate(review.body)
        tier = rating_tier(review.rating)
        week = iso_week(review.date)
        key = (tier, disc, week)
        buckets.setdefault(key, []).append(review)

    for items in buckets.values():
        rng.shuffle(items)

    selected: list[NormalizedReview] = []
    cell_counts: dict[str, int] = {}

    keys_sorted = sorted(
        buckets.keys(),
        key=lambda k: (
            0 if k[0] == "negative" and k[1] else 1 if k[1] else 2,
            k[2],
        ),
    )

    for tier, disc, week in keys_sorted:
        cap = CELL_CAPS.get((tier, disc), 1)
        pool = buckets[(tier, disc, week)]
        take = min(cap, len(pool))
        if take:
            chunk = pool[:take]
            selected.extend(chunk)
            label = f"{tier}|disc={disc}|{week}"
            cell_counts[label] = take

    rng.shuffle(selected)
    if len(selected) > total_cap:
        selected = selected[:total_cap]

    return SampleResult(
        reviews=selected,
        seed=seed,
        total_cap=total_cap,
        cell_counts=cell_counts,
    )


def discovery_subset(
    reviews: list[NormalizedReview],
    cap: int = 300,
) -> list[NormalizedReview]:
    scoped = [r for r in reviews if is_discovery_candidate(r.body)]
    if len(scoped) <= cap:
        return scoped
    return scoped[:cap]
