"""Monitor reads events without loading checkpoints or creating CUDA tensors."""
import json
import time
import sys
from pathlib import Path

import pytest
from tensorboard.compat.proto.event_pb2 import Event
from tensorboard.compat.proto.summary_pb2 import Summary
from tensorboard.summary.writer.event_file_writer import EventFileWriter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from monitoring.demo import read_demo_metadata
from monitoring.resource_history import read_resource_history
from monitoring.server import Store


def test_real_tensorboard_scalars_and_dead_process(tmp_path):
    run = tmp_path / "trial"
    writer = EventFileWriter(str(run / "tb"))
    writer.add_event(Event(wall_time=time.time(), step=7,
                           summary=Summary(value=[Summary.Value(tag="wm/loss", simple_value=1.25)])))
    writer.close()
    (run / "config.json").write_text(json.dumps({"env": {"num_envs": 16}}))
    (run / "status.json").write_text(json.dumps(dict(status="running", pid=999999999,
                 process_start_ticks="missing", started_at=time.time(), iteration=7)))
    store = Store(tmp_path)
    result = store.run("trial")
    assert result["scalars"]["wm/loss"][0][:2] == [7, 1.25]
    assert result["status"]["status"] == "error"
    assert result["status"]["iteration"] == 7
    assert "进程已退出" in result["status"]["error"]
    with pytest.raises(ValueError):
        store.run("../outside")


def test_no_data_does_not_invent_progress(tmp_path):
    run = tmp_path / "empty"
    run.mkdir()
    result = Store(tmp_path).run("empty")
    assert result["scalars"] == {}
    assert result["status"]["iteration"] is None
    assert result["status"]["status"] == "unknown"
    assert result["checkpoint"] is None
    assert result["resources"]["available"] is False
    assert result["demo"]["track"] == "Track A"


def test_resource_history_reports_real_swap_threshold_crossing(tmp_path):
    run = tmp_path / "swap"
    run.mkdir()
    (run / "resources.csv").write_text(
        "wall_time,cgroup_bytes,cgroup_swap_bytes,tree_rss_kib,tree_swap_kib,"
        "available_kib,system_swap_used_kib,system_swap_growth_kib,"
        "cgroup_kernel_peak_bytes,gpu_used_mib,gpu_free_mib,gpu_util_pct,gpu_temp_c\n"
        "1000,1073741824,0,524288,0,4194304,320,0,1073741824,5000,1000,90,60\n"
        "1001,1072693248,0,524288,0,4194304,368,48,1073741824,5000,1000,90,60\n"
        "1002,1072693248,0,524288,0,4194304,396,76,1073741824,5000,1000,90,60\n"
    )
    (run / "launch.json").write_text(
        json.dumps({"max_system_swap_growth_mib": 0, "gpu_free_min_mib": 512})
    )
    (run / "result.json").write_text(
        json.dumps({"reason": "system Swap grew by 0.0742188 MiB (allowed 0 MiB)"})
    )

    history = read_resource_history(run)

    assert history["available"]
    assert history["summary"]["samples"] == 3
    assert history["summary"]["system_swap_growth_peak_mib"] == pytest.approx(76 / 1024)
    event = next(event for event in history["events"] if event["metric"] == "system_swap_growth_mib")
    assert event["relative_s"] == 1
    assert event["value"] == pytest.approx(48 / 1024)
    assert event["confirmed_by_result"]
    assert "0 MiB" in history["summary"]["stop_reason"]


def test_demo_metadata_uses_real_eval_and_marks_media_local_only(tmp_path):
    run = tmp_path / "demo"
    run.mkdir()
    (run / "args.json").write_text(
        json.dumps(
            {
                "motion_dir": "data/lafan1_g1",
                "resume": None,
                "num_envs": 128,
            }
        )
    )
    (run / "eval.csv").write_text(
        "iteration,norm_return,norm_return_framew,n_failed,eval_at\n"
        "14000,0.597475,0.625824,18,2026-10-26 09:51:17\n"
    )
    (run / "g1_walk.mp4").write_bytes(b"local video")
    (run / "post").mkdir()
    (run / "post/result.json").write_text(
        json.dumps({"pipeline_completed": True, "target_reached": False})
    )

    demo = read_demo_metadata(
        run,
        "demo",
        "vibed",
        {"status": "completed", "iteration": 14000},
        {"iteration": 14000},
    )

    assert demo["track"] == "Track B"
    assert demo["checkpoint_iteration"] == 14000
    assert demo["metrics"]["normalized_return"] == "0.597475"
    assert demo["metrics"]["failed_clips"] == "18"
    assert demo["publication"]["status"] == "LOCAL_ONLY"
    assert any("CC BY-NC-ND" in right["status"] for right in demo["rights"])
    assert any("未达到目标质量" in item for item in demo["incomplete"])
