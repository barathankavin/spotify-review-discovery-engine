"""CLI: Phase 6 operations (ensure vector store, weekly refresh)."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from dotenv import load_dotenv

from src.config import PROJECT_ROOT
from src.ops.ensure_vector_store import ensure_vector_store
from src.ops.refresh import refresh


def main(argv: list[str] | None = None) -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    parser = argparse.ArgumentParser(description="Phase 6 ops: ensure store, refresh pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("ensure-store", help="Build Chroma if empty (cold-start hook)")

    refresh_p = sub.add_parser("refresh", help="Run Phases 1-3 weekly refresh")
    refresh_p.add_argument("--lookback-weeks", type=int, default=10)
    refresh_p.add_argument("--skip-ingestion", action="store_true")
    refresh_p.add_argument("--skip-embed", action="store_true")
    refresh_p.add_argument("--skip-analysis", action="store_true")
    refresh_p.add_argument(
        "--rule-baseline",
        action="store_true",
        help="Use keyword baseline instead of Groq for analysis",
    )
    refresh_p.add_argument(
        "--incremental",
        action="store_true",
        help="Fetch only reviews newer than the last collected date and merge "
        "into the existing corpus (fast, additive)",
    )
    refresh_p.add_argument(
        "--overlap-days",
        type=int,
        default=None,
        help="Incremental safety overlap in days (default: INCREMENTAL_OVERLAP_DAYS or 3)",
    )

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    try:
        if args.command == "ensure-store":
            result = ensure_vector_store()
            print(json.dumps(result, indent=2))
            return 0 if result.get("count", 0) > 0 else 1

        if args.command == "refresh":
            result = refresh(
                lookback_weeks=args.lookback_weeks,
                skip_ingestion=args.skip_ingestion,
                skip_embed=args.skip_embed,
                skip_analysis=args.skip_analysis,
                rule_baseline=args.rule_baseline,
                incremental=args.incremental,
                overlap_days=args.overlap_days,
            )
            print(json.dumps(result, indent=2))
            if not result.get("theme_validation_ok"):
                logging.warning("Theme validation did not pass — check run_metadata.json")
            return 0 if result.get("theme_validation_ok") else 1
    except Exception as exc:
        logging.error("Ops command failed: %s", exc)
        return 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
