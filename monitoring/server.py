"""Loopback dashboard: TensorBoard events + nvidia-smi, no torch/CUDA imports."""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
from monitoring.status import process_identity
from monitoring.vibed import read_run as read_vibed_run

ROOT = Path(__file__).resolve().parent


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


class Store:
    def __init__(self, logs):
        self.logs = logs.resolve()
        self.lock = threading.Lock()
        self.accumulators = {}
        self.cache = {}
        self.gpu = {"available": False, "error": "等待 nvidia-smi"}

    def run(self, name):
        path = (self.logs / name).resolve()
        if path.parent != self.logs or not path.is_dir():
            raise ValueError("unknown run")
        with self.lock:
            cached = self.cache.get(name)
            if cached and time.monotonic() - cached[0] < 2.5:
                return cached[1]
            if (path / "args.json").exists() or (path / "train_log.csv").exists():
                result = read_vibed_run(path, name)
                self.cache[name] = (time.monotonic(), result)
                return result
            config = read_json(path / "config.json")
            status = read_json(path / "status.json")
            audit = read_json(path / "audit.json")
            scalars, error = {}, None
            tb = path / "tb"
            if tb.is_dir():
                try:
                    acc = self.accumulators.setdefault(name, EventAccumulator(str(tb), size_guidance={"scalars": 0}))
                    acc.Reload()
                    for tag in acc.Tags()["scalars"]:
                        events = acc.Scalars(tag)
                        # Browser receives at most ~1500 evenly spaced real samples per curve.
                        stride = max(1, math.ceil(len(events) / 1500))
                        selected = events[::stride]
                        if events and (not selected or selected[-1] != events[-1]):
                            selected.append(events[-1])
                        scalars[tag] = [[v.step, v.value if math.isfinite(v.value) else None, v.wall_time] for v in selected]
                except Exception as exc:
                    error = str(exc)
            if status.get("status") == "running":
                proc = process_identity(status.get("pid"))
                if not proc or proc["start_ticks"] != status.get("process_start_ticks") or proc["state"] == "Z":
                    status = dict(status, status="error", error="进程已退出，未写入正常结束记录；保留最后进度。请检查该 run 的输出日志。")
                elif proc["state"] in ("T", "t"):
                    status = dict(status, status="paused")
                else:
                    status = dict(status, elapsed_s=time.time() - status["started_at"])
            if not status:
                status = dict(status="completed" if audit.get("elapsed_s") is not None else "unknown",
                              stage=audit.get("phase", "unknown"), elapsed_s=audit.get("elapsed_s"),
                              iteration=audit.get("iterations", audit.get("optimizer_steps")))
            checkpoint = status.get("checkpoint")
            files = sorted(path.glob("ckpt*.pt"), key=lambda p: p.stat().st_mtime, reverse=True)
            if files and (not checkpoint or files[0].stat().st_mtime > checkpoint["saved_at"] + 0.1):
                p = files[0]
                suffix = p.stem.removeprefix("ckpt_")
                iteration = int(suffix) if suffix.isdigit() else audit.get("iterations")
                checkpoint = dict(name=p.name, path=str(p), iteration=iteration, saved_at=p.stat().st_mtime)
            # Legacy logs have no lifecycle: do not infer "running" from fresh events.
            latest_steps = [values[-1][0] for values in scalars.values() if values]
            if latest_steps and status.get("iteration") is None:
                status["iteration"] = max(latest_steps)
            if status.get("elapsed_s") is None and scalars.get("time/hours"):
                status["elapsed_s"] = scalars["time/hours"][-1][1] * 3600
            result = dict(name=name, config=config, status=status, checkpoint=checkpoint,
                          scalars=scalars, read_error=error, directory=str(path))
            self.cache[name] = (time.monotonic(), result)
            return result

    def runs(self):
        if not self.logs.exists():
            return []
        def priority(path):
            status = read_json(path / "status.json")
            proc = process_identity(status.get("pid")) if status.get("status") == "running" else None
            live = bool(proc and proc["start_ticks"] == status.get("process_start_ticks") and proc["state"] != "Z")
            return live, status.get("updated_at", path.stat().st_mtime)
        paths = [p for p in self.logs.iterdir() if p.is_dir()
                 and any((p / n).exists() for n in ("tb", "config.json", "status.json", "args.json", "train_log.csv"))]
        return [p.name for p in sorted(paths, key=priority, reverse=True)]

    def poll_gpu(self):
        while True:
            try:
                command = ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu", "--format=csv,noheader,nounits"]
                result = subprocess.run(command, capture_output=True, text=True, timeout=2, check=True)
                rows = list(csv.reader(io.StringIO(result.stdout)))
                row = next((r for r in rows if "5060" in r[0]), rows[0])
                self.gpu = dict(available=True, name=row[0].strip(), total_mib=float(row[1]),
                                used_mib=float(row[2]), free_mib=float(row[3]), utilization=float(row[4]),
                                temperature=float(row[5]), sampled_at=time.time())
            except Exception as exc:
                self.gpu = dict(available=False, error=str(exc), sampled_at=time.time())
            time.sleep(3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-root", type=Path, default=Path("logs"))
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()
    store = Store(args.log_root)
    threading.Thread(target=store.poll_gpu, daemon=True).start()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            try:
                if parsed.path == "/api/runs":
                    data = dict(runs=store.runs(), gpu=store.gpu, sampled_at=time.time())
                elif parsed.path == "/api/run":
                    name = parse_qs(parsed.query).get("name", [""])[0]
                    data = store.run(name)
                elif parsed.path in ("/", "/index.html"):
                    self.respond((ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
                    return
                else:
                    self.send_error(404)
                    return
                self.respond(json.dumps(data, allow_nan=False).encode(), "application/json; charset=utf-8")
            except ValueError:
                self.send_error(404, "Unknown run")

        def respond(self, content, content_type):
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:")
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"SuperMimic dashboard: http://127.0.0.1:{args.port} | logs={store.logs}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
