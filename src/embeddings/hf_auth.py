"""Hugging Face Hub auth and offline cache helpers for local embeddings."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

from src.config import PROJECT_ROOT

logger = logging.getLogger(__name__)


def _load_env() -> None:
    load_dotenv(PROJECT_ROOT / ".env")


def get_hf_token() -> str | None:
    _load_env()
    token = (os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN") or "").strip()
    return token or None


def configure_hf_hub() -> str | None:
    """Authenticate with Hugging Face Hub when HF_TOKEN is set in .env."""
    token = get_hf_token()
    if not token:
        return None

    os.environ["HF_TOKEN"] = token
    os.environ["HUGGINGFACE_HUB_TOKEN"] = token
    try:
        from huggingface_hub import login

        login(token=token, add_to_git_credential=False)
        logger.info("Hugging Face Hub authenticated")
    except Exception as exc:
        logger.warning("Hugging Face Hub login failed: %s", exc)
    return token


def model_is_cached(model_name: str) -> bool:
    try:
        from huggingface_hub import try_to_load_from_cache

        return try_to_load_from_cache(model_name, "config.json") is not None
    except Exception:
        return False


def prefer_local_files_only(model_name: str) -> bool:
    """Use cached weights only — avoids unauthenticated Hub requests."""
    _load_env()
    if os.getenv("HF_HUB_OFFLINE", "").lower() in ("1", "true", "yes"):
        return True
    if get_hf_token():
        return False
    return model_is_cached(model_name)
