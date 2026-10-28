"""Inspect unmodified upstream SuperMimic checkpoints without changing them.

The pinned upstream writes two intentionally different formats:

* ``ckpt_<iteration>.pt``: inference/weight-only ``pi`` and ``wm`` state dicts.
* ``last.pt``: the same networks plus ``critic``, three Adam state dicts, and
  iteration/timing metadata.

Weight-only files are valid, but they cannot be used as a complete training resume.
Even an upstream ``last.pt`` omits replay, RNG, and simulator state, so the validator
reports optimizer resumability separately from exact/repeatable recovery.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import torch

NETWORKS = ("wm", "pi", "critic")
OPTIMIZERS = ("opt_wm", "opt_pi", "opt_v")
WEIGHT_ONLY_NETWORKS = {"wm", "pi"}
REQUIRED_NETWORK_PREFIXES = {
    "wm": ("net.", "in_norm.", "out_norm."),
    "pi": ("enc.", "dec.", "obs_norm.", "goal_norm."),
}
RESUME_METADATA = ("iteration", "wall_time", "sim_steps", "args")


def nonfinite(value: Any) -> int:
    """Count non-finite tensor elements in nested checkpoint data."""
    if isinstance(value, torch.Tensor):
        if value.is_floating_point() or value.is_complex():
            return int((~torch.isfinite(value)).sum())
        return 0
    if isinstance(value, Mapping):
        return sum(nonfinite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return sum(nonfinite(item) for item in value)
    return 0


def _inspect_state_dict(name: str, value: Any) -> dict[str, Any]:
    issues: list[str] = []
    if not isinstance(value, Mapping):
        return {
            "kind": "network",
            "present": True,
            "valid": False,
            "tensors": 0,
            "parameters": 0,
            "nonfinite": 0,
            "issues": [f"{name} is {type(value).__name__}, expected a state_dict mapping"],
        }
    if not value:
        issues.append(f"{name} state_dict is empty")

    tensors = 0
    parameters = 0
    invalid_entries: list[str] = []
    dtypes: set[str] = set()
    for key, tensor in value.items():
        if not isinstance(key, str) or not key:
            invalid_entries.append(repr(key))
            continue
        if not isinstance(tensor, torch.Tensor):
            invalid_entries.append(key)
            continue
        tensors += 1
        parameters += tensor.numel()
        dtypes.add(str(tensor.dtype))
    if invalid_entries:
        issues.append(
            f"{name} contains non-tensor or invalid state_dict entries: "
            + ", ".join(sorted(invalid_entries)[:8])
        )

    keys = {key for key in value if isinstance(key, str)}
    for prefix in REQUIRED_NETWORK_PREFIXES.get(name, ()):
        if not any(key.startswith(prefix) for key in keys):
            issues.append(f"{name} state_dict lacks expected {prefix!r} keys")

    bad = nonfinite(value)
    if bad:
        issues.append(f"{name} contains {bad} non-finite tensor elements")
    return {
        "kind": "network",
        "present": True,
        "valid": not issues,
        "tensors": tensors,
        "parameters": parameters,
        "nonfinite": bad,
        "dtypes": sorted(dtypes),
        "issues": issues,
    }


def _optimizer_steps(value: Any) -> list[int]:
    if not isinstance(value, Mapping):
        return []
    state = value.get("state")
    if not isinstance(state, Mapping):
        return []
    steps: set[int] = set()
    for entry in state.values():
        if not isinstance(entry, Mapping):
            continue
        step = entry.get("step")
        if isinstance(step, torch.Tensor) and step.numel() == 1:
            steps.add(int(step.detach().cpu().item()))
        elif isinstance(step, (int, float)) and not isinstance(step, bool):
            steps.add(int(step))
    return sorted(steps)


def _inspect_optimizer(name: str, value: Any) -> dict[str, Any]:
    issues: list[str] = []
    if not isinstance(value, Mapping):
        return {
            "kind": "optimizer",
            "present": True,
            "valid": False,
            "state_entries": 0,
            "nonfinite": 0,
            "steps": [],
            "issues": [f"{name} is {type(value).__name__}, expected an optimizer mapping"],
        }
    for key in ("state", "param_groups"):
        if key not in value:
            issues.append(f"{name} lacks {key!r}")
    state = value.get("state")
    groups = value.get("param_groups")
    if state is not None and not isinstance(state, Mapping):
        issues.append(f"{name}.state is not a mapping")
    if groups is not None and not isinstance(groups, list):
        issues.append(f"{name}.param_groups is not a list")
    elif isinstance(groups, list):
        for index, group in enumerate(groups):
            if not isinstance(group, Mapping):
                issues.append(f"{name}.param_groups[{index}] is not a mapping")
                break
            if not isinstance(group.get("params"), (list, tuple)):
                issues.append(f"{name}.param_groups[{index}] lacks a params list")
                break
    state_entries = len(state) if isinstance(state, Mapping) else 0
    bad = nonfinite(value)
    if bad:
        issues.append(f"{name} contains {bad} non-finite tensor elements")
    return {
        "kind": "optimizer",
        "present": True,
        "valid": not issues,
        "state_entries": state_entries,
        "nonfinite": bad,
        "steps": _optimizer_steps(value),
        "issues": issues,
    }


def _expected_steps(checkpoint: Mapping[str, Any], iteration: int) -> dict[str, list[int]]:
    args = checkpoint.get("args")
    if not isinstance(args, Mapping):
        return {}
    try:
        wm_only = int(args["wm_only_iters"])
        wm_batches = int(args["wm_batches"])
        critic_epochs = int(args["critic_epochs"])
        critic_minibatches = int(args["critic_minibatches"])
    except (KeyError, TypeError, ValueError):
        return {}
    actor_updates = max(0, iteration - wm_only)
    return {
        "opt_wm": [iteration * wm_batches],
        "opt_pi": [actor_updates] if actor_updates else [],
        "opt_v": [actor_updates * critic_epochs * critic_minibatches]
        if actor_updates
        else [],
    }


def inspect_checkpoint(
    checkpoint: Any,
    checkpoint_path: str | Path | None = None,
    require_resume: bool = False,
) -> dict[str, Any]:
    """Return a JSON-serializable validation report without mutating ``checkpoint``."""
    result: dict[str, Any] = {
        "checkpoint": None if checkpoint_path is None else str(Path(checkpoint_path).resolve()),
        "format": "invalid",
        "passed": False,
        "network_integrity": {},
        "optimizer_integrity": {},
        "resume": {
            "optimizer_state_present": False,
            "training_resume_possible": False,
            "exact_recovery_confirmed": False,
        },
        "structural_issues": [],
        "warnings": [],
    }
    if not isinstance(checkpoint, Mapping):
        result["structural_issues"].append(
            f"checkpoint is {type(checkpoint).__name__}, expected a mapping"
        )
        return result

    keys = set(checkpoint)
    present_networks = {name for name in NETWORKS if name in keys}
    present_optimizers = {name for name in OPTIMIZERS if name in keys}
    result["present_network_keys"] = sorted(present_networks)
    result["present_optimizer_keys"] = sorted(present_optimizers)

    if present_networks == WEIGHT_ONLY_NETWORKS and not present_optimizers and "critic" not in keys:
        result["format"] = "weight_only"
    elif present_networks == set(NETWORKS) and present_optimizers == set(OPTIMIZERS):
        result["format"] = "resumable"
    else:
        result["format"] = "partial"

    for name in NETWORKS:
        if name in checkpoint:
            result["network_integrity"][name] = _inspect_state_dict(name, checkpoint[name])
        else:
            result["network_integrity"][name] = {
                "kind": "network",
                "present": False,
                "valid": False,
                "tensors": 0,
                "parameters": 0,
                "nonfinite": 0,
                "issues": [f"missing network key {name!r}"],
            }
    for name in OPTIMIZERS:
        if name in checkpoint:
            result["optimizer_integrity"][name] = _inspect_optimizer(name, checkpoint[name])
        else:
            result["optimizer_integrity"][name] = {
                "kind": "optimizer",
                "present": False,
                "valid": False,
                "state_entries": 0,
                "nonfinite": 0,
                "steps": [],
            }

    if result["format"] == "weight_only":
        result["warnings"].append(
            "Weight-only checkpoint: critic and Adam state are absent, so complete "
            "training recovery cannot be confirmed."
        )
    elif result["format"] == "resumable":
        result["resume"]["optimizer_state_present"] = True
        result["resume"]["training_resume_possible"] = True
        result["warnings"].append(
            "Optimizer state is present, but replay buffer, RNG state, and simulator "
            "state are absent; exact/repeatable recovery cannot be confirmed."
        )
    else:
        missing_networks = sorted(set(NETWORKS) - present_networks)
        missing_optimizers = sorted(set(OPTIMIZERS) - present_optimizers)
        details = []
        if missing_networks:
            details.append("missing networks: " + ", ".join(missing_networks))
        if missing_optimizers:
            details.append("missing optimizer states: " + ", ".join(missing_optimizers))
        result["structural_issues"].append(
            "unsupported or partially written checkpoint"
            + (f" ({'; '.join(details)})" if details else "")
        )

    invalid_networks = [
        name
        for name, report in result["network_integrity"].items()
        if report["present"] and not report["valid"]
    ]
    if invalid_networks:
        result["structural_issues"].append(
            "invalid network state: " + ", ".join(sorted(invalid_networks))
        )

    iteration = checkpoint.get("iteration")
    if isinstance(iteration, bool) or not isinstance(iteration, int) or iteration < 0:
        result["structural_issues"].append("iteration must be a nonnegative integer")
        iteration = None
    result["iteration"] = iteration
    result["wall_time"] = checkpoint.get("wall_time")
    result["sim_steps"] = checkpoint.get("sim_steps")
    result["saved_at"] = checkpoint.get("saved_at")

    if result["format"] == "resumable":
        missing_metadata = [key for key in RESUME_METADATA if key not in checkpoint]
        if missing_metadata:
            result["warnings"].append(
                "Missing resume metadata: " + ", ".join(missing_metadata)
            )
            result["structural_issues"].append(
                "resumable checkpoint lacks required metadata: "
                + ", ".join(missing_metadata)
            )
            result["resume"]["training_resume_possible"] = False
        invalid_optimizers = [
            name
            for name, report in result["optimizer_integrity"].items()
            if not report["valid"]
        ]
        if invalid_optimizers:
            result["warnings"].append(
                "Invalid optimizer state: " + ", ".join(sorted(invalid_optimizers))
            )
            result["resume"]["training_resume_possible"] = False
        if iteration is not None and isinstance(checkpoint.get("args"), Mapping):
            expected = _expected_steps(checkpoint, iteration)
            observed = {
                name: report["steps"]
                for name, report in result["optimizer_integrity"].items()
            }
            result["optimizer_steps"] = observed
            result["expected_optimizer_steps"] = expected
            if checkpoint["args"].get("resume") is not None:
                result["step_check"] = {
                    "status": "not_applicable",
                    "reason": "run resumed from an earlier checkpoint",
                }
            elif expected:
                passed = observed == expected
                result["step_check"] = {
                    "status": "passed" if passed else "failed",
                    "expected": expected,
                    "observed": observed,
                }
                if not passed:
                    result["structural_issues"].append(
                        "optimizer step counts do not match the upstream update schedule"
                    )
                    result["resume"]["training_resume_possible"] = False

    finite = all(
        report["nonfinite"] == 0
        for section in ("network_integrity", "optimizer_integrity")
        for report in result[section].values()
        if report["present"]
    )
    required = {"wm", "pi", "critic"} if result["format"] == "resumable" else WEIGHT_ONLY_NETWORKS
    structure_valid = all(
        result["network_integrity"].get(name, {}).get("valid", False) for name in required
    )
    optimizer_structure_valid = (
        result["format"] != "resumable"
        or all(
            report["valid"]
            for report in result["optimizer_integrity"].values()
            if report["present"]
        )
    )
    result["all_tensors_finite"] = finite
    result["passed"] = (
        result["format"] in {"weight_only", "resumable"}
        and structure_valid
        and optimizer_structure_valid
        and finite
        and not result["structural_issues"]
        and (
            not require_resume
            or (
                result["format"] == "resumable"
                and result["resume"]["training_resume_possible"]
            )
        )
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--require-resume",
        action="store_true",
        help="fail a valid weight-only checkpoint unless optimizer state is present",
    )
    args = parser.parse_args(argv)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    checkpoint = torch.load(
        args.checkpoint, map_location="cpu", mmap=True, weights_only=False
    )
    result = inspect_checkpoint(
        checkpoint, args.checkpoint, require_resume=args.require_resume
    )
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, allow_nan=False), flush=True)
    if not result["passed"]:
        raise RuntimeError("checkpoint validation failed")


if __name__ == "__main__":
    main()
