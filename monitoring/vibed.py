"""Read the unmodified supermimic_vibed CSV logs; never import torch or write logs."""
import csv
import json
import math
from pathlib import Path

from monitoring.status import process_identity
from monitoring.eta import estimate


def load_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def read_run(path: Path, name: str):
    args = load_json(path / "args.json")
    status = load_json(path / "status.json")
    scalars, last, error = {}, {}, None
    timing = []
    mapping = {
        "wm_loss": ("wm/loss", 1), "wm_err8": ("wm/nse_kstep", 1),
        "pi_loss": ("policy/actor_loss", 1), "v_loss": ("policy/critic_loss", 1),
        "pi_gradnorm": ("policy/policy_grad_norm", 1),
        "imag_rew": ("policy/imag_reward_mean", .1),
        "ep_ret_norm": ("train/episode_norm_return", 1),
        "sim_rew": ("train/step_norm_reward", 1), "wall_h": ("time/hours", 1),
    }
    try:
        with (path / "train_log.csv").open() as stream:
            for row in csv.DictReader(stream):
                if None in row or any(value is None for value in row.values()):
                    continue  # A concurrent writer may not have completed the last CSV row.
                try:
                    step = int(row["iteration"])
                    values = {key: float(row[key]) for key in mapping}
                except (ValueError, KeyError):
                    continue
                last = row
                if math.isfinite(values["wall_h"]):
                    timing.append((step,values["wall_h"]*3600))
                for key, (tag, scale) in mapping.items():
                    if tag.startswith("policy/") and step <= args.get("wm_only_iters", 500):
                        continue  # Upstream logs zero placeholders before any policy update.
                    value = values[key] * scale
                    scalars.setdefault(tag, []).append([step, value if math.isfinite(value) else None, None])
                if not all(math.isfinite(value) for value in values.values()):
                    error = f"原始 CSV 在 iteration={step} 记录非有限指标，请检查 stdout.log。"
    except FileNotFoundError:
        pass
    except OSError as exc:
        error = str(exc)
    iteration = int(last["iteration"]) if last else None
    if not status:
        completed = iteration is not None and args.get("iterations") is not None and iteration >= args["iterations"]
        status = dict(status="completed" if completed else "unknown", iteration=iteration,
                      elapsed_s=float(last["wall_h"])*3600 if last else None,
                      planned_iterations=args.get("iterations"),
                      stage="policy_bptt" if iteration is not None and iteration > args.get("wm_only_iters", 500) else "world_model")
    elif status.get("status") == "running":
        proc = process_identity(status.get("pid"))
        if not proc or proc["start_ticks"] != status.get("process_start_ticks") or proc["state"] == "Z":
            status = dict(status, status="error", error="训练进程已退出；保留原 CSV 的最后进度。")
        elif proc["state"] in ("T", "t"):
            status = dict(status, status="paused")
    if iteration is not None:
        status["iteration"] = iteration
    if status.get("planned_iterations") is None:
        status["planned_iterations"] = args.get("iterations")
    config = dict(
        env=dict(num_envs=args.get("num_envs"), anchor_obs="上游内置 6D 相对根朝向"),
        wm_trainer=dict(batch_size=args.get("wm_batch"), window=args.get("wm_window"), batches_per_update=args.get("wm_batches")),
        policy_trainer=dict(batch_size=args.get("pi_batch"), horizon=args.get("horizon"),
                            critic_epochs=args.get("critic_epochs"), critic_minibatches=args.get("critic_minibatches")),
        schedule=dict(total_iterations=args.get("iterations"), updates_per_env_step=args.get("utd")),
        observation_note="supermimic_vibed 原生观测：99×10，目标 73×10；保留上游 6D 相对根朝向。",
    )
    files = sorted(path.glob("ckpt_*.pt"), key=lambda p: p.stat().st_mtime, reverse=True)
    checkpoint = None
    if files:
        p = files[0]
        suffix = p.stem.removeprefix("ckpt_")
        checkpoint = dict(name=p.name, path=str(p), iteration=int(suffix) if suffix.isdigit() else None, saved_at=p.stat().st_mtime)
    elif (path / "last.pt").exists():
        p = path / "last.pt"
        checkpoint = dict(name=p.name, path=str(p), iteration=None, saved_at=p.stat().st_mtime)
    log = path / "train_log.csv"
    progress = estimate(timing,args,dict(status,status="error") if error else status,
        load_json(path/"launch.json"),summary=load_json(path/"training_summary.json"),
        result=load_json(path/"result.json"),log_mtime=log.stat().st_mtime if log.exists() else None)
    post_result = load_json(path/"post/result.json")
    if post_result.get("pipeline_completed"):
        progress["postprocess_note"] = "评测、视频已完成"
    elif post_result.get("error"):
        progress["postprocess_note"] = "后处理已停止，请查看异常"
    return dict(name=name, config=config, status=status, checkpoint=checkpoint, scalars=scalars,
                read_error=error, directory=str(path), source="vibed",progress=progress,
                log_path=str(path/"train_log.csv"),
                metric_notes={"wm/loss": "上游 CSV wm_loss：原状态预测损失 / wm_window",
                              "policy/actor_loss": "上游 CSV pi_loss：原始 −J，未除以 H",
                              "train/episode_norm_return": "上游 ep_ret_norm：按存活回合长度归一化；整条动作评测见 eval.csv",
                              "wm/nse_kstep": "上游 CSV wm_err8：训练窗口末步预测误差"})
