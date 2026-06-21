"""Groq Embeddings API client with batching and rate-limit backoff."""

from __future__ import annotations

import logging
import os
import time
from typing import Callable, Sequence

from groq import Groq
from groq import RateLimitError

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "nomic-embed-text-v1.5"
FALLBACK_MODEL = "nomic-embed-text-v1_5"
MAX_RETRIES = 6
INITIAL_BACKOFF_S = 2.0


class GroqEmbedder:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        sleep_between_batches_s: float | None = None,
    ) -> None:
        key = api_key or os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to .env (see .env.example)."
            )
        self.client = Groq(api_key=key)
        self.model = model or os.getenv("GROQ_EMBEDDING_MODEL", DEFAULT_MODEL)
        self.sleep_between_batches_s = float(
            sleep_between_batches_s
            if sleep_between_batches_s is not None
            else os.getenv("EMBED_BATCH_SLEEP_S", "1.0")
        )
        self.api_call_count = 0

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.embeddings.create(
                    input=list(texts),
                    model=self.model,
                    encoding_format="float",
                )
                self.api_call_count += 1
                ordered = sorted(response.data, key=lambda item: item.index)
                return [item.embedding for item in ordered]
            except RateLimitError as exc:
                last_error = exc
                wait = INITIAL_BACKOFF_S * (2**attempt)
                logger.warning(
                    "Groq rate limit (attempt %s/%s); sleeping %.1fs",
                    attempt + 1,
                    MAX_RETRIES,
                    wait,
                )
                time.sleep(wait)
            except Exception as exc:
                if self.model == DEFAULT_MODEL and "model" in str(exc).lower():
                    logger.warning(
                        "Model %s failed (%s); trying %s",
                        self.model,
                        exc,
                        FALLBACK_MODEL,
                    )
                    self.model = FALLBACK_MODEL
                    continue
                raise

        raise RuntimeError(f"Groq embedding failed after {MAX_RETRIES} retries") from last_error

    def embed_one(self, text: str) -> list[float]:
        vectors = self.embed_texts([text])
        return vectors[0]

    def embed_batches(
        self,
        texts: Sequence[str],
        batch_size: int,
        on_batch_complete: Callable[[int, int, int], None] | None = None,
    ) -> list[list[float]]:
        all_vectors: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            vectors = self.embed_texts(batch)
            all_vectors.extend(vectors)
            if on_batch_complete:
                on_batch_complete(start, len(batch), len(all_vectors))
            if start + batch_size < len(texts) and self.sleep_between_batches_s > 0:
                time.sleep(self.sleep_between_batches_s)
        return all_vectors
