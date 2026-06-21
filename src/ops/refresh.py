"""Weekly refresh orchestration — Phases 1 through 3."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.config import PROCESSED_DIR, PROJECT_ROOT

logger = logging.getLogger(__name__)

ARTIFACT_NAMES = (
    "themes.json",
    "unmet_needs.json",
    "segments.json",
    "run_metadata.json",
    "normalized_reviews.json",
    "embed_checkpoint.json",
)


def _run_module(module: str, extra_args: list[str] | None = None) -> None:
    cmd = [sys.executable, "-m", module, *(extra_args or [])]
    logger.info("Running: %s", " ".join(cmd))
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def backup_artifacts(run_id: str) -> Path:
    backup_dir = PROCESSED_DIR / "backups" / run_id
    backup_dir.mkdir(parents=True, exist_ok=True)
    for name in ARTIFACT_NAMES:
        src = PROCESSED_DIR / name
        if src.exists():
            shutil.copy2(src, backup_dir / name)
    return backup_dir


def refresh(
    lookback_weeks: int = 10,
    skip_ingestion: bool = False,
    skip_embed: bool = False,
    skip_analysis: bool = False,
    rule_baseline: bool = False,
) -> dict:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_artifacts(run_id)

    if not skip_ingestion:
        _run_module("src.ingestion.run", ["--lookback-weeks", str(lookback_weeks)])

    if not skip_embed:
        _run_module("src.embeddings.run")

    if not skip_analysis:
        args = ["--rule-baseline"] if rule_baseline else []
        _run_module("src.analysis.run", args)

    meta_path = PROCESSED_DIR / "run_metadata.json"
    metadata = {}
    if meta_path.exists():
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))

    ok = metadata.get("theme_validation_ok", False)
    return {
        "run_id": run_id,
        "backup_dir": str(PROCESSED_DIR / "backups" / run_id),
        "theme_validation_ok": ok,
        "metadata": metadata,
    }
