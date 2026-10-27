"""Fetch the pinned third-party checkout without copying it into this repository."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from experiments.low_vram_vibed.config import REPO_ROOT, load_upstream
from experiments.low_vram_vibed.provenance import inspect_upstream


def main(argv: list[str] | None = None) -> None:
    upstream = load_upstream()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=REPO_ROOT / upstream["checkout"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    selected = dict(upstream, checkout=str(args.dest))

    if args.dest.exists():
        status = inspect_upstream(selected)
        if status.get("ready"):
            print(f"upstream already present and clean: {args.dest}")
            return
        parser.error(
            f"destination exists but is not the pinned clean checkout: {status.get('reason')}"
        )

    commands = [
        ["git", "init", str(args.dest)],
        ["git", "-C", str(args.dest), "remote", "add", "origin", upstream["repository"]],
        ["git", "-C", str(args.dest), "fetch", "--depth", "1", "origin", upstream["commit"]],
        ["git", "-C", str(args.dest), "checkout", "--detach", "FETCH_HEAD"],
    ]
    for command in commands:
        print(" ".join(command))
        if not args.dry_run:
            subprocess.run(command, check=True)
    if not args.dry_run:
        status = inspect_upstream(selected)
        if not status.get("ready"):
            raise RuntimeError(
                status.get("reason", "fetched checkout failed provenance validation")
            )
        print("upstream fetch complete; follow its own README for Isaac Lab and data setup")


if __name__ == "__main__":
    main()
