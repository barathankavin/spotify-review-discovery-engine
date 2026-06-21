"""CLI: Groq analysis Stages A-D."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.analysis.pipeline import run_pipeline, save_artifacts
from src.analysis.rule_baseline import run_rule_baseline
from src.config import PROCESSED_DIR, PROJECT_ROOT
from src.ingestion.schema import NormalizedReview

DEFAULT_INPUT = PROCESSED_DIR / "normalized_reviews.json"


def load_reviews(path: Path) -> list[NormalizedReview]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [NormalizedReview.from_dict(item) for item in raw]


def print_summary(result: dict) -> None:
    meta = result["run_metadata"]
    print("\n=== Analysis Report ===")
    print(f"Run ID:           {meta['run_id']}")
    print(f"Model:            {meta['model_id']}")
    print(f"Sample size:      {meta['sample_size']}")
    print(f"Groq calls:       {meta['groq_call_count']}")
    print(f"Est. tokens:      {meta['estimated_tokens']}")
    print(f"Themes found:     {len(result['themes'])}")
    for theme in result["themes"]:
        print(f"  - {theme.get('label')} ({len(theme.get('supporting_review_ids', []))} ids)")
    print(f"Unmet needs:      {len(result['unmet_needs'])}")
    print(f"Theme validation: {'PASS' if meta['theme_validation_ok'] else 'WARN'}")
    if meta.get("theme_validation_errors"):
        for err in meta["theme_validation_errors"][:5]:
            print(f"  ! {err}")
    print("=======================\n")


def main(argv: list[str] | None = None) -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    parser = argparse.ArgumentParser(description="Run Groq analysis (Phase 3).")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--sample-cap", type=int, default=None, help="Override ANALYSIS_SAMPLE_CAP")
    parser.add_argument("--unmet-cap", type=int, default=None, help="Override UNMET_NEEDS_SAMPLE_CAP")
    parser.add_argument("--skip-unmet", action="store_true", help="Skip Stage C (saves tokens)")
    parser.add_argument(
        "--rule-baseline",
        action="store_true",
        help="Keyword-based themes (no Groq) when quota exhausted",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if not args.input.exists():
        logging.error("Missing %s — run Phase 1 first", args.input)
        return 1

    try:
        reviews = load_reviews(args.input)
        if args.rule_baseline:
            result = run_rule_baseline(reviews, seed=args.seed, sample_cap=args.sample_cap)
        else:
            result = run_pipeline(
                reviews,
                seed=args.seed,
                sample_cap=args.sample_cap,
                unmet_cap=args.unmet_cap,
                skip_unmet=args.skip_unmet,
            )
        save_artifacts(result)
        print_summary(result)
        return 0
    except Exception as exc:
        logging.error("Analysis failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
