"""CLI smoke test for Phase 5 RAG chatbot."""

from __future__ import annotations

import argparse
import logging
import sys

from dotenv import load_dotenv

from src.config import PROJECT_ROOT
from src.rag.pipeline import answer_question
from src.rag.retriever import ReviewRetriever

GROUNDED = [
    "Why do users struggle to discover new music?",
    "What are the most common frustrations with recommendations?",
]

REFUSAL = [
    "What's Spotify's stock price?",
    "Who is the CEO of Apple Music?",
]


def main(argv: list[str] | None = None) -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    parser = argparse.ArgumentParser(description="RAG chatbot smoke test")
    parser.add_argument("question", nargs="?", help="Single question to ask")
    parser.add_argument("--smoke", action="store_true", help="Run built-in test questions")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)

    retriever = ReviewRetriever()
    print(f"Corpus size: {retriever.corpus_size}")

    questions = [args.question] if args.question else []
    if args.smoke:
        questions = GROUNDED + REFUSAL
    if not questions:
        parser.print_help()
        return 1

    for q in questions:
        print(f"\n{'='*60}\nQ: {q}")
        result = answer_question(q, retriever)
        print(f"Groq called: {result.groq_called}  Refused: {result.refused}")
        print(f"Max similarity: {result.max_similarity:.3f}")
        print(f"Retrieved: {len(result.retrieved)}")
        print(f"A: {result.answer[:500]}")
        if result.validation_errors:
            print(f"Validation errors: {result.validation_errors}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
