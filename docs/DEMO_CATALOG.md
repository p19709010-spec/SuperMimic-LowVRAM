# Dashboard 与机器人 Demo 目录

本目录只记录本地真实产物和证据边界。所有机器人演示媒体、动作数据、机器人模型和
checkpoint 均为 **LOCAL_ONLY**，不进入 `release/public_files.txt`。

## Track A

| 资源 | 来源 | Checkpoint / iteration | 数据、模型与模式 | 真实指标 | 完成状态 |
|---|---|---|---|---|---|
| 本地 Dashboard 历史曲线 | `src/supermimic/`、TensorBoard | 由所选 run 决定；无记录时不推断 | Track A 独立 mjlab 实现；训练/诊断模式 | 仅展示日志原始指标 | Track A 长训未稳定完成 |
| `logs/local_20261025_sim16/reference_visual/motion.gif` | Track A 仿真参考回放 | 无 policy checkpoint | LAFAN1 本地动作；G1 mjlab/MuJoCo 仿真；参考动作回放 | 不是策略跟踪成绩 | 仅演示参考动作与仿真链路 |
| 当前 Track A policy 视频 | 无 | — | — | — | 未找到可用的完整 Track A policy 演示视频 |

Track A 的短 WM/BPTT run 有曲线和有限 checkpoint，但 Actor feedback 稳定性问题未解决；
不能把训练曲线当作论文级跟踪成绩。

## Track B

所有 Track B run 都使用未修改的
`zita-ch/supermimic_vibed@a1508d42c9d1699a52e8233ab16d08c488441ab9`，数据为 LAFAN1
40 条 G1 retarget，模型为上游 World Model / Policy / Critic。

| 媒体或证据 | Run / checkpoint | 配置与模式 | 真实性能 | 未完成部分 |
|---|---|---|---|---|
| `smoke510_walk_NOT_CONVERGED.mp4` | `vibed_local_20261026_smoke02`，iteration 510 | 16 env / WM 32 / Policy 32 / H32；fresh training + 原生评测/渲染 | normalized return 0.00164382；40/40 clips failed | 明确未收敛；只用于链路 smoke |
| `g1_walk.mp4`、`success_curve.png` | `vibed_local_20261026_fit128`，iteration 600 | 128 / 64 / 128 / H32；fresh training + 原生评测/渲染 | normalized return 0.00124821；40/40 failed | `target_reached=false`；只完成少量 Actor 更新 |
| `g1_walk.mp4`、`success_curve.png` | `vibed_local_20261026_lafan40_main01`，iteration 14000 | 128 / 64 / 128 / H32；fresh training + 40 动作评测 + walk 渲染 | normalized return 0.59747535；18/40 failed；frame-weighted 0.62582439 | `target_reached=false`，低于上游报告质量；不等于稳定论文复现 |
| `ckpt_000900_eval` 与 512 短测资源证据 | `vibed_local_20261027_vram512_01`，iteration 900 | 512 / 256 / 512 / H32；fresh short test | checkpoint 有限；更新计数 9000/400/8000；GPU 采样峰值 5412 MiB | 未生成本 run 的视频或 40 动作评测 |
| 768 资源证据 | `vibed_local_20261027_vram768_01`，训练到 iteration 570 | 768 / 384 / 768 / H32；fresh short test | CSV 有限；GPU 峰值 6780 MiB；整机 Swap +76 KiB 后停止 | 无最终 checkpoint/eval/video；不是完整配置 |

评测协议为原生 40 动作整 clip 回放，摩擦 1.0、无噪声/域随机化。上表分数是本地
`eval.csv` / `post/result.json` 的真实结果，不是上游报告数字。

## 资源公开授权

| 资产 | 当前授权判断 | PUBLIC 边界 |
|---|---|---|
| LAFAN1 G1 动作 CSV / NPZ / 动作库 | CC BY-NC-ND 4.0（Ubisoft La Forge） | 不公开、不再分发 |
| Unitree G1 机器人模型、网格与描述 | 上游 README 标注 BSD-3-Clause；仍需保留通知并核对具体资产 | 当前不进入 PUBLIC 清单 |
| Track B 本地 checkpoint、replay、日志、轨迹 | 项目/运行本地产物，依赖受限数据 | 不公开 |
| 本地生成的 `g1_walk.mp4`、曲线和 Dashboard 截图 | 由受限动作和机器人资产生成，公开再分发授权未确认 | LOCAL_ONLY |
| 上游 `supermimic_lafan1_highlight.gif` 与上游结果图 | 上游演示媒体，不能默认由本项目 MIT 重新授权 | 不公开 |
| `supermimic_vibed` 源码 | MIT，Copyright (c) 2026 ETH Zurich, Chong Zhang | 通过固定版本获取，不 vendored |

受限动作、机器人模型、视频、轨迹、日志和 checkpoint 均不得直接加入 GitHub PUBLIC
清单。Dashboard 只在本机展示这些证据的摘要，不把媒体嵌入公开包。
