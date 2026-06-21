"""Local smoke tests for Phase 6 deployment readiness."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from src.config import PROCESSED_DIR, PROJECT_ROOT, VECTOR_STORE_DIR
from src.dashboard.data_loader import load_dashboard_data
from src.embeddings.store import ReviewVectorStore
from src.ops.ensure_vector_store import ensure_vector_store
from src.rag.pipeline import answer_question
from src.rag.retriever import ReviewRetriever

load_dotenv(PROJECT_ROOT / ".env")

CHECKS: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((name, ok, detail))
    status = "PASS" if ok else "FAIL"
    line = f"[{status}] {name}"
    if detail:
        line += f" — {detail}"
    print(line)


def main() -> int:
    print("=== Phase 6 Smoke Test ===\n")

    required = [
        PROCESSED_DIR / "themes.json",
        PROCESSED_DIR / "unmet_needs.json",
        PROCESSED_DIR / "segments.json",
        PROCESSED_DIR / "normalized_reviews.json",
        PROCESSED_DIR / "run_metadata.json",
    ]
    for path in required:
        record(f"Artifact exists: {path.name}", path.exists())

    try:
        data = load_dashboard_data()
        record("Dashboard data loader", True, f"{len(data.themes)} themes")
        record("Theme count <= 5", len(data.themes) <= 5, str(len(data.themes)))
        record("Theme validation", data.run_metadata.get("theme_validation_ok", False))
    except Exception as exc:
        record("Dashboard data loader", False, str(exc))

    try:
        status = ensure_vector_store()
        record(
            "Vector store",
            status.get("count", 0) > 0,
            f"{status.get('action')} count={status.get('count')}",
        )
    except Exception as exc:
        record("Vector store", False, str(exc))

    store = ReviewVectorStore()
    record("Chroma path", VECTOR_STORE_DIR.exists(), str(VECTOR_STORE_DIR))

    try:
        retriever = ReviewRetriever()
        grounded = answer_question(
            "Why do users struggle to discover new music?", retriever
        )
        record(
            "Chatbot retrieval",
            len(grounded.retrieved) > 0,
            f"sim={grounded.max_similarity:.2f}",
        )
        oof = answer_question("What's Spotify's stock price?", retriever)
        record(
            "Chatbot out-of-scope refusal",
            oof.refused and not oof.groq_called,
            oof.answer[:60],
        )
    except Exception as exc:
        record("Chatbot", False, str(exc))

    failed = sum(1 for _, ok, _ in CHECKS if not ok)
    print(f"\n=== {len(CHECKS) - failed}/{len(CHECKS)} passed ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
