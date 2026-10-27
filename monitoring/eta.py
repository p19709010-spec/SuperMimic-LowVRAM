"""Training-only ETA from a recent, phase-consistent window of native CSV samples."""
import math
import statistics
import time


def finite(value):
    return isinstance(value, (int,float)) and math.isfinite(value)


def estimate(samples, args, status, launch, summary=None, result=None, log_mtime=None, now=None):
    now = time.time() if now is None else now
    summary, result = summary or {}, result or {}
    target = args.get("iterations") or status.get("planned_iterations")
    started = summary.get("started_at", status.get("started_at"))
    ended = summary.get("finished_at")
    completed = summary.get("completed", False)
    # The training controller's elapsed record precedes evaluation/rendering.
    if not finite(ended) and finite(started) and finite(result.get("elapsed_s")):
        ended = started + result["elapsed_s"]
        completed = result.get("returncode")==0 and not result.get("reason")
    if not finite(ended) and status.get("stage")=="finished" and status.get("status") in ("completed","error"):
        ended = status.get("updated_at")
        completed = status["status"]=="completed"
    limit = summary.get("limit_seconds") or launch.get("max_seconds")
    if not finite(limit) and finite(status.get("planned_hours")):
        limit = status["planned_hours"]*3600
    elapsed = max(0., (ended if finite(ended) else now)-started) if finite(started) else None
    deadline = started+limit if finite(started) and finite(limit) else None

    # A restart/clock discontinuity starts a new contiguous measurement segment.
    contiguous = []
    for step,seconds in samples:
        if not finite(step) or not finite(seconds):
            continue
        if contiguous and (step<=contiguous[-1][0] or seconds<=contiguous[-1][1]):
            contiguous = []
        contiguous.append((step,seconds))
    current = contiguous[-1][0] if contiguous else status.get("iteration")
    window, rate, span, measured_seconds = [], None, 0, None
    if contiguous:
        warmup = args.get("wm_only_iters",500)
        floor = max(current-500, warmup if current>warmup else 0)
        window = [(i,t) for i,t in contiguous if i>=floor]
        if len(window)>1:
            span = window[-1][0]-window[0][0]
            measured_seconds = window[-1][1]-window[0][1]
            if span>=300 and measured_seconds>0:
                rate = span/measured_seconds
    state = "completed" if finite(ended) and completed else "stopped" if finite(ended) else status.get("status","unknown")
    answer = dict(current_iteration=current,target_iteration=target,
        iteration_percent=100*min(1,max(0,current/target)) if finite(current) and finite(target) and target>0 else None,
        training_elapsed_seconds=elapsed, time_limit_seconds=limit,
        time_budget_percent=100*min(1,elapsed/limit) if finite(elapsed) and finite(limit) and limit>0 else None,
        recent_iterations_per_second=rate,recent_iterations_per_minute=rate*60 if rate else None,
        window_iterations=span,window_seconds=measured_seconds,
        training_state=state,actual_finished_at=ended if finite(ended) else None,
        training_completed=completed,eta_seconds=None,estimated_finish_at=None,
        iteration_eta_seconds=None,budget_remaining_seconds=max(0,deadline-now) if deadline else None,
        budget_deadline_at=deadline,predicted_stop=None,note=None,postprocess_note="评测时间待估")
    if finite(ended):
        answer["predicted_stop"] = "iterations" if finite(current) and finite(target) and current>=target else "ended"
        answer["note"] = "实际训练结束时间；评测、视频生成单独计时"
        return answer
    if state != "running" or status.get("stage")=="evaluation":
        answer["note"] = "训练未运行，ETA 暂停"
        return answer
    if not rate:
        answer["note"] = "等待同一训练阶段至少 300 次迭代的速度记录"
        return answer
    if contiguous[-1][0]<=args.get("wm_only_iters",500) and finite(target) and target>args.get("wm_only_iters",500):
        answer["note"] = "当前为 WM 预热速度；BPTT 阶段速度待测"
        return answer
    interval = statistics.median(b[1]-a[1] for a,b in zip(window,window[1:]))
    age = max(0,now-log_mtime) if finite(log_mtime) else None
    if age is None or age>max(30,3*interval):
        answer["note"] = "训练日志暂未更新，ETA 暂停估算"
        return answer
    if finite(target) and finite(current):
        iteration_remaining = max(0,(target-current)/rate-age)
        answer["iteration_eta_seconds"] = iteration_remaining
        finish = now+iteration_remaining
        if deadline is not None and deadline<finish:
            answer.update(eta_seconds=max(0,deadline-now),estimated_finish_at=max(now,deadline),predicted_stop="time_limit")
        else:
            answer.update(eta_seconds=iteration_remaining,estimated_finish_at=finish,predicted_stop="iterations")
    answer["note"] = f"按最近 {span:g} 次迭代的实际耗时动态估算"
    return answer
