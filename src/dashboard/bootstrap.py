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


def apply_streamlit_secrets(st_module) -> None:
    """Map Streamlit secrets into os.environ.

    Works on Streamlit Community Cloud and Hugging Face Spaces, where secrets are
    injected via st.secrets without a local secrets.toml at a predictable path.
    Existing os.environ values (e.g. HF Spaces env-var secrets) take precedence.
    """
    try:
        secrets = st_module.secrets
        for key in list(secrets.keys()):
            value = secrets[key]
            if isinstance(value, str) and not os.environ.get(key):
                os.environ[key] = value
    except Exception:
        # No secrets configured (e.g. local run with only .env) — that's fine.
        return
