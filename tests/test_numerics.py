"""Finite checks must reject the optimizer step, not repair/skip its input."""
import copy

import pytest
import torch

from supermimic.data.replay_buffer import ReplayBuffer
from supermimic.training.numerics import NumericalFailure, NumericalGuard, backward_step


def test_nonfinite_loss_does_not_call_optimizer(tmp_path):
    model = torch.nn.Linear(2, 1)
    opt = torch.optim.Adam(model.parameters())
    before = copy.deepcopy(model.state_dict())
    guard = NumericalGuard(tmp_path)
    guard.networks = {"test": model}
    guard.optimizers = {"test": opt}
    guard.begin("test", input=torch.ones(1, 2))
    with pytest.raises(NumericalFailure):
        backward_step(model, opt, model(torch.ones(1, 2)).sum()*float("nan"), 1., guard, "test")
    assert not opt.state
    assert all(torch.equal(v, before[k]) for k, v in model.state_dict().items())
    assert len(list(tmp_path.glob("failure_*.pt"))) == 1


def test_nonfinite_gradient_rejects_finite_loss():
    model = torch.nn.Linear(2, 1)
    opt = torch.optim.Adam(model.parameters())
    before = copy.deepcopy(model.state_dict())
    handle = model.weight.register_hook(lambda grad: grad*float("nan"))
    with pytest.raises(NumericalFailure):
        backward_step(model, opt, model(torch.ones(1, 2)).sum(), 1., NumericalGuard(), "test")
    handle.remove()
    assert not opt.state
    assert all(torch.equal(v, before[k]) for k, v in model.state_dict().items())


def test_replay_termination_label_belongs_to_source_transition():
    buffer = ReplayBuffer(1, 8, 71, 29, 33, "cpu")
    buffer.valid[0, :4] = True
    buffer.ep_id[0, :4] = 0
    buffer.terminal[0, 3] = True
    buffer.done[0, 2:4] = 1  # source transition 2 -> terminal state 3
    buffer.ptr[0] = 4
    window = buffer.sample_windows(1, 3)
    assert window.done[:, 0].tolist() == [0., 0., 1.]


def test_actor_only_lr_change_keeps_critic_schedule_independent():
    from supermimic.imagination.policy_trainer import PolicyTrainer, PolicyTrainerCfg
    trainer = PolicyTrainer.__new__(PolicyTrainer)
    trainer.cfg = PolicyTrainerCfg(lr=2e-5,critic_lr=2e-4)
    trainer.opt = torch.optim.Adam(torch.nn.Linear(1,1).parameters(),lr=2e-4)
    trainer.critic_opt = torch.optim.Adam(torch.nn.Linear(1,1).parameters(),lr=2e-4)
    trainer.set_lr(1e-5)
    assert trainer.opt.param_groups[0]["lr"] == pytest.approx(1e-5)
    assert trainer.critic_opt.param_groups[0]["lr"] == pytest.approx(1e-4)
    trainer.cfg = PolicyTrainerCfg(lr=2e-4,critic_lr=2e-4)
    trainer.set_lr(1e-4)
    assert trainer.critic_opt.param_groups[0]["lr"] == pytest.approx(1e-4)


def test_feedback_diagnostic_preserves_parameters_gradients_and_rng():
    from supermimic.policy.nets import Policy,PolicyCfg
    from supermimic.imagination.feedback import local_radius
    model=Policy(PolicyCfg(encoder_hidden=(16,),decoder_hidden=(16,)))
    obs=torch.randn(1,930)
    goal=torch.randn(1,680)
    for parameter in model.parameters():parameter.grad=torch.randn_like(parameter)
    weights=copy.deepcopy(model.state_dict())
    gradients=[p.grad.clone() for p in model.parameters()]
    rng=torch.get_rng_state().clone()
    radius=local_radius(model,obs,goal)
    assert radius>=0 and torch.isfinite(torch.tensor(radius))
    assert all(torch.equal(value,weights[key]) for key,value in model.state_dict().items())
    assert all(torch.equal(p.grad,g) for p,g in zip(model.parameters(),gradients))
    assert torch.equal(torch.get_rng_state(),rng)


def test_cache_limited_checkpoint_roundtrip(tmp_path):
    from supermimic.training.checkpoint import atomic_torch_save
    data={"tensor":torch.arange(400000,dtype=torch.float32),"iteration":123}
    path=tmp_path/"verified.pt"
    atomic_torch_save(data,path)
    loaded=torch.load(path,weights_only=True,mmap=True)
    assert loaded["iteration"]==123
    assert torch.equal(loaded["tensor"],data["tensor"])
    assert not list(tmp_path.glob("*.tmp"))
