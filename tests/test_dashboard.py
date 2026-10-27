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
