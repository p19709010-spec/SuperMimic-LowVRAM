"""Serial postprocessing through upstream evaluation, recording, rendering and plotting tools."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from experiments.low_vram_vibed.config import load_upstream
from experiments.low_vram_vibed.provenance import require_clean_upstream
from monitoring.resources import ResourceMonitor
from monitoring.status import RunStatus


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--max-seconds", type=int, default=900)
    parser.add_argument("--max-system-swap-growth-mib", type=float)
    args = parser.parse_args()
    provenance = require_clean_upstream(load_upstream())
    repo = Path(provenance["path"])
    if Path(args.run_name).name != args.run_name or args.run_name in (".", ".."):
        parser.error("run name must be a single directory name")
    directory = repo / "logs" / args.run_name
    old_status = json.loads((directory / "status.json").read_text())
    if old_status["status"] != "completed":
        raise RuntimeError("postprocessing requires a normally completed training process")
    post = directory / "post"
    post.mkdir(exist_ok=False)
    rel = next(
        line.split(":", 2)[2].strip().lstrip("/")
        for line in Path("/proc/self/cgroup").read_text().splitlines()
        if line.startswith("0:")
    )
    group = Path("/sys/fs/cgroup") / rel
    maximum = (group / "memory.max").read_text().strip()
    if maximum == "max" or int(maximum) > 4 * 2**30:
        raise RuntimeError("postprocessing requires an effective <=4 GiB cgroup")
    # Freeze the recorded training completion before evaluation changes status.json.
    summary = directory / "training_summary.json"
    if not summary.exists():
        launch = json.loads((directory / "launch.json").read_text())
        temporary = summary.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(
                {
                    "started_at": old_status["started_at"],
                    "finished_at": old_status["updated_at"],
                    "elapsed_s": old_status["elapsed_s"],
                    "completed": True,
                    "iteration": old_status["iteration"],
                    "limit_seconds": launch.get("max_seconds"),
                },
                indent=2,
            )
        )
        temporary.replace(summary)
    status = RunStatus(directory, "evaluation")
    own = {key: status.data[key] for key in ("pid", "process_start_ticks")}
    status.data.update(old_status)
    status.data.update(own, status="running", stage="evaluation", planned_hours=None)
    status.started = old_status["started_at"]
    status.update()
    monitor = ResourceMonitor(
        post, group, max_system_swap_growth_mib=args.max_system_swap_growth_mib
    )
    monitor.start()
    stopped = {"signal": None}

    def stop(sig, _frame):
        stopped["signal"] = sig

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.update(
        UV_PROJECT_ENVIRONMENT=str(repo / ".venv"),
        UV_CACHE_DIR="/tmp/supermimic-vibed-uv",
        UV_PYTHON="/usr/bin/python3.12",
        UV_PYTHON_PREFERENCE="only-system",
        TORCHDYNAMO_DISABLE="1",
        TORCH_COMPILE_DISABLE="1",
        TORCHINDUCTOR_COMPILE_THREADS="1",
        MAX_JOBS="1",
        OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
        MUJOCO_GL="egl",
        WARP_CACHE_PATH=str(repo / ".cache/warp"),
        XDG_CACHE_HOME=str(repo / ".cache"),
        MPLCONFIGDIR="/tmp/supermimic-vibed-mpl",
    )
    environment["PATH"] = str(repo / ".cache/bin") + os.pathsep + environment.get("PATH", "")
    prefix = [
        shutil.which("uv"),
        "run",
        "--project",
        str(repo / "IsaacLab"),
        "--no-sync",
        "python",
        "-u",
    ]
    start = time.monotonic()
    result, child = {"pipeline_completed": False, "target_reached": False}, None

    def run(command, name, cpu_only=False):
        nonlocal child
        status.update(stage="evaluation", phase_detail=name)
        child_env = dict(environment)
        if cpu_only:
            child_env["CUDA_VISIBLE_DEVICES"] = ""
        with (post / (name + ".log")).open("x") as output:
            child = subprocess.Popen(
                prefix + list(map(str, command)),
                cwd=repo,
                env=child_env,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            while child.poll() is None:
                if (
                    monitor.issue
                    or stopped["signal"]
                    or time.monotonic() - start > args.max_seconds
                ):
                    raise RuntimeError(
                        monitor.issue
                        or f"postprocessing stopped; signal={stopped['signal']}, elapsed={time.monotonic() - start:.0f}s"
                    )
                time.sleep(2)
            if child.returncode:
                raise RuntimeError(
                    f"upstream {name} exited {child.returncode}; see {post / (name + '.log')}"
                )

    try:
        run(
            [
                ROOT / "scripts/vibed_check.py",
                "--checkpoint",
                directory / "last.pt",
                "--out",
                post / "checkpoint_validity.json",
            ],
            "checkpoint_check",
            True,
        )
        validity = json.loads((post / "checkpoint_validity.json").read_text())
        iteration = validity["iteration"]
        ckpt = directory / f"ckpt_{iteration:06d}.pt"
        if not ckpt.is_file():
            raise RuntimeError("numbered checkpoint does not match last.pt")
        cfg = json.loads((directory / "args.json").read_text())
        run(
            [
                "supermimic/evaluate.py",
                "--run_dir",
                directory,
                "--every",
                max(1, iteration // cfg["ckpt_every"]),
            ],
            "evaluate40",
        )
        metrics = json.loads(ckpt.with_name(ckpt.stem + "_eval.json").read_text())
        if not math.isfinite(metrics["norm_return"]):
            raise RuntimeError("nonfinite original evaluation return")
        motion = post / "visual_motion"
        motion.mkdir()
        shutil.copy2(repo / "data/lafan1_g1/walk1_subject1.csv", motion / "walk1_subject1.csv")
        trajectory = post / "trajectory_walk.npz"
        run(
            [
                "supermimic/evaluate.py",
                "--run_dir",
                directory,
                "--ckpt",
                ckpt,
                "--motion_dir",
                motion,
                "--record",
                trajectory,
            ],
            "record_walk",
        )
        video = directory / "g1_walk.mp4"
        title = f"supermimic_vibed it {iteration}; eval {metrics['norm_return']:.3f}; {metrics['n_failed']}/40 failed"
        run(
            [
                "tools/render.py",
                trajectory,
                video,
                "--clips",
                "walk1_subject1",
                "--seconds",
                "10",
                "--width",
                "960",
                "--height",
                "540",
                "--title",
                title,
            ],
            "render_walk",
        )
        run(["tools/plot.py", directory, "--out", directory / "success_curve.png"], "plot", True)
        if monitor.issue:
            raise RuntimeError(monitor.issue)
        result.update(
            pipeline_completed=True,
            target_reached=metrics["norm_return"] >= 0.82 and metrics["n_failed"] == 0,
            iteration=iteration,
            eval=metrics,
            video=str(video),
            curve=str(directory / "success_curve.png"),
            upstream_source_modified=False,
        )
        status.finish()
    except BaseException as error:
        result["error"] = str(error)
        status.finish(error)
        raise
    finally:
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=5)
        monitor.close()
        result.update(
            resource_peak=monitor.peak,
            resource_issue=monitor.issue,
            elapsed_s=time.monotonic() - start,
        )
        (post / "result.json").write_text(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
