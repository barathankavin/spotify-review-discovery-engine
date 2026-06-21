from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

from src.ingestion.fetch import fetch_reviews, save_raw_snapshot
from src.ingestion.normalize import date_range, normalize_reviews
from src.ingestion.schema import NormalizedReview

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "normalized_reviews.json"
DEFAULT_RAW_SNAPSHOT = PROJECT_ROOT / "data" / "raw" / "play_store_reviews_snapshot.json"


def _merge_stats(*counters: Counter[str]) -> Counter[str]:
    merged: Counter[str] = Counter()
    for counter in counters:
        merged.update(counter)
    return merged


def run_ingestion(
    output_path: Path | None = None,
    lookback_weeks: int | None = None,
    min_word_count: int | None = None,
    save_raw: bool = False,
) -> tuple[list[NormalizedReview], Counter[str]]:
    output_path = output_path or DEFAULT_OUTPUT
    min_words = min_word_count or int(os.getenv("MIN_WORD_COUNT", "6"))
    weeks = lookback_weeks or int(os.getenv("LOOKBACK_WEEKS", "10"))

    raw_reviews, fetch_stats = fetch_reviews(lookback_weeks=weeks)
    if save_raw:
        save_raw_snapshot(raw_reviews, str(DEFAULT_RAW_SNAPSHOT))

    normalized, norm_stats = normalize_reviews(raw_reviews, min_word_count=min_words)
    stats = _merge_stats(fetch_stats, norm_stats)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [review.to_dict() for review in normalized]
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    min_date, max_date = date_range(normalized)
    stats["date_min"] = min_date or ""
    stats["date_max"] = max_date or ""

    return normalized, stats


def print_report(stats: Counter[str], output_path: Path) -> None:
    print("\n=== Ingestion Report ===")
    print(f"Output: {output_path}")
    print(f"Raw fetched:           {stats.get('raw_fetched', 0)}")
    print(f"Malformed skipped:     {stats.get('malformed_skipped', 0)}")
    print(f"Fetch errors:          {stats.get('fetch_errors', 0)}")
    print(f"Dropped (too short):   {stats.get('dropped_too_short', 0)}")
    print(f"Dropped (emoji-only):  {stats.get('dropped_emoji_only', 0)}")
    print(f"Dropped (non-English): {stats.get('dropped_non_english', 0)}")
    print(f"Dropped (duplicate):   {stats.get('dropped_duplicate', 0)}")
    print(f"Normalized count:      {stats.get('normalized_count', 0)}")
    print(f"Date range:            {stats.get('date_min')} -> {stats.get('date_max')}")
    print("========================\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest and normalize Play Store reviews.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path for normalized_reviews.json",
    )
    parser.add_argument(
        "--lookback-weeks",
        type=int,
        default=None,
        help="Weeks of reviews to retain (default: LOOKBACK_WEEKS env or 10)",
    )
    parser.add_argument(
        "--min-word-count",
        type=int,
        default=None,
        help="Minimum word count for review body (default: 6)",
    )
    parser.add_argument(
        "--save-raw",
        action="store_true",
        help="Save pre-normalization snapshot under data/raw/",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    args = build_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    try:
        reviews_list, stats = run_ingestion(
            output_path=args.output,
            lookback_weeks=args.lookback_weeks,
            min_word_count=args.min_word_count,
            save_raw=args.save_raw,
        )
    except Exception as exc:
        logging.error("Ingestion failed: %s", exc)
        return 1

    print_report(stats, args.output)

    if not reviews_list:
        logging.error("No reviews normalized — check network, package name, or filters.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
