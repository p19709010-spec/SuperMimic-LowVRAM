"""Compare native CSV throughput and sampled resources, without loading models."""

import argparse
import csv
import json
import math
import statistics
from pathlib import Path


def load(path):
    return json.loads(path.read_text())


def measure(directory, start=500, end=900):
    config = load(directory / "args.json")
    result = load(directory / "result.json")
    launch = load(directory / "launch.json")
    rows = [
        {k: float(v) for k, v in row.items()}
        for row in csv.DictReader((directory / "train_log.csv").open())
    ]
    if not all(math.isfinite(v) for row in rows for v in row.values()):
        raise ValueError(f"nonfinite native CSV: {directory}")
    selected = [r for r in rows if start <= r["iteration"] <= end]
    if len(selected) < 2 or selected[0]["iteration"] != start or selected[-1]["iteration"] != end:
        raise ValueError(f"requested measurement window incomplete: {directory}")
    first, last = selected[0], selected[-1]
    seconds = (last["wall_h"] - first["wall_h"]) * 3600
    iterations = last["iteration"] - first["iteration"]
    rate = iterations / seconds
    resources = [
        {k: float(v) for k, v in r.items()}
        for r in csv.DictReader((directory / "resources.csv").open())
    ]
    # Native wall_h is relative to t_start; CSV mtime is the last flush's epoch.
    # This aligns low-rate GPU samples approximately, not per-kernel profiling.
    offset = (directory / "train_log.csv").stat().st_mtime - rows[-1]["wall_h"] * 3600
    active = [
        r
        for r in resources
        if offset + first["wall_h"] * 3600 <= r["wall_time"] <= offset + last["wall_h"] * 3600
    ]
    peak = result["resource_peak"]
    kernel_peak = peak.get("cgroup_kernel_peak_bytes", peak["cgroup_bytes"])
    swap_samples = [r["system_swap_growth_kib"] for r in resources if "system_swap_growth_kib" in r]
    swap_growth_mib = max(0, max(swap_samples)) / 1024 if swap_samples else None
    swap_limit = launch.get("max_system_swap_growth_mib")
    safe = (
        result.get("returncode") == 0
        and not result.get("reason")
        and not result.get("resource_issue")
        and kernel_peak < 3.75 * 2**30
        and peak["cgroup_swap_bytes"] <= 256 * 2**20
        and (launch.get("memory_swap_max") != "0" or peak["cgroup_swap_bytes"] == 0)
        and (swap_limit is None or swap_growth_mib is not None and swap_growth_mib <= swap_limit)
        and min(r["gpu_free_mib"] for r in resources) >= launch.get("gpu_free_min_mib", 768)
        and min(r["available_kib"] for r in resources) >= 2 * 2**20
    )
    return {
        "run": directory.name,
        "config": {
            k: config[k] for k in ("num_envs", "wm_batch", "pi_batch", "horizon", "iterations")
        },
        "window": [start, end],
        "measured_seconds": seconds,
        "iterations_per_second": rate,
        "simulation_transitions_per_second": (last["sim_steps"] - first["sim_steps"]) / seconds,
        "wm_windows_per_second": rate * config["wm_batches"] * config["wm_batch"],
        "imagination_transitions_per_second": rate * config["horizon"] * config["pi_batch"],
        "gpu_util_mean_percent": statistics.mean(r["gpu_util_pct"] for r in active)
        if active
        else None,
        "gpu_util_samples": len(active),
        "gpu_util_note": f"{launch.get('resource_interval', 3)}-second whole-device samples, approximately aligned to CSV window",
        "sampled_gpu_peak_mib": peak["gpu_used_mib"],
        "sampled_cgroup_ram_peak_gib": peak["cgroup_bytes"] / 2**30,
        "kernel_cgroup_ram_peak_gib": kernel_peak / 2**30,
        "sampled_cgroup_swap_peak_mib": peak["cgroup_swap_bytes"] / 2**20,
        "max_system_swap_growth_mib": swap_growth_mib,
        "sampled_process_tree_rss_peak_mib": peak["tree_rss_kib"] / 1024,
        "sampled_process_tree_swap_peak_mib": peak["tree_swap_kib"] / 1024,
        "host_available_min_gib": min(r["available_kib"] for r in resources) / 2**20,
        "resource_safe": safe,
        "native_csv_finite": True,
        "elapsed_seconds": result["elapsed_s"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    baseline, candidate = measure(args.baseline), measure(args.candidate)
    ratio = candidate["iterations_per_second"] / baseline["iterations_per_second"]
    samples = (
        candidate["simulation_transitions_per_second"]
        / baseline["simulation_transitions_per_second"]
    )
    result = {
        "baseline": baseline,
        "candidate": candidate,
        "iterations_per_second_ratio": ratio,
        "simulation_throughput_ratio": samples,
        "iteration_speed_improved": ratio > 1,
        "sample_throughput_improved": samples > 1,
        "resource_safe": candidate["resource_safe"],
        "recommended_for_sample_throughput": candidate["resource_safe"] and samples > 1.05,
        "recommended_for_iteration_speed": candidate["resource_safe"] and ratio > 1.05,
        "caveat": "Fresh runs, same 500–900 BPTT window; hardware load and sample distributions can differ. This is a performance check, not a tracking-quality result.",
        "formal_training_launched": False,
    }
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
