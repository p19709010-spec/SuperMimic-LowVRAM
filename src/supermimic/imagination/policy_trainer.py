"""Short-horizon actor–critic through the frozen world model (paper §3.3, Table A.5)."""

from __future__ import annotations

from dataclasses import dataclass

import torch

from supermimic.data.replay_buffer import ReplayBuffer
from supermimic.envs.mdp.motion_library import MotionLibrary
from supermimic.imagination.objective import gae_targets, policy_objective
from supermimic.imagination.rollout import ImagRollout, imagine
from supermimic.policy.nets import Critic, Policy
from supermimic.training.numerics import NumericalGuard, backward_step
from supermimic.world_model.world_model import WorldModel


@dataclass
class PolicyTrainerCfg:
    horizon: int = 32
    batch_size: int = 4096
    history: int = 10
    future_frames: int = 10
    gamma: float = 0.99
    gae_lambda: float = 0.95
    lr: float = 2e-4
    betas: tuple[float, float] = (0.9, 0.95)
    grad_clip_norm: float = 1.0
    grad_clip_value: float = 0.1
    critic_lr: float = 2e-4
    critic_grad_clip: float = 1.0
    critic_epochs: int = 5
    critic_minibatches: int = 4
    use_critic: bool = True
    obs_noise: bool = True
    compile: str | None = "default"
    anchor_obs: bool = False  # None | "default" | "reduce-overhead" | "max-autotune-no-cudagraphs"
    max_action_abs: float | None = None  # fail-stop limits, never clip or replace values
    max_velocity_abs: float | None = None
    max_target_abs: float | None = None
    max_critic_loss: float | None = None


class PolicyTrainer:
    def __init__(self, wm: WorldModel, policy: Policy, critic: Critic, lib: MotionLibrary, cfg: PolicyTrainerCfg):
        self.wm, self.policy, self.critic, self.lib, self.cfg = wm, policy, critic, lib, cfg
        self.opt = torch.optim.Adam(policy.parameters(), lr=cfg.lr, betas=cfg.betas)
        self.critic_opt = torch.optim.Adam(critic.parameters(), lr=cfg.critic_lr)
        self.guard = NumericalGuard()
        self.feedback_observer = None  # optional read-only diagnostics, no loss modification
        from supermimic.imagination.compiled import ImagStep

        self.step_fn = ImagStep(wm, lib.default_joint_pos, compile_mode=cfg.compile)

    def set_lr(self, lr: float) -> None:
        for g in self.opt.param_groups:
            g["lr"] = lr
        for g in self.critic_opt.param_groups:
            # Keep independently configured actor/critic rates under the same schedule.
            # Assigning lr directly silently changed critic lr in actor-only ablations.
            g["lr"] = lr * self.cfg.critic_lr / self.cfg.lr

    def _critic_inputs(self, ro: ImagRollout):
        H1, n, _ = ro.states.shape
        feat = self.wm.spec.canonical(ro.states.reshape(H1 * n, -1)).reshape(H1, n, -1)
        return feat, ro.goals, ro.e_root

    def update(self, buffer: ReplayBuffer, xi_norm_fn=None) -> dict[str, float]:
        cfg, guard = self.cfg, self.guard
        start = buffer.sample_starts(cfg.batch_size, cfg.history)
        guard.begin("policy_rollout", start=start)
        guard.finite("policy.start", start)
        xi_norm = self.wm.spec.normalize_xi(start.xi)
        self.wm.requires_grad_(False)
        self.critic.requires_grad_(False)
        try:
            ro = imagine(self.wm, self.policy, self.lib, start, cfg.horizon, cfg.future_frames,
                         obs_noise=cfg.obs_noise, step_fn=self.step_fn, anchor_obs=cfg.anchor_obs)
            guard.add(rollout=ro)
            guard.finite("policy.rollout", ro)
            guard.bound("imagination.action", ro.actions, cfg.max_action_abs)
            guard.bound("imagination.velocity", ro.states[..., 36:], cfg.max_velocity_abs)
            feat, goals, e_root = self._critic_inputs(ro)
            v_H = self.critic(feat[-1], goals[-1], xi_norm, e_root[-1]) if cfg.use_critic else None
            J = policy_objective(ro, v_H, cfg.gamma)
            loss = -J / cfg.horizon
            guard.add(actor_loss=loss)
            guard.finite("actor.loss", loss)

            # Compute exactly the original fixed targets, before *any* optimizer step.
            # The actor update never changes these stored states or critic weights.
            if cfg.use_critic:
                with torch.no_grad():
                    feat_d, goals_d, e_root_d = feat.detach(), goals.detach(), e_root.detach()
                    H1, n, _ = feat_d.shape
                    xi_rep = xi_norm[None].expand(H1, n, -1)
                    values = self.critic(feat_d.reshape(H1*n, -1), goals_d.reshape(H1*n, -1),
                        xi_rep.reshape(H1*n, -1), e_root_d.reshape(H1*n, -1)).reshape(H1, n)
                    targets = gae_targets(ro.rewards.detach(), ro.dhat[1:].detach(), values,
                                          cfg.gamma, cfg.gae_lambda)
                    guard.add(critic_values=values, targets=targets)
                    guard.bound("critic.targets", targets, cfg.max_target_abs)
                    preflight = torch.nn.functional.mse_loss(values[:-1], targets)
                    guard.add(critic_preflight_loss=preflight)
                    guard.bound("critic.preflight_loss", preflight, cfg.max_critic_loss)
                    X_feat = feat_d[:-1].reshape(-1, feat_d.shape[-1])
                    X_goal = goals_d[:-1].reshape(-1, goals_d.shape[-1])
                    X_xi = xi_rep[:-1].reshape(-1, xi_rep.shape[-1])
                    X_er = e_root_d[:-1].reshape(-1, 4)
                    Y = targets.reshape(-1)

            guard.add(phase="actor_backward")
            if self.feedback_observer is not None:
                self.feedback_observer("before", start, ro, None)
            gn = backward_step(self.policy, self.opt, loss, cfg.grad_clip_norm, guard,
                               "actor", clip_value=cfg.grad_clip_value)
            feedback_metrics = self.feedback_observer("after", start, ro, gn) if self.feedback_observer is not None else {}
            self.wm.requires_grad_(True)
            self.critic.requires_grad_(True)
            metrics = {
                "imag_objective": float(J.detach()), "actor_loss": float(loss.detach()),
                "imag_return_undisc": float((ro.survival[:-1]*ro.rewards).sum(0).mean().detach()),
                "imag_reward_mean": float(ro.rewards.mean().detach()),
                "imag_reward_min": float(ro.rewards.min().detach()),
                "imag_survival_H": float(ro.survival[-1].mean().detach()),
                "imag_dhat_mean": float(ro.dhat[1:].mean().detach()),
                "policy_grad_norm": float(gn),
                "action_abs_mean": float(ro.actions.abs().mean().detach()),
                "action_abs_max": float(ro.actions.abs().max().detach()),
                "velocity_abs_max": float(ro.states[...,36:].abs().max().detach()),
                "zero_survival_fraction": float((ro.survival[:-1] == 0).float().mean()),
            }
            for k, v in ro.reward_terms.items():
                metrics[f"imag_r/{k}"] = v
            metrics.update(feedback_metrics or {})

            if cfg.use_critic:
                N = Y.shape[0]
                mb = N // cfg.critic_minibatches
                if mb == 0:
                    guard.fail("critic minibatch is empty")
                last = torch.zeros((), device=Y.device)
                losses, grad_norms = [], []
                for epoch in range(cfg.critic_epochs):
                    perm = torch.randperm(N, device=Y.device)
                    for i in range(cfg.critic_minibatches):
                        idx = perm[i*mb:(i+1)*mb]
                        pred = self.critic(X_feat[idx], X_goal[idx], X_xi[idx], X_er[idx])
                        closs = torch.nn.functional.mse_loss(pred, Y[idx])
                        guard.add(phase="critic_backward", epoch=epoch, minibatch=i,
                                  minibatch_indices=idx, prediction=pred, critic_loss=closs)
                        guard.bound("critic.loss", closs, cfg.max_critic_loss)
                        cgn = backward_step(self.critic, self.critic_opt, closs,
                                            cfg.critic_grad_clip, guard, "critic")
                        last = closs.detach()
                        losses.append(last)
                        grad_norms.append(cgn)
                metrics.update(critic_loss=float(last),
                    critic_loss_max=float(torch.stack(losses).max()),
                    critic_grad_norm=float(torch.stack(grad_norms).max()),
                    critic_value_mean=float(values.mean()), critic_target_mean=float(targets.mean()),
                    critic_target_abs_max=float(targets.abs().max()),
                    lambda_advantage_abs_max=float((targets-values[:-1]).abs().max()))
            guard.finite("policy.metrics", metrics)
            return metrics
        finally:
            self.wm.requires_grad_(True)
            self.critic.requires_grad_(True)
            guard.context = {}
