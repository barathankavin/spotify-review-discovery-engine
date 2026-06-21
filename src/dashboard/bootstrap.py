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

_SECRETS_PATHS = (
    PROJECT_ROOT / ".streamlit" / "secrets.toml",
    Path.home() / ".streamlit" / "secrets.toml",
    Path(__file__).resolve().parent / ".streamlit" / "secrets.toml",
)


def secrets_file_exists() -> bool:
    return any(p.is_file() for p in _SECRETS_PATHS)


def apply_streamlit_secrets(st_module) -> None:
    """Map Streamlit Cloud secrets into os.environ; no-op if no secrets.toml."""
    if not secrets_file_exists():
        return
    try:
        from streamlit.errors import StreamlitSecretNotFoundError
    except ImportError:
        StreamlitSecretNotFoundError = Exception  # type: ignore[misc, assignment]

    try:
        for key, value in st_module.secrets.items():
            if isinstance(value, str) and key not in os.environ:
                os.environ[key] = value
    except StreamlitSecretNotFoundError:
        return
