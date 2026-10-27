"""Fail before unsafe optimizer steps; preserve the failing input instead of skipping it."""
from __future__ import annotations

import dataclasses
import json
import math
import random
import time
from pathlib import Path

import numpy as np
import torch
from supermimic.training.checkpoint import atomic_torch_save

from supermimic.training.distributed import allreduce_grads


class NumericalFailure(RuntimeError):
    pass


def detached(value, cpu=False):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu() if cpu else value.detach()
    if dataclasses.is_dataclass(value):
        return {f.name: detached(getattr(value, f.name), cpu) for f in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {k: detached(v, cpu) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [detached(v, cpu) for v in value]
    return value


class NumericalGuard:
    def __init__(self, directory: Path | None = None):
        self.directory = directory
        self.context = {}
        self.networks = {}
        self.optimizers = {}
        self._dumping = False

    def begin(self, phase, **context):
        self.context = dict(phase=phase, **detached(context))

    def add(self, **context):
        self.context.update(detached(context))

    def fail(self, reason):
        artifact = None
        if self.directory is not None and not self._dumping:
            self._dumping = True
            self.directory.mkdir(parents=True, exist_ok=True)
            artifact = self.directory / f"failure_{time.time_ns()}.pt"
            payload = dict(reason=reason, context=detached(self.context, cpu=True),
                networks={k: v.state_dict() for k, v in self.networks.items()},
                optimizers={k: v.state_dict() for k, v in self.optimizers.items()},
                rng=dict(torch=torch.get_rng_state(), cuda=torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
                         numpy=np.random.get_state(), python=random.getstate()))
            try:
                atomic_torch_save(payload, artifact)
                artifact.with_suffix(".json").write_text(json.dumps(dict(reason=reason, phase=self.context.get("phase"), artifact=str(artifact)), indent=2))
            finally:
                self._dumping = False
        raise NumericalFailure(f"{reason}; diagnostic={artifact}")

    def finite(self, name, value):
        if isinstance(value, torch.Tensor):
            if not bool(torch.isfinite(value).all()):
                self.fail(f"nonfinite {name}")
        elif isinstance(value, (float, int)):
            if not math.isfinite(value):
                self.fail(f"nonfinite {name}")
        elif dataclasses.is_dataclass(value):
            for field in dataclasses.fields(value):
                self.finite(f"{name}.{field.name}", getattr(value, field.name))
        elif isinstance(value, dict):
            for key, item in value.items():
                self.finite(f"{name}.{key}", item)
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                self.finite(f"{name}.{index}", item)

    def optimizer(self, name, module, optimizer):
        self.finite(f"{name}.parameters", module.state_dict())
        self.finite(f"{name}.optimizer_groups", optimizer.param_groups)
        for index, state in enumerate(optimizer.state.values()):
            self.finite(f"{name}.optimizer.{index}", state)
            for field in ("exp_avg_sq", "max_exp_avg_sq"):
                if field in state and bool((state[field] < 0).any()):
                    self.fail(f"negative {name}.{field}")

    def bound(self, name, value, maximum):
        self.finite(name, value)
        if maximum is not None and float(value.detach().abs().max()) > maximum:
            self.fail(f"{name} exceeds configured stop limit {maximum}")


def backward_step(module, optimizer, loss, clip_norm, guard, name, clip_value=None):
    """Original backward/clipping/Adam order with mandatory pre-step validation."""
    guard.finite(f"{name}.loss", loss)
    guard.optimizer(name, module, optimizer)
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    allreduce_grads(module)
    gradients = {n: p.grad for n, p in module.named_parameters() if p.grad is not None}
    guard.add(gradients=gradients)
    guard.finite(f"{name}.gradients", gradients)
    try:
        norm = torch.nn.utils.clip_grad_norm_(module.parameters(), clip_norm, error_if_nonfinite=True)
    except RuntimeError as error:
        guard.add(gradients=gradients)
        guard.fail(f"{name}.gradient_norm: {error}")
    if clip_value is not None:
        torch.nn.utils.clip_grad_value_(module.parameters(), clip_value)
    guard.finite(f"{name}.clipped_gradients", gradients)
    optimizer.step()
    guard.optimizer(f"{name}.after_step", module, optimizer)
    return norm.detach()
