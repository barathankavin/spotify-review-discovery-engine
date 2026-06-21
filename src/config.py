"""Project configuration defaults (non-secret)."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"
VECTOR_STORE_DIR = PROJECT_ROOT / "vector_store"

PACKAGE_NAME = "com.spotify.music"
LOOKBACK_WEEKS = 10
MIN_WORD_COUNT = 6

GROQ_EMBEDDING_MODEL = "nomic-embed-text-v1.5"
EMBED_BATCH_SIZE = 128
EMBED_BATCH_SLEEP_S = 1.0

# Phase 3 — Groq chat model (enable llama-3.1-8b-instant in Groq project for 500K TPD)
GROQ_CHAT_MODEL = "llama-3.3-70b-versatile"
ANALYSIS_SAMPLE_CAP = 450
UNMET_NEEDS_SAMPLE_CAP = 300
ANALYSIS_BATCH_SIZE = 20
GROQ_CALL_SLEEP_S = 0.5

# Phase 5 — RAG chatbot
RAG_TOP_K = 4
RAG_SIMILARITY_THRESHOLD = 0.35
RAG_MAX_ANSWER_TOKENS = 512
