"""Failed clips must forfeit the unplayed part of the reference reward budget."""
import pytest
from supermimic.eval.benchmark import ClipResult, normalized_return, summarize


def test_early_failure_uses_full_reference_budget():
    assert normalized_return(0.2, frames=11) == pytest.approx(0.2)
    assert normalized_return(1.0, frames=11) == pytest.approx(1.0)


def test_aggregate_weights_reference_duration():
    results = [ClipResult("short", 11, 2, .2, True, 2),
               ClipResult("long", 21, 20, 1., False, -1)]
    summary = summarize(results)
    assert summary["failed"] == 1
    assert summary["step_weighted_norm_return"] == pytest.approx(22 / 30)


def test_short_clip_queue_stops_at_last_reference_transition(tmp_path):
    """Real MuJoCo: staggered clip lengths exercise explicit-reset queue ordering."""
    from pathlib import Path
    import numpy as np
    import torch
    from supermimic.eval.benchmark import run_benchmark
    source = Path(__file__).resolve().parents[1] / "data/npz/lafan1/walk1_subject1.npz"
    if not torch.cuda.is_available() or not source.exists():
        pytest.skip("needs CUDA + LAFAN1 npz")
    lengths = (3, 4, 5, 6)
    files = []
    with np.load(source) as data:
        original_length = len(data["joint_pos"])
        for i, length in enumerate(lengths):
            path = tmp_path / f"short_{i}.npz"
            np.savez(path, **{k: (data[k][:length] if data[k].ndim and data[k].shape[0] == original_length else data[k]) for k in data.files})
            files.append(str(path))
    def policy(obs, goal):
        return torch.zeros(len(obs), 29, device=obs.device)
    results = run_benchmark(policy, files, num_envs=2, verbose=False)
    assert [r.steps for r in results] == [n - 1 for n in lengths]
    assert not any(r.failed for r in results)
    assert all(r.tracking_errors is not None for r in results)
