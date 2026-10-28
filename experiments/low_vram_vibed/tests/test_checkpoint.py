from __future__ import annotations

import math

import torch

from experiments.low_vram_vibed.checkpoint import inspect_checkpoint


def _weight_only_checkpoint() -> dict:
    return {
        "pi": {
            "enc.0.weight": torch.tensor([[1.0]]),
            "dec.0.bias": torch.tensor([0.0]),
            "obs_norm.mean": torch.tensor([0.0]),
            "goal_norm.mean": torch.tensor([0.0]),
        },
        "wm": {
            "net.0.weight": torch.tensor([[1.0]]),
            "in_norm.mean": torch.tensor([0.0]),
            "out_norm.mean": torch.tensor([0.0]),
        },
        "iteration": 900,
        "wall_time": 1.0,
        "sim_steps": 100,
        "args": {"resume": None},
        "saved_at": "2026-10-27 00:00:00",
    }


def _optimizer(step: int) -> dict:
    return {
        "state": {
            0: {
                "step": torch.tensor(step),
                "exp_avg": torch.tensor([0.0]),
                "exp_avg_sq": torch.tensor([0.0]),
            }
        },
        "param_groups": [{"params": [0], "lr": 0.0002}],
    }


def _resumable_checkpoint() -> dict:
    checkpoint = _weight_only_checkpoint()
    checkpoint["critic"] = {"net.0.weight": torch.tensor([[1.0]])}
    checkpoint["opt_wm"] = _optimizer(9000)
    checkpoint["opt_pi"] = _optimizer(400)
    checkpoint["opt_v"] = _optimizer(8000)
    checkpoint["args"] = {
        "resume": None,
        "wm_only_iters": 500,
        "wm_batches": 10,
        "critic_epochs": 5,
        "critic_minibatches": 4,
    }
    return checkpoint


def test_weight_only_checkpoint_is_valid_but_not_resumable():
    result = inspect_checkpoint(_weight_only_checkpoint())

    assert result["format"] == "weight_only"
    assert result["passed"]
    assert result["all_tensors_finite"]
    assert result["resume"] == {
        "optimizer_state_present": False,
        "training_resume_possible": False,
        "exact_recovery_confirmed": False,
    }
    assert any("cannot be confirmed" in warning for warning in result["warnings"])
    assert "opt_wm" not in result.get("optimizer_steps", {})


def test_require_resume_rejects_weight_only_without_key_error():
    result = inspect_checkpoint(_weight_only_checkpoint(), require_resume=True)

    assert not result["passed"]
    assert result["format"] == "weight_only"
    assert any("weight-only" in warning.lower() for warning in result["warnings"])


def test_resumable_checkpoint_checks_network_optimizer_and_step_counts():
    result = inspect_checkpoint(_resumable_checkpoint())

    assert result["format"] == "resumable"
    assert result["passed"]
    assert result["resume"]["optimizer_state_present"]
    assert result["resume"]["training_resume_possible"]
    assert not result["resume"]["exact_recovery_confirmed"]
    assert result["optimizer_steps"] == {
        "opt_wm": [9000],
        "opt_pi": [400],
        "opt_v": [8000],
    }
    assert result["step_check"]["status"] == "passed"
    assert any("replay buffer" in warning for warning in result["warnings"])


def test_missing_optimizer_component_is_reported_not_raised():
    checkpoint = _resumable_checkpoint()
    del checkpoint["opt_pi"]

    result = inspect_checkpoint(checkpoint)

    assert result["format"] == "partial"
    assert not result["passed"]
    assert not result["resume"]["training_resume_possible"]
    assert any("opt_pi" in issue for issue in result["structural_issues"])


def test_nonfinite_network_tensor_fails_structure_check():
    checkpoint = _weight_only_checkpoint()
    checkpoint["wm"]["net.0.weight"] = torch.tensor([[math.nan]])

    result = inspect_checkpoint(checkpoint)

    assert not result["passed"]
    assert result["network_integrity"]["wm"]["nonfinite"] == 1
    assert not result["all_tensors_finite"]


def test_optimizer_step_mismatch_fails_resume_validation():
    checkpoint = _resumable_checkpoint()
    checkpoint["opt_pi"] = _optimizer(399)

    result = inspect_checkpoint(checkpoint, require_resume=True)

    assert not result["passed"]
    assert result["step_check"]["status"] == "failed"
    assert not result["resume"]["training_resume_possible"]
