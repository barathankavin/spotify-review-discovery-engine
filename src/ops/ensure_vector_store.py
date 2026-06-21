"""Ensure Chroma vector store exists (Phase 6 cold-start hook)."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from src.config import PROCESSED_DIR, PROJECT_ROOT, VECTOR_STORE_DIR
from src.embeddings.run import run_embed_all
from src.embeddings.store import ReviewVectorStore

logger = logging.getLogger(__name__)

DEFAULT_REVIEWS = PROCESSED_DIR / "normalized_reviews.json"


def ensure_vector_store(
    reviews_path: Path | None = None,
    persist_dir: Path | None = None,
    batch_size: int | None = None,
) -> dict:
    """
    Build the vector store if empty or missing.
    Returns a status dict with action, count, and optional embed stats.
    """
    load_dotenv(PROJECT_ROOT / ".env")
    reviews_path = reviews_path or DEFAULT_REVIEWS
    persist_dir = persist_dir or VECTOR_STORE_DIR
    batch_size = batch_size or int(os.getenv("EMBED_BATCH_SIZE", "128"))

    store = ReviewVectorStore(persist_dir=persist_dir)
    count = store.count()
    if count > 0:
        logger.info("Vector store ready (%s vectors)", count)
        return {"action": "ready", "count": count}

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
