"""Ensure Chroma vector store exists (Phase 6 cold-start hook)."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from src.config import PROCESSED_DIR, PROJECT_ROOT, VECTOR_STORE_DIR
from src.embeddings.run import load_reviews, run_embed_all
from src.embeddings.store import (
    ReviewVectorStore,
    compose_document,
    content_hash,
)

logger = logging.getLogger(__name__)

DEFAULT_REVIEWS = PROCESSED_DIR / "normalized_reviews.json"


def _count_pending(reviews_path: Path, store: ReviewVectorStore) -> int:
    """Cheap check (no embedding model load) for how many reviews are new or
    changed relative to what is already stored in Chroma."""
    try:
        reviews = load_reviews(reviews_path)
    except Exception:
        return 0
    stored = store.stored_hashes()
    pending = 0
    for review in reviews:
        doc_hash = content_hash(compose_document(review))
        if stored.get(review.review_id) != doc_hash:
            pending += 1
    return pending


def ensure_vector_store(
    reviews_path: Path | None = None,
    persist_dir: Path | None = None,
    batch_size: int | None = None,
) -> dict:
    """
    Make the vector store reflect the current normalized_reviews.json.

    - Empty store  -> embed the full corpus.
    - Warm store with new/changed reviews -> embed just those (incremental upsert),
      so freshly ingested reviews become retrievable without a full rebuild.
    - Warm store, nothing pending -> ready (no embedding-model load).

    Returns a status dict with action, count, and optional embed stats.
    """
    load_dotenv(PROJECT_ROOT / ".env")
    reviews_path = reviews_path or DEFAULT_REVIEWS
    persist_dir = persist_dir or VECTOR_STORE_DIR
    batch_size = batch_size or int(os.getenv("EMBED_BATCH_SIZE", "128"))

    store = ReviewVectorStore(persist_dir=persist_dir)
    count = store.count()

    if count > 0:
        if not reviews_path.exists():
            logger.info("Vector store ready (%s vectors)", count)
            return {"action": "ready", "count": count}
        pending = _count_pending(reviews_path, store)
        if pending == 0:
            logger.info("Vector store ready (%s vectors, no new reviews)", count)
            return {"action": "ready", "count": count}
        logger.info("Vector store has %s new/changed reviews — embedding them", pending)
        stats = run_embed_all(reviews_path, batch_size, persist_dir)
        return {
            "action": "updated",
            "count": ReviewVectorStore(persist_dir).count(),
            "newly_embedded": stats.get("newly_embedded", 0),
            "duration_seconds": stats.get("duration_seconds"),
        }

    if not reviews_path.exists():
        raise FileNotFoundError(
            f"Vector store empty and {reviews_path} not found. Run Phase 1 ingestion."
        )

    logger.info("Vector store empty — embedding from %s", reviews_path)
    stats = run_embed_all(reviews_path, batch_size, persist_dir)
    new_count = ReviewVectorStore(persist_dir).count()
    return {
        "action": "rebuilt",
        "count": new_count,
        "newly_embedded": stats.get("newly_embedded", 0),
        "duration_seconds": stats.get("duration_seconds"),
    }
