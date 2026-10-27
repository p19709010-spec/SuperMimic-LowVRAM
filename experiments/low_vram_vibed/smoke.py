"""No-GPU smoke check for profiles, provenance and core CPU imports."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from experiments.low_vram_vibed.config import REPO_ROOT, all_profiles, load_upstream
from experiments.low_vram_vibed.provenance import inspect_upstream


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-upstream", action="store_true")
    args = parser.parse_args(argv)

    profiles = all_profiles()
    upstream = inspect_upstream(load_upstream())
    if args.require_upstream and not upstream.get("ready"):
        raise SystemExit(f"upstream provenance failed: {upstream.get('reason')}")

    import torch

    from supermimic.policy.nets import Policy, PolicyCfg

    policy = Policy(PolicyCfg(encoder_hidden=(8,), decoder_hidden=(8,)))
    with torch.no_grad():
        actions = policy(torch.zeros(2, 930), torch.zeros(2, 680))
    if tuple(actions.shape) != (2, 29) or not bool(torch.isfinite(actions).all()):
        raise SystemExit("policy CPU smoke failed: invalid output")

    forbidden_artifacts = [
        str(path.relative_to(REPO_ROOT))
        for pattern in ("*.pt", "*.npz", "*.ckpt")
        for path in (REPO_ROOT / "experiments").rglob(pattern)
    ]
    result = {
        "profile_count": len(profiles),
        "profiles": {profile["name"]: profile["status"] for profile in profiles},
        "upstream": upstream,
        "policy_output_shape": list(actions.shape),
        "policy_output_finite": True,
        "forbidden_artifacts_in_experiments": forbidden_artifacts,
    }
    print(json.dumps(result, indent=2))
    if forbidden_artifacts:
        raise SystemExit("model or data artifacts must not be stored in experiments/")


if __name__ == "__main__":
    main()
