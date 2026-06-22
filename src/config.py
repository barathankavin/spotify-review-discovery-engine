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

# Phase 3 — Groq chat model. Use a model ENABLED in your Groq project (a disabled
# model returns 403). llama-3.1-8b-instant has ~5x the daily token limit of 70b;
# enable it in the Groq console to switch, then set GROQ_CHAT_MODEL accordingly.
GROQ_CHAT_MODEL = "llama-3.3-70b-versatile"
ANALYSIS_SAMPLE_CAP = 450
UNMET_NEEDS_SAMPLE_CAP = 300
ANALYSIS_BATCH_SIZE = 20
GROQ_CALL_SLEEP_S = 0.5

# Phase 5 — RAG chatbot
RAG_TOP_K = 12          # final reviews sent to the LLM (kept <=13 for context budget)
RAG_FETCH_K = 40        # candidate pool pulled from Chroma before MMR re-selection
RAG_MMR_LAMBDA = 0.7    # MMR trade-off: 1.0 = pure relevance, 0.0 = pure diversity
RAG_SIMILARITY_THRESHOLD = 0.35
RAG_MAX_ANSWER_TOKENS = 512
