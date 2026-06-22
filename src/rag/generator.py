"""Groq answer generation from retrieved review excerpts."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from groq import Groq, RateLimitError

from src.config import GROQ_CHAT_MODEL, RAG_MAX_ANSWER_TOKENS
from src.rag.retriever import RetrievedReview

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a research assistant analyzing Spotify Play Store reviews about music discovery and recommendations.

Rules:
1. Answer ONLY using the review excerpts provided below. Do not use general knowledge.
2. Cite every factual claim with [review_id: <uuid>] matching an excerpt review_id.
3. Draw on the FULL set of provided excerpts, not just the first one or two. When several
   reviews support a point, cite multiple distinct review_ids, and group related themes so
   the breadth of evidence is visible.
4. If excerpts are ambiguous or contradictory, say so explicitly.
5. Never include reviewer names, emails, phone numbers, or other PII.
6. Do not discuss stock prices, company strategy, or future product launches.
7. Keep answers PM-readable and well-structured (aim for under 300 words).
8. If excerpts do not support an answer, say "The retrieved reviews do not contain enough evidence."
"""


def _format_context(retrieved: list[RetrievedReview]) -> str:
    blocks = []
    for item in retrieved:
        blocks.append(
            json.dumps(
                {
                    "review_id": item.review_id,
                    "rating": item.rating,
                    "date": item.date,
                    "text": item.document[:800],
                },
                ensure_ascii=False,
            )
        )
    return "\n".join(blocks)


def generate_answer(question: str, retrieved: list[RetrievedReview]) -> tuple[str, dict[str, Any]]:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY not found. Add it to .env locally, or to your platform "
            "Secrets (Streamlit Cloud / Hugging Face Spaces) and reboot the app."
        )

    model = os.getenv("GROQ_CHAT_MODEL", GROQ_CHAT_MODEL)
    max_tokens = int(os.getenv("RAG_MAX_ANSWER_TOKENS", RAG_MAX_ANSWER_TOKENS))
    client = Groq(api_key=key, max_retries=10)

    user_prompt = (
        f"Question: {question}\n\n"
        f"Retrieved review excerpts:\n{_format_context(retrieved)}\n\n"
        "Answer the question using only these excerpts. Include [review_id: ...] citations."
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=max_tokens,
        )
    except RateLimitError as exc:
        logger.warning("Groq rate limited during chat: %s", exc)
        raise exc

    answer = (response.choices[0].message.content or "").strip()
    usage = getattr(response, "usage", None)
    meta = {
        "model": model,
        "tokens": getattr(usage, "total_tokens", None) if usage else None,
    }
    return answer, meta
