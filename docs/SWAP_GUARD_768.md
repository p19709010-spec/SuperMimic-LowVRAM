# 768 配置 Swap Guard 诊断

诊断日期：2026-10-28（Europe/Berlin）
证据：`external/supermimic_vibed/logs/vibed_local_20261027_vram768_01/` 中的
`resources.csv`、`resources_latest.json`、`launch.json`、`status.json`、
`result.json` 和 `train_log.csv`。
范围：只读分析；未启动训练、未运行 GPU 压测、未修改原 checkpoint 或资源阈值。

## 结论

76 KiB 增长的真实可观测来源是 `/proc/meminfo` 暴露的整机
`SwapTotal - SwapFree` 增量，不是训练 cgroup 的 Swap。165 个真实采样中：

- 整机 Swap 已用量从 **320 KiB** 上升到 **396 KiB**，相对监控起点增长
  **76 KiB = 0.07421875 MiB**。
- 首次越界发生在样本 164：已用量变为 368 KiB，增长 **48 KiB**；下一采样增至
  396 KiB，随后保持 76 KiB。
- 训练 cgroup `memory.swap.current` 全程为 **0**。
- 训练进程树 `VmSwap` 全程为 **0 KiB**。
- 因此这次触发属于“整机 Swap 增长”，不能据此证明训练进程发生换出。

现有数据没有保存逐 PID 的 `VmSwap` 快照，无法事后点名具体进程。最准确的结论是：
增长发生在训练 cgroup 之外；具体来源不可归因，可能是主机上的其他进程、内核/页面回收
活动或采样期间的背景负载。不能把“无法点名”写成“已证明是误触发”，也不能把整机增量
直接归因于 768 训练。

## 原始数值

| 项目 | 结果 |
|---|---:|
| 采样数 | 165 |
| 采样时长 | 167.29 s |
| 采样间隔 | 1.0 s |
| 首次采样整机 Swap 已用 | 320 KiB |
| 首次越界整机 Swap 已用 / 增长 | 368 KiB / 48 KiB |
| 峰值整机 Swap 已用 / 增长 | 396 KiB / 76 KiB |
| 训练 cgroup Swap 峰值 | 0 MiB |
| 进程树 Swap 峰值 | 0 MiB |
| cgroup RAM 峰值 | 2.980 GiB |
| cgroup 内核 `memory.peak` | 2.994 GiB |
| 进程树 RSS 峰值 | 3.340 GiB |
| 主机可用 RAM 最小值 | 4.515 GiB |
| GPU 采样峰值 | 6780 MiB |
| 停止时 iteration | 570 |

Linux 页面大小为 4096 B，因此 76 KiB 是 19 个页面，首次增长的 48 KiB 是 12 个页面。
页面数量本身不能说明页面属于哪个进程。

## 是否使用了整机指标

是。`monitoring/resources.py` 同时采集三种范围：

1. 训练 cgroup：`memory.current`、`memory.swap.current`、`memory.peak`。
2. 训练进程树：各 PID 的 `VmRSS`、`VmSwap` 求和。
3. 整机：`/proc/meminfo` 的 `SwapTotal - SwapFree`，再减去本次监控首个样本。

768 的 `max_system_swap_growth_mib=0` 明确作用于第 3 项。cgroup 与进程树 Swap 是独立
证据，不应把三者合并成“训练 Swap”。

## 其他进程与误触发判断

首次越界的相邻采样还出现：

- 训练 cgroup RAM 从 3,153,727,488 B 降到 3,000,401,920 B，减少约 **146 MiB**。
- 进程树 RSS 从 3,502,020 KiB 降到 3,428,264 KiB，减少约 **72 MiB**。
- 主机可用 RAM 从 5,064,020 KiB 降到 4,810,164 KiB，减少约 **248 MiB**。

训练 cgroup 内存明显下降、主机可用内存同时下降时发生整机 Swap 增长，这不支持
“训练 cgroup 因接近 4 GiB 上限而换出”的解释，更强地指向训练 cgroup 之外的主机活动。
但 1 秒采样没有 PID 归因，不能进一步确认是哪个进程。

这次事件按当前规则是**正确触发**，是否属于“误触发”取决于后续政策规定“整机任何增长”
是否仍应立即停止。当前严格约束下，保护逻辑没有错误；需要改进的是可归因性和抑制策略，
而不是把本次结果改判为通过。

## 当前阈值与持续时间

768 profile 和实际 `launch.json`：

- 采样间隔：1.0 s。
- 整机 Swap 相对监控起点允许增长：0 MiB。
- cgroup 硬 MemoryMax：4 GiB。
- cgroup 内核 RAM 软停止阈值：3.75 GiB。
- 训练 cgroup Swap 阈值：256 MiB（同时 `memory.swap.max=0`）。
- 主机可用 RAM 阈值：2 GiB。
- GPU 空闲显存阈值：512 MiB。

整机 Swap 条件是**即时阈值**：第一次采样严格大于 0 即设置 issue，没有持续时间、连续
样本数或回归区间要求。监控每秒采样，外层训练包装器约每 3 秒检查 issue，并在发现后
终止训练进程组。连续三次遥测失败才报告 telemetry failure，这不是 Swap 抑制窗口。

## 建议的修改方案（本轮未实施）

保持现有阈值和停止行为，提交单独变更后再决定是否采用：

1. **增加归因字段**：同时记录 `pswpin/pswpout` 增量、cgroup Swap 增量、进程树 Swap
   增量，并仅在整机增长出现时抓取一次 `/proc/*/status` 的 `VmSwap` 和
   `/proc/*/cgroup`，保存变化最大的前 N 个 PID/cgroup。不要高频扫描整机进程。
2. **拆分事件类型**：保留 `host_swap_delta` 硬安全信号，同时增加
   `training_cgroup_swap_delta`；Dashboard 明确显示两者，避免把整机增长写成训练换出。
3. **可选抑制窗口**：把“首次整机增长”先记为 warning，只有在连续采样仍增长或超过单独
   确认的容差时才停止。该方案会改变当前零容忍策略，必须先由用户明确批准；本轮未启用。
4. **稳定基线**：在训练前增加数秒只读基线采样，使用中位数/回归后的稳定起点，同时保留
   绝对起始值，避免单次瞬时变化决定整个 run。
5. **验证方式**：新策略先 shadow mode 运行，记录若按旧/新规则分别会在何时停止；
   不自动重跑 768，不放宽正式训练门槛。

最低建议是先实施方案 1 和 2；它们改善证据质量，不改变阈值。方案 3 涉及策略变化，不能
作为本轮修复顺手开启。
