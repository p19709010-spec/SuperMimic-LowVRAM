"""Read-only action-history feedback diagnostics; no loss or policy-output changes."""
from __future__ import annotations

import json
import math
from collections import deque

import torch

from supermimic.world_model.heads import analytic_observation, flatten_history_term_major
from supermimic.training.numerics import detached
from supermimic.training.checkpoint import atomic_torch_save


def select_start(start, index):
    start = detached(start, cpu=True)
    return {key: value[:,index:index+1] if key.startswith("hist_") else value[index:index+1]
            for key,value in start.items()}


def observation(start, q0):
    history = [analytic_observation(start["hist_states"][i],start["hist_actions"][i],start["xi"],q0)
               for i in range(start["hist_states"].shape[0])]
    return history, flatten_history_term_major(torch.stack(history))


def local_radius(actor, obs, goal):
    # State = ten chronological action vectors; shift nine lags, append actor output.
    history_size = actor.cfg.history * 29
    with torch.enable_grad():
        def fn(h):
            return actor(torch.cat([obs[:,:-history_size],h.reshape(1,history_size)],-1),goal).squeeze(0)
        jac = torch.autograd.functional.jacobian(fn,obs[:,-history_size:].reshape(-1),vectorize=False)
    if not bool(torch.isfinite(jac).all()):
        return float("inf")
    matrix = torch.zeros(history_size,history_size,dtype=torch.float64)
    matrix[:-29,29:] = torch.eye(history_size-29,dtype=torch.float64)
    matrix[-29:] = jac.detach().to(device="cpu",dtype=torch.float64)
    return float(torch.linalg.eigvals(matrix).abs().max())


@torch.no_grad()
def measure(actor, wm, q0, start, goals):
    history,obs = observation(start,q0)
    radius = local_radius(actor,obs,goals[0])
    result = dict(frame=int(start["frame"][0]),radius=radius,
                  initial_velocity_absmax=float(start["state"][:,36:].abs().max()),
                  initial_action_history_absmax=float(start["hist_actions"].abs().max()))
    for mode in ("fixed_state","world_model"):
        hist = list(history)
        state = start["state"].clone()
        trace = []
        for t in range(len(goals)):
            action = actor(flatten_history_term_major(torch.stack(hist)),goals[t])
            if mode == "world_model":
                state = wm.step(state,action,start["xi"])
            hist = hist[1:]+[analytic_observation(state,action,start["xi"],q0)]
            trace.append(dict(t=t,action_absmax=float(action.abs().max()),
                              velocity_absmax=float(state[:,36:].abs().max())))
        result[mode] = trace
        result[mode+"_action_absmax"] = max(row["action_absmax"] for row in trace)
        result[mode+"_velocity_absmax"] = max(row["velocity_absmax"] for row in trace)
    return result


def json_safe(value):
    if isinstance(value,float) and not math.isfinite(value): return str(value)
    if isinstance(value,dict): return {k:json_safe(v) for k,v in value.items()}
    if isinstance(value,list): return [json_safe(v) for v in value]
    return value


class FeedbackObserver:
    """Input Jacobians on resident models; autograd.grad never accumulates parameter grads."""
    def __init__(self,tr,fixed_starts,save_every=0,stop_on_feedback=True):
        self.tr = tr
        self.q0 = tr.lib.default_joint_pos.detach()
        self.actor = tr.policy
        self.wm = tr.wm
        self.fixed_starts = fixed_starts
        self.save_every = save_every
        self.stop_on_feedback = stop_on_feedback
        self.update = 0
        self.first_radius_crossing = None
        self.first_large_feedback = None
        self.before_params = None
        self.rows = deque(maxlen=80)
        self.stream = (tr.log_dir/"feedback_updates.jsonl").open("x",buffering=1)
        (tr.log_dir/"actor_updates").mkdir()

    def goals(self,start):
        frame = start["frame"].to(self.tr.lib.device)
        last = self.tr.lib.last_frame_of(frame)
        return [self.tr.lib.goal_window(torch.minimum(frame+t,last),self.tr.cfg.env.future_frames).detach()
                for t in range(self.tr.cfg.policy_trainer.horizon)]

    def __call__(self,phase,start,rollout,grad_norm):
        if phase == "before":
            self.update += 1
            self.active_starts = list(self.fixed_starts)
            index = int(start.state[:,42:].abs().amax(-1).argmax())
            self.active_starts.append(select_start(start,index))
            self.active_starts = [{k:v.to(self.tr.device) for k,v in s.items()} for s in self.active_starts]
            self.active_goals = [self.goals(s) for s in self.active_starts]
        measured = [measure(self.actor,self.wm,self.q0,s,g) for s,g in zip(self.active_starts,self.active_goals)]
        row = dict(update=self.update,iteration=self.tr.iteration,phase=phase,
                   actor_lr=self.tr.policy_trainer.opt.param_groups[0]["lr"],
                   critic_lr=self.tr.policy_trainer.critic_opt.param_groups[0]["lr"],
                   samples=measured,max_radius=max(m["radius"] for m in measured),
                   fixed_action_absmax=max(m["fixed_state_action_absmax"] for m in measured),
                   closed_action_absmax=max(m["world_model_action_absmax"] for m in measured),
                   closed_velocity_absmax=max(m["world_model_velocity_absmax"] for m in measured))
        if phase == "before":
            self.before_params = {k:v.detach().clone() for k,v in self.actor.named_parameters()}
            self.before_row = row
        else:
            deltas = {k:float((v.detach().double()-self.before_params[k].double()).square().sum())**.5
                      for k,v in self.actor.named_parameters()}
            row["parameter_step_l2"] = sum(v*v for v in deltas.values())**.5
            row["top_layer_steps"] = dict(sorted(deltas.items(),key=lambda p:p[1],reverse=True)[:5])
            first = "decoder.mlp.net.0.weight"
            row["action_input_weight_step_l2"] = float((self.actor.state_dict()[first][:,-290:].double()-self.before_params[first][:,-290:].double()).square().sum())**.5
            row["actor_grad_norm"] = float(grad_norm)
            state = self.tr.policy_trainer.opt.state
            row["adam_step"] = int(next(iter(state.values()))["step"])
            row["adam_exp_avg_absmax"] = max(float(s["exp_avg"].abs().max()) for s in state.values())
            if self.first_radius_crossing is None and any(a["radius"]<=1<b["radius"] for a,b in zip(self.before_row["samples"],measured)):
                self.first_radius_crossing = dict(update=self.update,iteration=self.tr.iteration)
            if self.first_large_feedback is None and max(row["fixed_action_absmax"],row["closed_action_absmax"]) > 20:
                self.first_large_feedback = dict(update=self.update,iteration=self.tr.iteration)
            if self.save_every and (self.update%self.save_every==0 or self.first_radius_crossing==dict(update=self.update,iteration=self.tr.iteration)):
                path=self.tr.log_dir/"actor_updates"/f"actor_{self.update:05d}.pt"
                # Serialize GPU storages one at a time, avoiding a full CPU optimizer replica.
                atomic_torch_save(dict(policy=self.actor.state_dict(),optimizer=self.tr.policy_trainer.opt.state_dict(),
                    before_policy=self.before_params,wm=self.wm.state_dict(),critic=self.tr.critic.state_dict(),
                    start=detached(start,cpu=True),rollout=detached(rollout,cpu=True),
                    diagnostic=json_safe(row)),path)
        self.stream.write(json.dumps(json_safe(row),allow_nan=False)+"\n")
        self.rows.append(row)
        if phase == "after":
            summary = dict(updates=self.update,first_radius_crossing=self.first_radius_crossing,
                           first_large_feedback=self.first_large_feedback,last=json_safe(row))
            temporary=self.tr.log_dir/"feedback_summary.tmp"
            temporary.write_text(json.dumps(summary,indent=2,allow_nan=False))
            temporary.replace(self.tr.log_dir/"feedback_summary.json")
        bad = not all(math.isfinite(row[k]) for k in ("max_radius","fixed_action_absmax","closed_action_absmax","closed_velocity_absmax"))
        bad = bad or max(row["fixed_action_absmax"],row["closed_action_absmax"])>20
        bad = bad or row["closed_velocity_absmax"]>200
        if bad and self.stop_on_feedback:
            self.tr.guard.add(feedback=row,actor_before_state=self.before_params)
            self.tr.guard.fail(f"feedback probe unstable {phase} actor step {self.update}")
        if phase == "after":
            return dict(feedback_radius_before=self.before_row["max_radius"],feedback_radius_after=row["max_radius"],
                        feedback_fixed_action_max=row["fixed_action_absmax"],feedback_closed_action_max=row["closed_action_absmax"],
                        actor_parameter_step_l2=row["parameter_step_l2"])

    def close(self):
        self.stream.close()
