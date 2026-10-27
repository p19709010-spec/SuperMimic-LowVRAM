"""Plot real low-VRAM resource telemetry without importing training code."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main(input_csv: Path, output: Path, title: str) -> None:
    with input_csv.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise SystemExit(f"no resource samples in {input_csv}")

    started = float(rows[0]["wall_time"])
    elapsed = [float(row["wall_time"]) - started for row in rows]
    gpu_mib = [float(row["gpu_used_mib"]) for row in rows]
    cgroup_mib = [int(row["cgroup_bytes"]) / 2**20 for row in rows]
    swap_mib = [int(row["system_swap_growth_kib"]) / 1024 for row in rows]

    figure, axes = plt.subplots(2, 1, figsize=(9.5, 6.2), sharex=True)
    axes[0].plot(elapsed, gpu_mib, color="#2563eb", linewidth=1.8, label="GPU memory")
    axes[0].set_ylabel("GPU memory (MiB)")
    axes[0].grid(alpha=0.25)
    axes[0].legend(loc="upper left")

    axes[1].plot(elapsed, cgroup_mib, color="#059669", linewidth=1.6, label="cgroup RAM")
    axes[1].plot(elapsed, swap_mib, color="#dc2626", linewidth=1.6, label="whole-system Swap growth")
    axes[1].set_xlabel("Elapsed time (s)")
    axes[1].set_ylabel("MiB")
    axes[1].grid(alpha=0.25)
    axes[1].legend(loc="upper left")

    axes[0].set_title(title)
    figure.text(
        0.01,
        0.01,
        f"Source: {input_csv.name}. Telemetry only; this is not a tracking-quality result.",
        fontsize=8,
        color="#4b5563",
    )
    figure.tight_layout(rect=(0, 0.04, 1, 1))
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, format="svg", metadata={"Date": None})
    plt.close(figure)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--title", default="Low-VRAM resource telemetry")
    args = parser.parse_args()
    main(args.input_csv, args.output, args.title)
