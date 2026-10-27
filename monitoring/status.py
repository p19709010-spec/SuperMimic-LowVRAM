"""Small lifecycle sidecar; all training scalars remain in TensorBoard."""
from __future__ import annotations

import json
import os
import time
import traceback
from pathlib import Path


def process_identity(pid):
    try:
        text = Path(f"/proc/{pid}/stat").read_text()
        fields = text[text.rfind(")") + 2:].split()
        return {"state": fields[0], "start_ticks": fields[19]}
    except (OSError, IndexError):
        return None


class RunStatus:
    def __init__(self, directory, phase, planned_hours=None, planned_iterations=None, start_iteration=0):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.started = time.time()
        identity = process_identity(os.getpid())
        self.data = dict(status="running", stage=phase, pid=os.getpid(),
                         process_start_ticks=identity["start_ticks"] if identity else None,
                         started_at=self.started, updated_at=self.started, iteration=start_iteration,
                         planned_hours=planned_hours, planned_iterations=planned_iterations,
                         start_iteration=start_iteration, error=None)
        self.update()

    def update(self, **values):
        self.data.update(values)
        self.data.update(updated_at=time.time(), elapsed_s=time.time() - self.started)
        path = self.directory / "status.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(self.data, indent=2, allow_nan=False))
        temporary.replace(path)

    def finish(self, error=None):
        self.update(status="completed" if error is None else "error", stage="finished",
                    error=None if error is None else "".join(traceback.format_exception(error)))


def instrument(trainer, status):
    """Wrap existing calls only to publish lifecycle metadata and the actor objective."""
    original_step = trainer.env.step
    def step(*args, **kwargs):
        status.update(stage="data_collection", iteration=trainer.iteration)
        return original_step(*args, **kwargs)
    trainer.env.step = step
    for component, stage in ((trainer.wm_trainer, "world_model"), (trainer.policy_trainer, "policy_bptt")):
        original = component.update
        def update(*args, _original=original, _stage=stage, **kwargs):
            status.update(stage=_stage, iteration=trainer.iteration)
            metrics = _original(*args, **kwargs)
            if _stage == "policy_bptt":
                metrics["actor_loss"] = -metrics["imag_objective"] / trainer.cfg.policy_trainer.horizon
            return metrics
        component.update = update
    original_save = trainer.save
    def save(name="ckpt_latest.pt"):
        original_save(name)
        checkpoint = trainer.log_dir / name
        if checkpoint.exists():
            status.update(iteration=trainer.iteration,
                          checkpoint={"name": name, "path": str(checkpoint.resolve()),
                                      "iteration": trainer.iteration, "saved_at": checkpoint.stat().st_mtime})
    trainer.save = save
