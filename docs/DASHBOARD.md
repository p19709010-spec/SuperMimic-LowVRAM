# 本地实时训练 Dashboard

当前 `supermimic_vibed` 面板已作为独立服务运行。其启动参数和原生 CSV 指标可直接从本节命令确认；训练 ETA 与双停止条件的详细本地实验记录仍在 REVIEW 边界内，未纳入首批公开候选。以下默认启动命令和包装入口用于旧项目日志；查看新项目应添加 `--log-root external/supermimic_vibed/logs`，已有 7860 服务运行时不要重复启动。

在项目根目录启动独立监控进程：

```bash
env -u PYTHONPATH UV_CACHE_DIR=/tmp/supermimic-uv \
  XDG_CACHE_HOME=/tmp/supermimic-cache MPLCONFIGDIR=/tmp/supermimic-mpl \
  uv run --no-sync python -m monitoring.server --port 7860
```

浏览器打开 **http://127.0.0.1:7860**。服务器固定绑定 IPv4 loopback，没有公网监听参数。无需安装新依赖。停止面板不会停止训练；面板不导入 torch、不加载 checkpoint、不创建 CUDA 上下文。

## 使用

- 顶部选择当前或历史 run，可选择另一 run 叠加同名曲线并比较配置。
- 训练曲线上方显示 `resources.csv` 的三组真实历史：GPU 显存、RAM（cgroup / 进程树 /
  主机可用）和 Swap（cgroup / 进程树 / 整机）。对比 run 以虚线叠加，资源摘要表同时列出
  峰值和停止原因。
- 红色横坐标标记来自 `launch.json` 阈值与逐样本数值的首次越界；表格保留实测值、阈值和
  Run。整机 Swap 与训练 cgroup Swap 分开呈现，默认不把主机活动归因于训练。
- 页面每 5 秒刷新，GPU 每 3 秒采样。鼠标移入曲线可查看真实样本的步数和数值；没有指标则显示等待，不生成示例数据。
- 原训练日志位于 `logs/<run>/tb`。Dashboard 直接使用 TensorBoard EventAccumulator；可另外启动原生 TensorBoard 深入分析同一目录。
- 每条曲线标明实际 tag。独立验证误差优先显示；没有时显示原 `online_nse`，其来自 replay 采样，不称为独立验证。
- Simulation vs Imagination：仿真回合归一化回报与想象平均每步奖励 `/0.1` 对比。两者采样分布不同；不能直接当作模型误差。
- 若存在 `max-hours`，进度条明确显示“时间预算进度”；同时存在迭代上限时可能提前完成，因此完成时预算条可以不到 100%。“预算剩余”是时间上限余额，不是收敛时间预测。
- 没有时间预算时，已知迭代上限才显示迭代百分比；旧 run 无生命周期信息时，仅显示最后日志步数和“状态未记录”，不推测正在运行。
- GPU 卡片读取 `nvidia-smi` 的当前全卡显存、空闲显存、利用率和温度，反映所有本机 GPU 使用者，不等于选中历史 run 的训练资源。
- checkpoint 只读取文件名、mtime 和训练侧写出的迭代元数据；旧 `ckpt_latest.pt` 无迭代记录时显示“未记录”，不把当前训练步数冒充保存步数。
- Demo 面板从 `args.json`、`eval.csv`、`post/result.json` 和实际文件名生成，显示 Track
  A/B、真实 checkpoint iteration、数据/模型/模式、40 动作指标、未完成项和公开授权。
  详细边界见 [DEMO_CATALOG.md](DEMO_CATALOG.md)；面板不复制或嵌入受限媒体。

## 让新训练显示精确状态与阶段

原来的 `sm-train` 仍可直接使用。若需要精确阶段、结束/异常和 checkpoint 迭代信息，改用独立包装入口，参数与原 `sm-train` 相同：

```bash
env -u PYTHONPATH UV_CACHE_DIR=/tmp/supermimic-uv \
  XDG_CACHE_HOME=/tmp/supermimic-cache MPLCONFIGDIR=/tmp/supermimic-mpl \
  OMP_NUM_THREADS=1 uv run --no-sync python scripts/monitored_train.py --help
```

包装器调用原 `Trainer.run()`；只在原 env.step、WM.update、Policy.update、save 周围写入 `logs/<run>/status.json`，不改变 forward、backward、optimizer 或损失。Actor Loss 从原返回值按原式 `−imag_objective/H` 记录。所有学习曲线继续保存在原 TensorBoard 中，不另建训练日志格式。

本地验证入口 `scripts/local_smoke.py` 已接入相同状态记录。WM 独立验证按仿真环境划分：前 75% 供训练，后 25% 固定窗口供验证。

进程暂停（Linux T/t 状态）显示“暂停”；异常退出、Ctrl-C 或进程消失保留最后步数。能捕获的异常保留 traceback；SIGKILL 等无法执行清理的退出显示“未写入正常结束记录”，不伪造具体原因。

## 文件与验收

- `monitoring/server.py`：只读 HTTP API、TensorBoard 缓存及 GPU 采样。
- `monitoring/index.html`：无外部 CDN 的响应式界面与 SVG 曲线。
- `monitoring/resource_history.py`：只读解析资源 CSV，识别真实阈值越界点。
- `monitoring/demo.py`：从 run 元数据汇总 Demo 来源、指标和授权边界。
- `monitoring/status.py`：训练生命周期与 checkpoint 元信息。
- `scripts/monitored_train.py`：独立训练包装入口。
- `tests/test_dashboard.py`：真实 TensorBoard event 读入、空日志、进程消失和目录访问边界。
- 真实 WM run：`logs/local_20261025_wm_dashboard/`，含 60 个 loss 点及 6 组独立验证误差。
- 真实 BPTT run：`logs/local_20261025_policy_h8/`，含原训练回报、WM loss、actor/critic loss 和梯度曲线。
- 桌面验收截图：`logs/local_20261025_data/dashboard_desktop.png`，截图时真实训练处于 Policy BPTT 第 127 步。

单独运行与原训练不同的进程；没有 Web 写入、终止训练或删除实验的接口。
