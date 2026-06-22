"""Trigger the GitHub Actions refresh workflow from the dashboard.

The in-app "Refresh pipeline" button always reloads local artifacts from disk.
When GH_DISPATCH_TOKEN + GH_REPO are configured (locally in .env or in platform
Secrets), it can additionally fire the weekly-refresh workflow via the GitHub
REST API (workflow_dispatch), so a click actually re-runs ingestion + analysis
on GitHub and commits fresh artifacts. Uses only the standard library.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

DEFAULT_WORKFLOW = "weekly-refresh.yml"
DEFAULT_BRANCH = "master"


@dataclass
class RefreshOutcome:
    ok: bool
    message: str
    actions_url: str | None = None


def github_refresh_configured() -> bool:
    """True when both a dispatch token and a target repo are available."""
    return bool(os.getenv("GH_DISPATCH_TOKEN") and os.getenv("GH_REPO"))


def trigger_github_refresh() -> RefreshOutcome:
    """Fire a workflow_dispatch event for the refresh workflow."""
    token = os.getenv("GH_DISPATCH_TOKEN")
    repo = os.getenv("GH_REPO")
    if not token or not repo:
        return RefreshOutcome(False, "Remote refresh is not configured.")

    workflow = os.getenv("GH_WORKFLOW_FILE", DEFAULT_WORKFLOW)
    branch = os.getenv("GH_BRANCH", DEFAULT_BRANCH)
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches"
    payload = json.dumps({"ref": branch}).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "review-discovery-engine")

    actions_url = f"https://github.com/{repo}/actions/workflows/{workflow}"
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status in (201, 204):
                return RefreshOutcome(
                    True,
                    "Pipeline refresh triggered on GitHub Actions.",
                    actions_url,
                )
            return RefreshOutcome(False, f"Unexpected response: HTTP {resp.status}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "ignore")[:200]
        return RefreshOutcome(False, f"GitHub API error (HTTP {exc.code}): {detail}")
    except Exception as exc:  # noqa: BLE001 - surface any network/url issue to the UI
        return RefreshOutcome(False, f"Could not reach GitHub: {exc}")
