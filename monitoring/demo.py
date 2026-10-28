"""Summarize demo provenance and evidence from retained run metadata."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _latest_eval(path: Path) -> dict[str, str]:
    latest = {}
    try:
        with path.open(newline="") as stream:
            for row in csv.DictReader(stream):
                if row.get("iteration"):
                    latest = row
    except (OSError, csv.Error):
        pass
    return latest


def read_demo_metadata(
    directory: str | Path,
    name: str,
    source: str,
    status: dict[str, Any],
    checkpoint: dict[str, Any] | None,
) -> dict[str, Any]:
    directory = Path(directory)
    args = _json(directory / "args.json")
    post = _json(directory / "post/result.json")
    evaluation = _latest_eval(directory / "eval.csv")
    result = _json(directory / "result.json")
    track = "Track B" if source == "vibed" else "Track A"
    checkpoint_iteration = None
    for value in (
        (checkpoint or {}).get("iteration"),
        evaluation.get("iteration"),
        post.get("iteration"),
    ):
        try:
            checkpoint_iteration = int(value)
            break
        except (TypeError, ValueError):
            continue
    try:
        training_iteration = int(status.get("iteration"))
    except (TypeError, ValueError):
        training_iteration = checkpoint_iteration

    dataset = "未从 run 元数据确认"
    motion_dir = args.get("motion_dir")
    if isinstance(motion_dir, str):
        if "lafan1" in motion_dir.lower():
            dataset = "LAFAN1 G1 retargets · 40 clips"
        else:
            dataset = Path(motion_dir).name

    if source == "vibed":
        model = "zita-ch/supermimic_vibed · World Model / Policy / Critic（上游源码未修改）"
        upstream = "a1508d42c9d1699a52e8233ab16d08c488441ab9"
    else:
        model = "src/supermimic 独立 mjlab 实现 · World Model / Actor / Critic"
        upstream = None

    if args:
        run_mode = "resume" if args.get("resume") else "fresh"
        if evaluation or post:
            run_mode += " training + native evaluation/postprocessing"
        else:
            run_mode += " training"
    else:
        run_mode = "未从 args.json 确认"

    metric = None
    if evaluation:
        metric = {
            "normalized_return": evaluation.get("norm_return"),
            "normalized_return_framew": evaluation.get("norm_return_framew"),
            "failed_clips": evaluation.get("n_failed"),
            "total_clips": 40,
            "eval_iteration": evaluation.get("iteration"),
            "eval_at": evaluation.get("eval_at"),
        }

    artifact_names = (
        "ckpt_014000_eval.json",
        "ckpt_000600_eval.json",
        "eval.csv",
        "g1_walk.mp4",
        "smoke510_walk_NOT_CONVERGED.mp4",
        "success_curve.png",
        "post/checkpoint_validity.json",
        "post/trajectory_walk.npz",
    )
    artifacts = [
        {"name": relative, "size_bytes": (directory / relative).stat().st_size}
        for relative in artifact_names
        if (directory / relative).is_file()
    ]

    incomplete = []
    if status.get("status") == "error":
        incomplete.append("run 被保护或异常停止")
    if evaluation and post and post.get("target_reached") is False:
        incomplete.append("完整 40 动作评测完成，但未达到目标质量")
    if not evaluation:
        incomplete.append("未生成原生 40 动作评测结果")
    if not artifacts:
        incomplete.append("未保留机器人演示媒体")
    if result.get("reason"):
        incomplete.append("资源保护触发：" + str(result["reason"]))
    if not incomplete:
        incomplete.append("未声明稳定长训或论文级复现")

    return {
        "track": track,
        "run": name,
        "source": (
            f"pinned upstream {upstream}"
            if upstream
            else "project-authored Track A source"
        ),
        "checkpoint_iteration": checkpoint_iteration,
        "training_iteration": training_iteration,
        "dataset": dataset,
        "model": model,
        "run_mode": run_mode,
        "metrics": metric,
        "pipeline_completed": post.get("pipeline_completed"),
        "target_reached": post.get("target_reached"),
        "incomplete": incomplete,
        "artifacts": artifacts,
        "rights": [
            {
                "asset": "LAFAN1 G1 动作数据",
                "status": "CC BY-NC-ND 4.0；不随 PUBLIC 清单分发",
            },
            {
                "asset": "Unitree G1 机器人模型/网格",
                "status": "上游标注 BSD-3-Clause；需保留通知，当前不进入 PUBLIC 清单",
            },
            {
                "asset": "本地生成视频和渲染图",
                "status": "由受限动作与机器人资产生成；公开授权未确认，仅 LOCAL_ONLY",
            },
            {
                "asset": "supermimic_vibed 上游演示媒体",
                "status": "来源与再利用授权未单独确认；不得自动纳入 PUBLIC",
            },
        ],
        "publication": {
            "status": "LOCAL_ONLY",
            "reason": "动作数据、机器人资产、checkpoint 与演示媒体的公开再分发授权未完成。",
        },
    }
