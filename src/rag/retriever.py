"""Retrieve reviews from Chroma using the Phase 2 embedding model."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from src.config import RAG_TOP_K
from src.embeddings.local_embedder import LocalEmbedder
from src.embeddings.store import ReviewVectorStore


@dataclass(frozen=True)
class RetrievedReview:
    review_id: str
    document: str
    rating: int
    date: str
    app_version: str
    similarity: float


class ReviewRetriever:
    def __init__(self) -> None:
        self.store = ReviewVectorStore()
        model = os.getenv("LOCAL_EMBEDDING_MODEL")
        self.embedder = LocalEmbedder(model_name=model)

    @property
    def corpus_size(self) -> int:
        return self.store.count()

    def retrieve(self, question: str, top_k: int | None = None) -> list[RetrievedReview]:
        k = top_k if top_k is not None else int(os.getenv("RAG_TOP_K", RAG_TOP_K))
        if self.store.count() == 0:
            return []

        vector = self.embedder.embed_one(question)
        results = self.store.query(vector, n_results=min(k, self.store.count()))

        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        retrieved: list[RetrievedReview] = []
        for rid, doc, meta, dist in zip(ids, documents, metadatas, distances):
            meta = meta or {}
            retrieved.append(
                RetrievedReview(
                    review_id=str(rid),
                    document=str(doc or ""),
                    rating=int(meta.get("rating", 0)),
                    date=str(meta.get("date", "")),
                    app_version=str(meta.get("app_version", "")),
                    similarity=ReviewVectorStore.distance_to_similarity(float(dist)),
                )
            )
        return retrieved
