"""Similarity threshold gate — skip Groq when retrieval signal is weak."""

from __future__ import annotations

import os
import re

from src.config import RAG_SIMILARITY_THRESHOLD
from src.rag.retriever import RetrievedReview

REFUSAL_MESSAGE = (
    "Not enough signal in the reviews to answer that. "
    "Try rephrasing with Spotify discovery, recommendations, playlists, or shuffle."
)

OUT_OF_SCOPE_MESSAGE = (
    "Not enough signal in the reviews to answer that. "
    "This assistant only answers from Play Store review excerpts, not general knowledge."
)

OUT_OF_SCOPE_PATTERN = re.compile(
    r"stock price|share price|market cap|\bCEO\b|"
    r"will spotify launch|next year|lossless tier|"
    r"competitor|apple music ceo|warner|universal music",
    re.I,
)


def is_out_of_scope(question: str) -> bool:
    return bool(OUT_OF_SCOPE_PATTERN.search(question))


def max_similarity(retrieved: list[RetrievedReview]) -> float:
    if not retrieved:
        return 0.0
    return max(r.similarity for r in retrieved)


def passes_threshold(
    retrieved: list[RetrievedReview],
    threshold: float | None = None,
) -> bool:
    limit = threshold if threshold is not None else float(
        os.getenv("RAG_SIMILARITY_THRESHOLD", RAG_SIMILARITY_THRESHOLD)
    )
    return max_similarity(retrieved) >= limit
