"""Run unmodified upstream training with lifecycle, profile and resource guards."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from experiments.low_vram_vibed.config import load_profile, load_upstream
from experiments.low_vram_vibed.provenance import require_clean_upstream
from monitoring.resources import ResourceMonitor
from monitoring.status import RunStatus
from monitoring.vibed import read_run


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--config", type=Path, help="validated profile from experiments/low_vram_vibed/configs"
    )
    p.add_argument("--run-name")
    p.add_argument("--iterations", type=int, default=510)
    p.add_argument("--num-envs", type=int, default=16)
    p.add_argument("--wm-batch", type=int, default=32)
    p.add_argument("--pi-batch", type=int, default=32)
    p.add_argument("--horizon", type=int, default=32)
    p.add_argument("--checkpoint-every", type=int, default=2000)
    p.add_argument("--max-seconds", type=int, default=900)
    p.add_argument("--time-budget-progress", action="store_true")
    p.add_argument("--require-zero-swap", action="store_true")
    p.add_argument("--resource-interval", type=float, default=3)
    p.add_argument("--gpu-free-min-mib", type=float, default=768)
    p.add_argument("--max-system-swap-growth-mib", type=float)
    p.add_argument(
        "--allow-unverified",
        action="store_true",
        help="explicitly allow an experimental or untested profile",
    )
    return p


def _apply_profile(p: argparse.ArgumentParser, args: argparse.Namespace) -> dict | None:
    if args.config is None:
        return None
    profile = load_profile(args.config)
    if profile["status"] != "verified" and not args.allow_unverified:
        p.error(
            f"profile {profile['name']!r} is {profile['status']}; pass --allow-unverified explicitly"
        )
    for key in (
        "iterations",
        "num_envs",
        "wm_batch",
        "pi_batch",
        "horizon",
        "checkpoint_every",
        "max_seconds",
        "require_zero_swap",
        "resource_interval",
        "gpu_free_min_mib",
        "max_system_swap_growth_mib",
    ):
        setattr(args, key, profile[key])
    args.run_name = args.run_name or profile["run_name"]
    return profile


def main(argv: list[str] | None = None) -> None:
    p = build_parser()
    args = p.parse_args(argv)
    profile = _apply_profile(p, args)
    if not args.run_name:
        p.error("--run-name is required when --config is not supplied")
    if not 0.5 <= args.resource_interval <= 30 or args.gpu_free_min_mib < 512:
        p.error("resource interval must be 0.5–30 s and GPU reserve at least 512 MiB")
    if args.max_system_swap_growth_mib is not None and args.max_system_swap_growth_mib < 0:
        p.error("allowed system swap growth must be nonnegative")
    upstream = load_upstream()
    provenance = require_clean_upstream(upstream)
    repo = Path(provenance["path"])
    if not (repo / ".venv/bin/python").is_file():
        raise RuntimeError(
            "upstream virtual environment is missing; follow experiments/low_vram_vibed/README.md"
        )
    directory = repo / "logs" / args.run_name
    if directory.parent != repo / "logs" or Path(args.run_name).name != args.run_name:
        p.error("run name must be a single directory name")
    rel = next(
        line.split(":", 2)[2].strip().lstrip("/")
        for line in Path("/proc/self/cgroup").read_text().splitlines()
        if line.startswith("0:")
    )
    group = Path("/sys/fs/cgroup") / rel
    maximum = (group / "memory.max").read_text().strip()
    if maximum == "max" or int(maximum) > 4 * 2**30:
        raise RuntimeError("run only inside an effective <=4 GiB cgroup")
    swap_maximum = (group / "memory.swap.max").read_text().strip()
    if args.require_zero_swap and swap_maximum != "0":
        raise RuntimeError("zero-swap run requires effective memory.swap.max=0")
    directory.mkdir(parents=True, exist_ok=False)
    status = RunStatus(
        directory,
        "initializing",
        planned_iterations=args.iterations,
        planned_hours=args.max_seconds / 3600 if args.time_budget_progress else None,
    )
    command = [
        str(repo / ".venv/bin/python"),
        "-u",
        "supermimic/train.py",
        "--num_envs",
        str(args.num_envs),
        "--wm_batch",
        str(args.wm_batch),
        "--pi_batch",
        str(args.pi_batch),
        "--horizon",
        str(args.horizon),
        "--iterations",
        str(args.iterations),
        "--log_every",
        "10",
        "--ckpt_every",
        str(args.checkpoint_every),
        "--log_dir",
        str(directory),
    ]
    (directory / "launch.json").write_text(
        json.dumps(
            {
                "command": command,
                "cgroup": str(group),
                "memory_max": maximum,
                "memory_swap_max": swap_maximum,
                "max_seconds": args.max_seconds,
                "resource_interval": args.resource_interval,
                "gpu_free_min_mib": args.gpu_free_min_mib,
                "max_system_swap_growth_mib": args.max_system_swap_growth_mib,
                "upstream_repository": upstream["repository"],
                "upstream_commit": provenance["commit"],
                "upstream_source_modified": False,
                "profile": None
                if profile is None
                else {
                    "name": profile["name"],
                    "status": profile["status"],
                    "scope": profile["scope"],
                },
            },
            indent=2,
        )
    )
    monitor = ResourceMonitor(
        directory,
        group,
        interval=args.resource_interval,
        min_gpu_free_mib=args.gpu_free_min_mib,
        max_system_swap_growth_mib=args.max_system_swap_growth_mib,
    )
    stopped = {"signal": None}

    def stop(sig, _frame):
        stopped["signal"] = sig

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    child, reason = None, None
    start = time.monotonic()
    try:
        child_env = os.environ.copy()
        child_env.pop("PYTHONPATH", None)
        child_env.update(
            TORCHDYNAMO_DISABLE="1",
            TORCH_COMPILE_DISABLE="1",
            TORCHINDUCTOR_COMPILE_THREADS="1",
            MAX_JOBS="1",
            OMP_NUM_THREADS="1",
            MKL_NUM_THREADS="1",
            OPENBLAS_NUM_THREADS="1",
            WARP_CACHE_PATH=str(repo / ".cache/warp"),
            TORCHINDUCTOR_CACHE_DIR=str(repo / ".cache/inductor"),
            XDG_CACHE_HOME=str(repo / ".cache"),
            MPLCONFIGDIR="/tmp/supermimic-vibed-mpl",
        )
        with (directory / "stdout.log").open("x") as output:
            child = subprocess.Popen(
                command,
                cwd=repo,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                env=child_env,
            )
            monitor.start()
            while child.poll() is None:
                view = read_run(directory, args.run_name)
                iteration = view["status"].get("iteration")
                stage = (
                    "initializing"
                    if iteration is None
                    else "world_model"
                    if iteration <= 500
                    else "policy_bptt"
                )
                status.update(iteration=iteration, stage=stage, child_pid=child.pid)
                if (
                    monitor.issue
                    or view["read_error"]
                    or stopped["signal"]
                    or time.monotonic() - start > args.max_seconds
                ):
                    reason = monitor.issue or view["read_error"]
                    if reason is None:
                        reason = (
                            f"stop signal {stopped['signal']}"
                            if stopped["signal"]
                            else "training time budget reached"
                        )
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait(timeout=5)
                    break
                time.sleep(3)
        if reason is None and stopped["signal"]:
            reason = f"stop signal {stopped['signal']}"
        if reason or child.returncode:
            raise RuntimeError(
                reason or f"upstream exited with code {child.returncode}; inspect stdout.log"
            )
        final = read_run(directory, args.run_name)
        if final["read_error"] or monitor.issue:
            raise RuntimeError(final["read_error"] or monitor.issue)
        status.update(
            iteration=(final.get("checkpoint") or {}).get("iteration")
            or final["status"].get("iteration")
        )
        status.finish()
    except BaseException as error:
        status.finish(error)
        raise
    finally:
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
        if monitor.thread.ident is not None:
            monitor.close()
        result = {
            "returncode": child.returncode if child else None,
            "reason": reason,
            "resource_peak": monitor.peak,
            "resource_issue": monitor.issue,
            "elapsed_s": time.monotonic() - start,
        }
        (directory / "result.json").write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
