"""Low-rate process-tree/cgroup telemetry; no model imports and no restart policy."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import threading
import time


class ResourceMonitor:
    def __init__(self, directory, cgroup, interval=3, min_gpu_free_mib=768,
                 max_system_swap_growth_mib=None):
        self.directory = Path(directory)
        self.cgroup = Path(cgroup)
        self.interval = interval
        self.min_gpu_free_mib = min_gpu_free_mib
        self.max_system_swap_growth_mib = max_system_swap_growth_mib
        self.issue = None
        self.samples = 0
        self.peak = {}
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.thread.start()

    def run(self):
        fields = ["wall_time", "cgroup_bytes", "cgroup_swap_bytes", "tree_rss_kib", "tree_swap_kib",
                  "available_kib", "system_swap_used_kib", "system_swap_growth_kib", "cgroup_kernel_peak_bytes",
                  "gpu_used_mib", "gpu_free_mib", "gpu_util_pct", "gpu_temp_c"]
        failures = 0
        initial_system_swap = None
        with (self.directory / "resources.csv").open("x", buffering=1) as f:
            writer = csv.DictWriter(f, fields)
            writer.writeheader()
            while not self.stop.is_set():
                try:
                    row = dict(wall_time=time.time(),
                        cgroup_bytes=int((self.cgroup / "memory.current").read_text()),
                        cgroup_swap_bytes=int((self.cgroup / "memory.swap.current").read_text()),
                        tree_rss_kib=0, tree_swap_kib=0)
                    for path in self.cgroup.rglob("cgroup.procs"):
                        for pid in path.read_text().split():
                            try:
                                lines = Path(f"/proc/{pid}/status").read_text().splitlines()
                                values = {line.split(":",1)[0]:line.split()[1] for line in lines if line.startswith(("VmRSS:","VmSwap:"))}
                                row["tree_rss_kib"] += int(values.get("VmRSS",0))
                                row["tree_swap_kib"] += int(values.get("VmSwap",0))
                            except OSError:
                                pass
                    memory = {line.split(":")[0]: int(line.split()[1]) for line in Path("/proc/meminfo").read_text().splitlines()}
                    row["available_kib"] = memory["MemAvailable"]
                    row["system_swap_used_kib"] = memory["SwapTotal"] - memory["SwapFree"]
                    if initial_system_swap is None:
                        initial_system_swap = row["system_swap_used_kib"]
                    row["system_swap_growth_kib"] = row["system_swap_used_kib"] - initial_system_swap
                    peak_file = self.cgroup / "memory.peak"
                    row["cgroup_kernel_peak_bytes"] = max(row["cgroup_bytes"], int(peak_file.read_text())) if peak_file.exists() else row["cgroup_bytes"]
                    query = ["nvidia-smi", "--query-gpu=memory.used,memory.free,utilization.gpu,temperature.gpu", "--format=csv,noheader,nounits"]
                    output = subprocess.run(query, capture_output=True, text=True, timeout=2, check=True).stdout.splitlines()[0]
                    for key,value in zip(fields[-4:],output.split(",")):
                        row[key] = float(value.strip())
                    writer.writerow(row)
                    self.samples += 1
                    for key in ("cgroup_bytes","cgroup_kernel_peak_bytes","cgroup_swap_bytes","tree_rss_kib","tree_swap_kib","gpu_used_mib","system_swap_growth_kib"):
                        self.peak[key] = max(self.peak.get(key,0), row[key])
                    if row["cgroup_kernel_peak_bytes"] > 3.75*2**30:
                        self.issue = "cgroup RAM exceeded 3.75 GiB stop threshold"
                    elif row["cgroup_swap_bytes"] > 256*2**20:
                        self.issue = "cgroup swap exceeded 256 MiB stop threshold"
                    elif self.max_system_swap_growth_mib is not None and row["system_swap_growth_kib"] > self.max_system_swap_growth_mib*1024:
                        self.issue = f"system Swap grew by {row['system_swap_growth_kib']/1024:g} MiB (allowed {self.max_system_swap_growth_mib:g} MiB)"
                    elif row["available_kib"] < 2*2**20:
                        self.issue = "system available RAM fell below 2 GiB"
                    elif row["gpu_free_mib"] < self.min_gpu_free_mib:
                        self.issue = f"GPU free memory fell below {self.min_gpu_free_mib:g} MiB"
                    failures = 0
                    tmp = self.directory / "resources_latest.tmp"
                    tmp.write_text(json.dumps(dict(latest=row,peak=self.peak,issue=self.issue,samples=self.samples),indent=2))
                    tmp.replace(self.directory / "resources_latest.json")
                except Exception as error:
                    failures += 1
                    if failures >= 3:
                        self.issue = f"resource telemetry failed repeatedly: {error}"
                self.stop.wait(self.interval)

    def close(self):
        self.stop.set()
        self.thread.join(timeout=3)
