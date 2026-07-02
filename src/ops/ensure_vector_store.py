"""Ensure Chroma vector store exists (Phase 6 cold-start hook)."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from src.config import PROCESSED_DIR, PROJECT_ROOT
from src.embeddings.persist_dir import (
    committed_chroma_dir,
    is_streamlit_cloud,
    resolve_chroma_persist_dir,
    runtime_embed_enabled,
)
from src.embeddings.run import load_reviews, run_embed_all
from src.embeddings.store import (
    CHECKPOINT_PATH,
    ReviewVectorStore,
    compose_document,
    content_hash,
)

logger = logging.getLogger(__name__)

DEFAULT_REVIEWS = PROCESSED_DIR / "normalized_reviews.json"


def _checkpoint_corpus_count() -> int | None:
    if not CHECKPOINT_PATH.exists():
        return None
    try:
        data = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
        total = data.get("total_input")
        return int(total) if total is not None else None
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None


def _count_pending(reviews_path: Path, store: ReviewVectorStore) -> int:
    """Full hash-level pending count (used in CI; avoid on Streamlit hot path)."""
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


def _fast_pending(corpus_count: int, index_count: int) -> int:
    """O(1) estimate: enough when index covers the whole corpus."""
    if index_count <= 0:
        return corpus_count
    if index_count >= corpus_count:
        return 0
    return corpus_count - index_count


def _cloud_ready_status(store: ReviewVectorStore, corpus_count: int) -> dict:
    count = store.count()
    pending = _fast_pending(corpus_count, count)
    checkpoint_total = _checkpoint_corpus_count()
    synced = pending == 0 and (
        count >= corpus_count
        or (checkpoint_total is not None and checkpoint_total == corpus_count)
    )
    out = {
        "action": "ready",
        "count": count,
        "corpus_count": corpus_count,
        "persist_dir": str(store.persist_dir),
        "source": "committed_ci_index",
    }
    if not synced and corpus_count > count:
        out["warning"] = (
            f"Search index has {count:,} of {corpus_count:,} reviews. "
            "Run the weekly refresh workflow to rebuild the committed index."
        )
        out["pending_estimate"] = corpus_count - count
    return out


def ensure_vector_store(
    reviews_path: Path | None = None,
    persist_dir: Path | None = None,
    batch_size: int | None = None,
) -> dict:
    """
    Make the vector store reflect the current normalized_reviews.json.

    On Streamlit Cloud (default): use the committed CI index read-only — no copy,
    no runtime embed. Locally: incremental upsert when reviews are new/changed.
    """
    load_dotenv(PROJECT_ROOT / ".env")
    reviews_path = reviews_path or DEFAULT_REVIEWS
    corpus_count = len(load_reviews(reviews_path)) if reviews_path.exists() else 0

    # Streamlit Cloud: trust the weekly CI commit; skip tmp seed + heavy hash scan.
    if is_streamlit_cloud() and not runtime_embed_enabled():
        read_dir = persist_dir or committed_chroma_dir()
        store = ReviewVectorStore(persist_dir=read_dir)
        if store.count() == 0:
            raise FileNotFoundError(
                "Committed search index is empty. Run the weekly refresh workflow "
                "so CI can commit vector_store/."
            )
        return _cloud_ready_status(store, corpus_count)

    persist_dir = persist_dir or resolve_chroma_persist_dir(writable=True)
    batch_size = batch_size or int(os.getenv("EMBED_BATCH_SIZE", "128"))
    if is_streamlit_cloud():
        batch_size = min(batch_size, int(os.getenv("EMBED_BATCH_SIZE_CLOUD", "32")))

    store = ReviewVectorStore(persist_dir=persist_dir)
    count = store.count()

    if count > 0:
        if not reviews_path.exists():
            logger.info("Vector store ready (%s vectors)", count)
            return {
                "action": "ready",
                "count": count,
                "corpus_count": corpus_count,
                "persist_dir": str(persist_dir),
            }
        pending = _fast_pending(corpus_count, count)
        if pending == 0:
            logger.info("Vector store ready (%s vectors, corpus %s)", count, corpus_count)
            return {
                "action": "ready",
                "count": count,
                "corpus_count": corpus_count,
                "persist_dir": str(persist_dir),
            }
        # Exact pending only when a local incremental embed is worth doing.
        if not is_streamlit_cloud():
            pending = _count_pending(reviews_path, store)
            if pending == 0:
                return {
                    "action": "ready",
                    "count": count,
                    "corpus_count": corpus_count,
                    "persist_dir": str(persist_dir),
                }
        logger.info("Vector store has ~%s pending reviews — embedding", pending)
        try:
            stats = run_embed_all(reviews_path, batch_size, persist_dir)
        except Exception as exc:
            logger.exception("Incremental embed failed — continuing with existing index")
            return {
                "action": "ready_degraded",
                "count": count,
                "corpus_count": corpus_count,
                "pending_skipped": pending,
                "warning": (
                    "Could not update the search index on this host; chat uses the "
                    f"existing {count:,} indexed reviews."
                ),
                "error": str(exc)[:200],
                "persist_dir": str(persist_dir),
            }
        return {
            "action": "updated",
            "count": ReviewVectorStore(persist_dir).count(),
            "corpus_count": corpus_count,
            "newly_embedded": stats.get("newly_embedded", 0),
            "duration_seconds": stats.get("duration_seconds"),
            "persist_dir": str(persist_dir),
        }

    if not reviews_path.exists():
        raise FileNotFoundError(
            f"Vector store empty and {reviews_path} not found. Run Phase 1 ingestion."
        )

    logger.info("Vector store empty — embedding from %s", reviews_path)
    try:
        stats = run_embed_all(reviews_path, batch_size, persist_dir)
    except Exception as exc:
        logger.exception("Full embed failed")
        raise RuntimeError(
            "Search index could not be built on this host. "
            "Try rebooting the app or run the weekly refresh workflow."
        ) from exc
    new_count = ReviewVectorStore(persist_dir).count()
    return {
        "action": "rebuilt",
        "count": new_count,
        "corpus_count": corpus_count,
        "newly_embedded": stats.get("newly_embedded", 0),
        "duration_seconds": stats.get("duration_seconds"),
        "persist_dir": str(persist_dir),
    }
