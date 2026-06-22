"""Bootstrap path, .env, and optional Streamlit secrets."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.config import PROJECT_ROOT  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")


def _flatten_secrets(secrets) -> dict[str, str]:
    """Flatten st.secrets into a flat {KEY: value} dict.

    Handles both top-level keys (GROQ_API_KEY = "...") and values nested under a
    TOML section ([groq]\\nGROQ_API_KEY = "...") which is a common mistake when
    pasting secrets on Streamlit Cloud.
    """
    flat: dict[str, str] = {}
    try:
        items = list(secrets.items())
    except Exception:
        return flat
    for key, value in items:
        if isinstance(value, str):
            flat.setdefault(key, value)
        else:
            # Nested section (Mapping-like) — pull its string children up.
            try:
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, str):
                        flat.setdefault(sub_key, sub_value)
            except Exception:
                continue
    return flat


def apply_streamlit_secrets(st_module) -> None:
    """Map Streamlit secrets into os.environ.

    Works on Streamlit Community Cloud and Hugging Face Spaces, where secrets are
    injected via st.secrets without a local secrets.toml at a predictable path.
    Existing os.environ values (e.g. HF Spaces env-var secrets) take precedence.
    """
    try:
        flat = _flatten_secrets(st_module.secrets)
    except Exception:
        # No secrets configured (e.g. local run with only .env) — that's fine.
        return
    for key, value in flat.items():
        if not os.environ.get(key):
            os.environ[key] = value


def secret_key_names(st_module) -> list[str]:
    """Return visible secret key NAMES (never values) for safe diagnostics."""
    try:
        return sorted(_flatten_secrets(st_module.secrets).keys())
    except Exception:
        return []
