# P1 本地工程整理验收

日期：2026-10-27

范围：仅 P1；不进入 P2/P3。

## 边界与安全约束

- 未启动正式训练或高资源压力测试。
- 未修改 Actor、Critic、World Model 的核心算法、损失定义或安全阈值。
- 未执行 `git reset --hard`、`git clean -fdx`、`git add .`、提交、推送或 Release。
- 未复制、移动或删除 `external/`、数据、checkpoint、日志或模型资产。
- P1 开始前已有的未提交修改保持原样，仍由用户决定后续提交范围。

## 工作区保护

修改前备份位于被 Git 忽略的 `.local_backups/p1_20261027T100621/`。备份包含：

- 已跟踪文件的完整差异补丁与状态快照。
- 未跟踪源代码和文档归档。
- 上游 `supermimic_vibed` 和 Isaac Lab 的 HEAD、remote 与状态快照。
- `SHA256SUMS` 校验清单。

使用 `sha256sum -c SHA256SUMS` 校验通过。备份不包含 `external/`、数据、日志、虚拟环境或缓存，且不得公开发布。

## 工程整理内容

1. `.gitignore` 隔离 `external/`、数据、日志、checkpoint、模型文件、虚拟环境、本地备份、凭据和生成产物；确认没有已跟踪文件落在此忽略范围内。
2. 主 mjlab 实现继续位于 `src/supermimic/`，不合并第三方训练实现。
3. 低显存兼容层位于 `experiments/low_vram_vibed/`，只包含配置、来源校验、资源保护、checkpoint 检查和后处理适配。
4. 上游固定为 `zita-ch/supermimic_vibed@a1508d42c9d1699a52e8233ab16d08c488441ab9`；checkout 留在被忽略的 `external/supermimic_vibed/`，不 vendoring。
5. 保留 MIT 版权与许可文本，来源和依赖边界记录在 `THIRD_PARTY_NOTICES.md`。
6. README、`docs/REPRODUCTION_STATUS.md` 和实验文档分别标明 RTX 5090 历史记录、RTX 5060 Ti 当前证据与未验证功能。

## 验证记录

以下命令均为 CPU/无 GPU 运行，不以训练成功作为通过条件。

```bash
env -u PYTHONPATH CUDA_VISIBLE_DEVICES='' \
  MPLCONFIGDIR=/tmp/supermimic-mpl UV_CACHE_DIR=/tmp/supermimic-uv \
  uv run --no-sync pytest -q -rs
```

结果：`38 passed, 15 skipped, 1 warning in 6.33s`。跳过项需要 CUDA 或 LAFAN1 数据；本机没有执行这些高资源测试。

```bash
env -u PYTHONPATH CUDA_VISIBLE_DEVICES='' \
  MPLCONFIGDIR=/tmp/supermimic-mpl UV_CACHE_DIR=/tmp/supermimic-uv \
  uv run --no-sync python experiments/low_vram_vibed/smoke.py --require-upstream
```

结果：

- 5 个 profile 全部通过配置校验。
- 上游路径、remote 和 commit 正确，工作树无源码修改。
- CPU policy 输出形状为 `[2, 29]`，全部有限。
- `experiments/` 下未发现模型、数据或 checkpoint 资产。

其他检查：

- 低显存模块、兼容入口和仓库卫生测试的 Ruff 检查通过。
- `fetch_upstream.py --dry-run` 通过；已存在的固定上游 checkout 被识别为 clean。
- `git diff --check` 通过。
- `git ls-files -ci --exclude-standard` 为空。
- 已跟踪文件中没有 `.npz/.npy/.pt/.pth/.ckpt/.onnx/.safetensors` 文件。
- 公开文档扫描未发现用户名、本地 home 路径、访问令牌或私钥内容。

## 当前目录边界

```text
src/supermimic/                独立 mjlab 复现（主实现）
experiments/low_vram_vibed/    低显存兼容层（独立实验模块）
  configs/                     verified / experimental / untested profile
  tests/                       profile、来源和兼容入口测试
monitoring/                    本地资源与 Dashboard 工具
scripts/                       项目脚本；vibed_* 为薄兼容入口
tests/                         CPU 回归与仓库卫生测试
docs/                          规范、状态、审计与验证记录
external/                      第三方 checkout，本地忽略，不发布
data/ logs/ checkpoints/       本地资产，忽略，不发布
.local_backups/                P1 恢复备份，本地忽略，不发布
```

## 可公开范围

经人工复核后可公开：项目自有源代码、测试、配置模板、文档和来源说明。低显存层必须以“独立兼容层、非官方、实验性”描述，且不得暗示已稳定训练。

禁止公开：LAFAN1 CSV/NPZ/动作库、BONES-SEED 资产、checkpoint、replay buffer、日志、故障诊断原始产物、视频、虚拟环境、第三方 checkout、本地备份及任何凭据。

## 尚未解决

1. 独立 mjlab 实现的 Actor 反馈失稳仍未解决。
2. 没有当前可复核的稳定长训练或完整论文端到端复现。
3. 512 正式低显存 profile 未通过零 Swap 启动门槛；768 中途停止；1024 未运行。
4. RTX 5090 历史日志/checkpoint 和 BONES-SEED 数据不在当前工作区。
5. 当前工作区混合了 P1 前已有修改、未跟踪诊断代码和 P1 整理结果，提交前必须逐文件审查。
6. `monitoring/` 等较早代码仍存在未处理的历史 lint 问题；P1 未扩大范围修改无关代码。
7. 依赖许可证（尤其 `torchrunx` 的 GPL-3.0 元数据）、Unitree 资产和数据集条款仍需发布前审计。

## P2 前风险与建议

- 先由人工审查并拆分当前 dirty worktree，再决定提交批次；不要使用 `git add .`。
- 不要因为 CPU 测试通过就宣称训练或算法稳定性已验证；GPU/数据相关 15 项测试仍未执行。
- 低显存正式运行前应先解决 Swap 门槛的非确定性，并保留独立、可审计的 run 证据。
- 在文档建设前冻结历史结果与当前结果的表述边界，避免把 5090 数字或短测结果写成正式复现。
- 发布流程应增加自动隐私、许可证、大文件和受限数据扫描，并把 `external/` 排除在源码包之外。
