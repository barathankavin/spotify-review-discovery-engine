"""Lightweight live pull of the newest Play Store reviews (UI liveness probe).

This is intentionally small and read-only: it fetches a single page of the
newest reviews so the dashboard can show that ingestion is reaching the live
source. It does NOT touch normalized_reviews.json or the vector store — the full
refresh path is src.ops.refresh.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from google_play_scraper import Sort, reviews

from src.ingestion.normalize import normalize_reviews


def fetch_latest_reviews(count: int = 12, package_name: str | None = None) -> dict:
    package = package_name or os.getenv("PACKAGE_NAME", "com.spotify.music")
    country = os.getenv("PLAY_STORE_COUNTRY", "us")
    lang = os.getenv("PLAY_STORE_LANG", "en")

    batch, _ = reviews(
        package,
        lang=lang,
        country=country,
        sort=Sort.NEWEST,
        count=count,
    )

    raw = []
    for r in batch:
        at = r.get("at")
        raw.append(
            {
                "review_id": str(r.get("reviewId") or ""),
                "platform": "google_play",
                "date": at.date().isoformat() if isinstance(at, datetime) else "",
                "rating": int(r.get("score") or 0),
                "title": "",
                "body": str(r.get("content") or "").strip(),
                "app_version": str(r.get("reviewCreatedVersion") or ""),
                "thumbs_up": int(r.get("thumbsUpCount") or 0),
            }
        )

    normalized, _ = normalize_reviews(raw, min_word_count=1)
    return {
        "fetched_at": datetime.now(timezone.utc).astimezone().strftime("%I:%M:%S %p").lstrip("0"),
        "package": package,
        "count": len(normalized),
        "reviews": [n.to_dict() for n in normalized],
    }
