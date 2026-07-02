"""Resolve Chroma persistence directory for local dev vs Streamlit Cloud.

On Streamlit Cloud the committed ``vector_store/`` is kept in sync by the weekly
GitHub Action. The dashboard should **read that index directly** (no 57 MB copy
to ``/tmp``, no runtime embed). Runtime writes use a seeded tmp dir only when
``RUNTIME_EMBED=true`` (local-style incremental updates on cloud).
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

from src.config import VECTOR_STORE_DIR

logger = logging.getLogger(__name__)

_CLOUD_MOUNT = Path("/mount/src")
_SEED_MARKER = ".seeded_from_repo"


def is_streamlit_cloud() -> bool:
    if os.getenv("CHROMA_USE_TMP", "").lower() in ("1", "true", "yes"):
        return True
    if os.getenv("CHROMA_USE_TMP", "").lower() in ("0", "false", "no"):
        return False
    return _CLOUD_MOUNT.exists()


def runtime_embed_enabled() -> bool:
    """Whether the dashboard may embed/upsert on this host (default: off on cloud)."""
    flag = os.getenv("RUNTIME_EMBED", "").lower()
    if flag in ("1", "true", "yes"):
        return True
    if flag in ("0", "false", "no"):
        return False
    return not is_streamlit_cloud()


def default_tmp_chroma_dir() -> Path:
    return Path(os.getenv("CHROMA_PERSIST_DIR", "/tmp/nl_review_chroma"))


def committed_chroma_dir() -> Path:
    return VECTOR_STORE_DIR


def _seed_from_repo(target: Path) -> None:
    source = committed_chroma_dir()
    if not (source / "chroma.sqlite3").exists():
        logger.warning("Committed vector store missing at %s — starting empty", source)
        target.mkdir(parents=True, exist_ok=True)
        return

    if target.exists():
        shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True, exist_ok=True)

    logger.info("Seeding writable Chroma store: %s -> %s", source, target)
    for item in source.iterdir():
        dest = target / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    (target / _SEED_MARKER).write_text(str(source.resolve()), encoding="utf-8")


def resolve_chroma_persist_dir(*, writable: bool = False) -> Path:
    """Return the Chroma directory for reads (default) or writes (writable=True)."""
    override = os.getenv("CHROMA_PERSIST_DIR")
    if override and not is_streamlit_cloud():
        path = Path(override)
        path.mkdir(parents=True, exist_ok=True)
        return path

    if not is_streamlit_cloud():
        committed_chroma_dir().mkdir(parents=True, exist_ok=True)
        return committed_chroma_dir()

    # Cloud: read committed CI index directly (fast, no copy).
    if not writable or not runtime_embed_enabled():
        if (committed_chroma_dir() / "chroma.sqlite3").exists():
            return committed_chroma_dir()
        logger.warning("No committed chroma.sqlite3 — falling back to tmp store")

    tmp = default_tmp_chroma_dir()
    if not (tmp / "chroma.sqlite3").exists() or not (tmp / _SEED_MARKER).exists():
        _seed_from_repo(tmp)
    return tmp
