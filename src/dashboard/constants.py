"""Dashboard constants and copy."""

from pathlib import Path

from src.config import PROCESSED_DIR

ARTIFACT_DIR = PROCESSED_DIR
LKG_DIR = PROCESSED_DIR / "lkg"

THEMES_FILE = "themes.json"
UNMET_NEEDS_FILE = "unmet_needs.json"
SEGMENTS_FILE = "segments.json"
REVIEWS_FILE = "normalized_reviews.json"
RUN_METADATA_FILE = "run_metadata.json"

MAX_SUMMARY_WORDS = 250
ANOMALY_Z_THRESHOLD = 1.75

SEGMENT_DISCLAIMER = (
    "How to read this: segments are inferred from review wording (e.g. mentions of "
    "\"premium\", \"ads\", or low ratings) — they are directional signals only, "
    "not verified demographic or subscription data."
)

APP_TITLE = "Spotify Review Discovery Engine"
APP_SUBTITLE = "Play Store reviews — discovery & recommendations focus"
