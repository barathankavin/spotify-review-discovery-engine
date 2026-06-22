"""Chroma vector store for review embeddings."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from src.config import PROCESSED_DIR, VECTOR_STORE_DIR
from src.ingestion.schema import NormalizedReview

logger = logging.getLogger(__name__)

COLLECTION_NAME = "spotify_reviews"
CHECKPOINT_PATH = PROCESSED_DIR / "embed_checkpoint.json"


def compose_document(review: NormalizedReview | dict[str, Any]) -> str:
    if isinstance(review, NormalizedReview):
        title, body = review.title, review.body
    else:
        title = str(review.get("title") or "")
        body = str(review.get("body") or "")
    text = f"{title} {body}".strip()
    return text or body


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def review_metadata(review: NormalizedReview, doc_hash: str) -> dict[str, str | int]:
    return {
        "review_id": review.review_id,
        "rating": int(review.rating),
        "date": review.date,
        "app_version": review.app_version or "",
        "content_hash": doc_hash,
    }


class ReviewVectorStore:
    def __init__(self, persist_dir: Path | None = None) -> None:
        path = str(persist_dir or VECTOR_STORE_DIR)
        Path(path).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=path)
        self.collection: Collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        return self.collection.count()

    def stored_hashes(self) -> dict[str, str]:
        """review_id -> content_hash for all vectors in the collection."""
        total = self.count()
        if total == 0:
            return {}
        mapping: dict[str, str] = {}
        offset = 0
        page_size = 5000
        while offset < total:
            result = self.collection.get(
                include=["metadatas"],
                limit=page_size,
                offset=offset,
            )
            if not result["ids"]:
                break
            for review_id, meta in zip(result["ids"], result["metadatas"]):
                if meta and meta.get("content_hash"):
                    mapping[review_id] = str(meta["content_hash"])
            offset += len(result["ids"])
        return mapping

    def get_stored_hash(self, review_id: str) -> str | None:
        try:
            result = self.collection.get(ids=[review_id], include=["metadatas"])
        except Exception:
            return None
        if not result["ids"]:
            return None
        meta = result["metadatas"][0] or {}
        return str(meta.get("content_hash") or "") or None

    def needs_embedding(self, review_id: str, doc_hash: str) -> bool:
        stored = self.get_stored_hash(review_id)
        return stored != doc_hash

    def upsert_batch(
        self,
        reviews: list[NormalizedReview],
        embeddings: list[list[float]],
        documents: list[str],
        hashes: list[str],
    ) -> None:
        if not reviews:
            return
        if not (len(reviews) == len(embeddings) == len(documents) == len(hashes)):
            raise ValueError("upsert_batch: mismatched list lengths")

        ids = [r.review_id for r in reviews]
        metadatas = [review_metadata(r, h) for r, h in zip(reviews, hashes)]
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def query(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        include_embeddings: bool = False,
    ) -> dict[str, Any]:
        include = ["documents", "metadatas", "distances"]
        if include_embeddings:
            include.append("embeddings")
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=include,
        )

    @staticmethod
    def distance_to_similarity(distance: float) -> float:
        """Chroma cosine distance -> similarity in [0, 1] (higher is more similar)."""
        return max(0.0, min(1.0, 1.0 - distance))

    def save_checkpoint(self, stats: dict[str, Any]) -> None:
        CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
        CHECKPOINT_PATH.write_text(json.dumps(stats, indent=2), encoding="utf-8")

    def load_checkpoint(self) -> dict[str, Any]:
        if not CHECKPOINT_PATH.exists():
            return {}
        return json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
