"""Basic validity checks for checkpoints produced by unmodified upstream training."""

import argparse
import json
from pathlib import Path

import torch


def nonfinite(value):
    if isinstance(value, torch.Tensor):
        return int((~torch.isfinite(value)).sum())
    if isinstance(value, dict):
        return sum(nonfinite(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return sum(nonfinite(v) for v in value)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    ck = torch.load(args.checkpoint, map_location="cpu", mmap=True, weights_only=False)
    counts = {
        key: sorted({int(v["step"]) for v in ck[key]["state"].values()})
        for key in ("opt_wm", "opt_pi", "opt_v")
    }
    cfg, iteration = ck["args"], ck["iteration"]
    actor_updates = max(0, iteration - cfg["wm_only_iters"])
    expected = {
        "opt_wm": [iteration * cfg["wm_batches"]],
        "opt_pi": [actor_updates] if actor_updates else [],
        "opt_v": [actor_updates * cfg["critic_epochs"] * cfg["critic_minibatches"]]
        if actor_updates
        else [],
    }
    invalid = {
        key: nonfinite(ck[key]) for key in ("wm", "pi", "critic", "opt_wm", "opt_pi", "opt_v")
    }
    result = {
        "iteration": iteration,
        "checkpoint": str(args.checkpoint.resolve()),
        "nonfinite": invalid,
        "optimizer_steps": counts,
        "fresh_run": cfg.get("resume") is None,
        "passed": not any(invalid.values())
        and (cfg.get("resume") is not None or counts == expected),
    }
    args.out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2), flush=True)
    if not result["passed"]:
        raise RuntimeError("checkpoint validity or actual optimizer-update counts failed")


if __name__ == "__main__":
    main()
