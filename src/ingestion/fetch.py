from __future__ import annotations

import hashlib
import logging
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from google_play_scraper import Sort, reviews
from google_play_scraper.exceptions import NotFoundError

logger = logging.getLogger(__name__)

DEFAULT_PACKAGE = "com.spotify.music"
DEFAULT_LOOKBACK_WEEKS = 10
DEFAULT_COUNTRY = "us"
DEFAULT_LANG = "en"
BATCH_SIZE = 200
MAX_PAGES = 500


def _review_id(raw: dict[str, Any]) -> str:
    store_id = raw.get("reviewId")
    if store_id:
        return str(store_id)
    at = raw.get("at")
    content = str(raw.get("content") or "")
    seed = f"{content}|{at}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_review(raw: dict[str, Any]) -> dict[str, Any] | None:
    try:
        content = str(raw.get("content") or "").strip()
        if not content:
            return None

        at = raw.get("at")
        if not isinstance(at, datetime):
            return None

        at = _ensure_utc(at)

        rating = int(raw.get("score", 0))
        if rating < 1 or rating > 5:
            return None

        return {
            "review_id": _review_id(raw),
            "platform": "google_play",
            "date": at.date().isoformat(),
            "rating": rating,
            "title": "",
            "body": content,
            "app_version": str(raw.get("reviewCreatedVersion") or ""),
            "thumbs_up": int(raw.get("thumbsUpCount") or 0),
            "_parsed_at": at,
        }
    except (TypeError, ValueError) as exc:
        logger.warning("Skipping malformed review row: %s", exc)
        return None


def fetch_reviews(
    package_name: str | None = None,
    lookback_weeks: int | None = None,
    country: str = DEFAULT_COUNTRY,
    lang: str = DEFAULT_LANG,
) -> tuple[list[dict[str, Any]], Counter[str]]:
    package = package_name or os.getenv("PACKAGE_NAME", DEFAULT_PACKAGE)
    weeks = lookback_weeks or int(os.getenv("LOOKBACK_WEEKS", DEFAULT_LOOKBACK_WEEKS))
    cutoff = datetime.now(timezone.utc) - timedelta(weeks=weeks)

    stats: Counter[str] = Counter()
    collected: list[dict[str, Any]] = []
    continuation_token = None
    pages = 0
    stop = False

    while pages < MAX_PAGES and not stop:
        try:
            batch, continuation_token = reviews(
                package,
                lang=lang,
                country=country,
                sort=Sort.NEWEST,
                count=BATCH_SIZE,
                continuation_token=continuation_token,
            )
        except NotFoundError as exc:
            raise RuntimeError(f"App not found: {package}") from exc
        except Exception as exc:
            stats["fetch_errors"] += 1
            logger.warning("Fetch error on page %s: %s", pages + 1, exc)
            break

        pages += 1
        if not batch:
            break

        for raw in batch:
            stats["raw_fetched"] += 1
            parsed = _parse_review(raw)
            if parsed is None:
                stats["malformed_skipped"] += 1
                continue

            review_at = parsed["_parsed_at"]
            if review_at < cutoff:
                stop = True
                continue

            collected.append(parsed)

        if continuation_token is None:
            break

    return collected, stats


def save_raw_snapshot(reviews_list: list[dict[str, Any]], path: str) -> None:
    """Optional debug snapshot without internal fields."""
    import json
    from pathlib import Path

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    payload = [{k: v for k, v in r.items() if not k.startswith("_")} for r in reviews_list]
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
