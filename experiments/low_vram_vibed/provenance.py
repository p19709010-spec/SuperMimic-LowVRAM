"""Read-only provenance checks for the external ``supermimic_vibed`` checkout."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from experiments.low_vram_vibed.config import REPO_ROOT, load_upstream


class ProvenanceError(RuntimeError):
    """Raised when the external checkout is missing, modified or at the wrong commit."""


def _git(path: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(path), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def inspect_upstream(upstream: dict[str, Any] | None = None) -> dict[str, Any]:
    upstream = upstream or load_upstream()
    checkout = REPO_ROOT / upstream["checkout"]
    result: dict[str, Any] = {
        "path": str(checkout),
        "expected_repository": upstream["repository"],
        "expected_commit": upstream["commit"],
        "exists": checkout.is_dir(),
    }
    if not checkout.is_dir():
        result.update(ready=False, reason="checkout is missing")
        return result
    try:
        commit = _git(checkout, "rev-parse", "HEAD")
        remote = _git(checkout, "remote", "get-url", "origin")
        dirty = bool(_git(checkout, "status", "--porcelain", "--untracked-files=no"))
    except (subprocess.CalledProcessError, FileNotFoundError) as error:
        result.update(ready=False, reason=f"cannot inspect checkout: {error}")
        return result
    result.update(commit=commit, remote=remote, source_modified=dirty)
    problems = []
    if remote != upstream["repository"]:
        problems.append("origin URL does not match upstream.json")
    if commit != upstream["commit"]:
        problems.append("HEAD does not match upstream.json")
    if dirty:
        problems.append("tracked upstream source is modified")
    result["ready"] = not problems
    if problems:
        result["reason"] = "; ".join(problems)
    return result


def require_clean_upstream(upstream: dict[str, Any] | None = None) -> dict[str, Any]:
    status = inspect_upstream(upstream)
    if not status.get("ready"):
        raise ProvenanceError(status.get("reason", "upstream checkout is not ready"))
    return status
