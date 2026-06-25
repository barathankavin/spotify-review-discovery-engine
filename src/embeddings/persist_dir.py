"""Resolve a writable Chroma persistence directory for local vs Streamlit Cloud.

On Streamlit Cloud the repo lives under ``/mount/src`` and upserting into the
committed ``vector_store/`` often triggers Chroma InternalError (sqlite/HNSW
writes on the cloned index). We seed a writable copy under ``/tmp`` once per
container and use that for all reads and writes.
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


def default_tmp_chroma_dir() -> Path:
    return Path(os.getenv("CHROMA_PERSIST_DIR", "/tmp/nl_review_chroma"))


def _seed_from_repo(target: Path) -> None:
    source = VECTOR_STORE_DIR
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


def resolve_chroma_persist_dir() -> Path:
    """Return the Chroma directory all dashboard/ops code should use."""
    override = os.getenv("CHROMA_PERSIST_DIR")
    if override and not is_streamlit_cloud():
        path = Path(override)
        path.mkdir(parents=True, exist_ok=True)
        return path

    if not is_streamlit_cloud():
        VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
        return VECTOR_STORE_DIR

    tmp = default_tmp_chroma_dir()
    if not (tmp / "chroma.sqlite3").exists() or not (tmp / _SEED_MARKER).exists():
        _seed_from_repo(tmp)
    return tmp
