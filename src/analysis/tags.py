"""Deterministic review tags (pre-LLM)."""

from __future__ import annotations

import re
from datetime import date

DISCOVERY_PATTERN = re.compile(
    r"recommend|discover|playlist|algorithm|same song|radio|search|browse|"
    r"shuffle|personaliz|for you|daily mix|discover weekly|release radar|"
    r"stuck in a loop|over and over",
    re.I,
)
PREMIUM_PATTERN = re.compile(r"premium|subscription|subscribe", re.I)
ADS_PATTERN = re.compile(r"\bads?\b", re.I)
FREE_PATTERN = re.compile(r"free trial|can't afford|cant afford|without premium", re.I)


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


def is_discovery_candidate(body: str) -> bool:
    return bool(DISCOVERY_PATTERN.search(body))


def segment_hints(body: str) -> dict[str, bool]:
    return {
        "mentions_premium": bool(PREMIUM_PATTERN.search(body)),
        "mentions_ads": bool(ADS_PATTERN.search(body)),
        "mentions_free": bool(FREE_PATTERN.search(body)),
    }
