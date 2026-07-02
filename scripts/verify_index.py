"""Verify Chroma index count matches normalized_reviews.json (CI gate)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.embeddings.store import ReviewVectorStore
from src.ops.ensure_vector_store import _count_pending

REVIEWS_PATH = ROOT / "data" / "processed" / "normalized_reviews.json"


def main() -> int:
    if not REVIEWS_PATH.exists():
        print(f"Missing {REVIEWS_PATH}")
        return 1

    reviews = json.loads(REVIEWS_PATH.read_text(encoding="utf-8"))
    n_reviews = len(reviews)
    store = ReviewVectorStore()
    n_index = store.count()
    pending = _count_pending(REVIEWS_PATH, store)

    print(f"Corpus reviews:  {n_reviews:,}")
    print(f"Indexed vectors: {n_index:,}")
    print(f"Pending embed:   {pending:,}")

    if n_index == 0:
        print("FAIL: vector store is empty after embed step")
        return 1
    if pending > 0:
        print(f"FAIL: {pending:,} reviews still not indexed — run embed before commit")
        return 1
    print("OK: search index matches corpus")
    return 0


if __name__ == "__main__":
    sys.exit(main())
