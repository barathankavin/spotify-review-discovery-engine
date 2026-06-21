"""Local sentence-transformers embedder (fallback when Groq embeddings unavailable)."""

from __future__ import annotations

import logging
import os

from sentence_transformers import SentenceTransformer

from src.embeddings.hf_auth import configure_hf_hub, prefer_local_files_only

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class LocalEmbedder:
    def __init__(self, model_name: str | None = None) -> None:
        name = model_name or os.getenv("LOCAL_EMBEDDING_MODEL", DEFAULT_MODEL)
        configure_hf_hub()
        local_only = prefer_local_files_only(name)

        if local_only:
            logger.info("Loading local embedding model from cache: %s", name)
        else:
            logger.info("Loading local embedding model: %s", name)

        self.model = SentenceTransformer(name, local_files_only=local_only)
        self.model_name = name
        self.api_call_count = 0

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self.model.encode(texts, show_progress_bar=False)
        self.api_call_count += 1
        return [v.tolist() for v in vectors]

    def embed_one(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]
