"""Read resource telemetry and identify threshold crossings without running models."""

from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path
from typing import Any

MAX_SAMPLES = 3000
GIB = 2**30
MIB = 2**20


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _number(row: dict[str, str], key: str) -> float | None:
    try:
        value = float(row[key])
    except (KeyError, TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _sample(row: dict[str, str], first_wall_time: float) -> dict[str, float | None]:
    wall_time = _number(row, "wall_time")
    cgroup_bytes = _number(row, "cgroup_bytes")
    kernel_peak_bytes = _number(row, "cgroup_kernel_peak_bytes")
    tree_rss_kib = _number(row, "tree_rss_kib")
    available_kib = _number(row, "available_kib")
    cgroup_swap_bytes = _number(row, "cgroup_swap_bytes")
    tree_swap_kib = _number(row, "tree_swap_kib")
    system_swap_used_kib = _number(row, "system_swap_used_kib")
    system_swap_growth_kib = _number(row, "system_swap_growth_kib")
    return {
        "wall_time": wall_time,
        "relative_s": None if wall_time is None else max(0.0, wall_time - first_wall_time),
        "cgroup_ram_gib": None if cgroup_bytes is None else cgroup_bytes / GIB,
        "cgroup_kernel_peak_gib": None
        if kernel_peak_bytes is None
        else kernel_peak_bytes / GIB,
        "tree_rss_gib": None if tree_rss_kib is None else tree_rss_kib / 1024 / 1024,
        "host_available_gib": None if available_kib is None else available_kib / MIB,
        "cgroup_swap_mib": None if cgroup_swap_bytes is None else cgroup_swap_bytes / MIB,
        "tree_swap_mib": None if tree_swap_kib is None else tree_swap_kib / 1024,
        "system_swap_used_mib": None
        if system_swap_used_kib is None
        else system_swap_used_kib / 1024,
        "system_swap_growth_mib": None
        if system_swap_growth_kib is None
        else system_swap_growth_kib / 1024,
        "gpu_used_mib": _number(row, "gpu_used_mib"),
        "gpu_free_mib": _number(row, "gpu_free_mib"),
        "gpu_util_pct": _number(row, "gpu_util_pct"),
        "gpu_temp_c": _number(row, "gpu_temp_c"),
    }


def _guard_definitions(launch: dict[str, Any]) -> list[dict[str, Any]]:
    guards = [
        {
            "metric": "cgroup_kernel_peak_gib",
            "label": "训练 cgroup 内核 RAM 峰值",
            "limit": 3.75,
            "unit": "GiB",
            "direction": "above",
        },
        {
            "metric": "cgroup_swap_mib",
            "label": "训练 cgroup Swap",
            "limit": 256.0,
            "unit": "MiB",
            "direction": "above",
        },
        {
            "metric": "host_available_gib",
            "label": "主机可用 RAM",
            "limit": 2.0,
            "unit": "GiB",
            "direction": "below",
        },
    ]
    if "gpu_free_min_mib" in launch:
        guards.append(
            {
                "metric": "gpu_free_mib",
                "label": "GPU 空闲显存",
                "limit": float(launch["gpu_free_min_mib"]),
                "unit": "MiB",
                "direction": "below",
            }
        )
    growth_limit = launch.get("max_system_swap_growth_mib")
    if growth_limit is not None:
        guards.append(
            {
                "metric": "system_swap_growth_mib",
                "label": "整机 Swap 相对监控起点增长",
                "limit": float(growth_limit),
                "unit": "MiB",
                "direction": "above",
            }
        )
    return guards


def _crosses(value: float | None, guard: dict[str, Any]) -> bool:
    if value is None:
        return False
    if guard["direction"] == "above":
        return value > guard["limit"]
    return value < guard["limit"]


def _events(samples: list[dict[str, Any]], launch: dict[str, Any], result: dict) -> list[dict]:
    events = []
    for guard in _guard_definitions(launch):
        crossing = next(
            (sample for sample in samples if _crosses(sample[guard["metric"]], guard)),
            None,
        )
        if crossing is None:
            continue
        value = crossing[guard["metric"]]
        relation = ">" if guard["direction"] == "above" else "<"
        events.append(
            {
                **guard,
                "wall_time": crossing["wall_time"],
                "relative_s": crossing["relative_s"],
                "value": value,
                "reason": (
                    f"{guard['label']} {value:.6g} {guard['unit']} "
                    f"{relation} 阈值 {guard['limit']:g} {guard['unit']}"
                ),
                "confirmed_by_result": bool(result.get("resource_issue"))
                or bool(result.get("reason")),
            }
        )
    return sorted(events, key=lambda event: event["relative_s"])


def _summary(samples: list[dict[str, Any]], events: list[dict], result: dict) -> dict:
    def values(key):
        return [sample[key] for sample in samples if sample.get(key) is not None]

    gpu = values("gpu_used_mib")
    cgroup_ram = values("cgroup_ram_gib")
    kernel_peak = values("cgroup_kernel_peak_gib")
    tree_rss = values("tree_rss_gib")
    cgroup_swap = values("cgroup_swap_mib")
    tree_swap = values("tree_swap_mib")
    system_used = values("system_swap_used_mib")
    system_growth = values("system_swap_growth_mib")
    available = values("host_available_gib")
    return {
        "samples": len(samples),
        "duration_s": samples[-1]["relative_s"] if samples else None,
        "gpu_peak_mib": max(gpu) if gpu else None,
        "cgroup_ram_peak_gib": max(cgroup_ram) if cgroup_ram else None,
        "cgroup_kernel_peak_gib": max(kernel_peak) if kernel_peak else None,
        "tree_rss_peak_gib": max(tree_rss) if tree_rss else None,
        "cgroup_swap_peak_mib": max(cgroup_swap) if cgroup_swap else None,
        "tree_swap_peak_mib": max(tree_swap) if tree_swap else None,
        "system_swap_used_start_mib": system_used[0] if system_used else None,
        "system_swap_used_peak_mib": max(system_used) if system_used else None,
        "system_swap_growth_peak_mib": max(system_growth) if system_growth else None,
        "host_available_min_gib": min(available) if available else None,
        "trigger_count": len(events),
        "stop_reason": result.get("resource_issue") or result.get("reason"),
    }


def read_resource_history(directory: str | Path) -> dict[str, Any]:
    directory = Path(directory)
    path = directory / "resources.csv"
    launch = _json(directory / "launch.json")
    result = _json(directory / "result.json")
    samples: list[dict[str, Any]] = []
    try:
        with path.open(newline="") as stream:
            reader = csv.DictReader(stream)
            first_wall_time = None
            for row in reader:
                wall_time = _number(row, "wall_time")
                if wall_time is None:
                    continue
                if first_wall_time is None:
                    first_wall_time = wall_time
                samples.append(_sample(row, first_wall_time))
    except (OSError, csv.Error):
        samples = []

    events = _events(samples, launch, result) if samples else []
    summary = _summary(samples, events, result)
    intervals = [
        current["wall_time"] - previous["wall_time"]
        for previous, current in zip(samples, samples[1:])
        if current["wall_time"] is not None and previous["wall_time"] is not None
    ]
    stride = max(1, math.ceil(len(samples) / MAX_SAMPLES))
    selected = samples[::stride]
    if samples and (not selected or selected[-1]["wall_time"] != samples[-1]["wall_time"]):
        selected.append(samples[-1])
    return {
        "source": "resources.csv",
        "available": bool(samples),
        "samples": selected,
        "summary": summary,
        "events": events,
        "guards": _guard_definitions(launch),
        "sample_interval_s": statistics.median(intervals) if intervals else None,
        "downsampled": stride > 1,
    }
