# P3-A 发布候选封装与验收

> **Superseded provenance note (P3-A.1, 2026-10-27):** This report is retained as a
> historical candidate audit. It predates the disclosure that CuboiLeo/SuperMimic-Reproduced
> is the upstream project. Its NO decision remains valid historically, but its “independent”
> wording and ownership questions are superseded by `CONTRIBUTION_PROVENANCE.md` and
> `P3_DERIVATIVE_RELEASE_REVIEW.md`.

日期：2026-10-27（Europe/Berlin）
性质：独立本地源码候选验收。未创建远程仓库、未 push、未创建 tag 或 GitHub Release。

## 结论

**READY FOR PRIVATE GITHUB STAGING: NO**

隔离候选已成功封装并通过 CPU 回归，但项目代码的版权归属、发布授权和
`mjlab` 相关实现的署名边界尚未得到作者本人确认。在这些 BLOCKED 项解除前，
不得确认候选可发布，也不得创建候选 commit。当前仓库是已初始化的 unborn `main`，
不存在本地 commit hash。

## 1. 隔离仓库

- 绝对路径：`/tmp/SuperMimic-LowVRAM-P3A-20261027`
- 初始 Git 仓库：`main`，无 commit、无 remote、无 tag
- 源工作区 HEAD：`d9be385b3eeb13a638fb33fb200d3bfd9be9839f`
- 源工作区 branch/remote：`main` / `https://github.com/CuboiLeo/SuperMimic-Reproduced.git`
- 原工作区、remote、分支、HEAD 和已有未提交修改均未改动

候选由 `release/public_files.txt` 机械复制生成。复制后没有带入原始 `.git`、
REVIEW 文件、`external/`、`data/`、`logs/`、checkpoint、虚拟环境或备份。
候选内的 `.git`、`.venv/`、`dist/` 和测试缓存均为候选生成物，不属于 PUBLIC payload。

## 2. PUBLIC 数量与 P2 对比

P3-A 最终 PUBLIC 清单为 **130 个文件**，其中：

- 129 个为 P2 原有 PUBLIC 文件；
- 1 个为新增的本验收报告 `docs/P3A_VALIDATION.md`。

在开始 P3-A 修复前，P2 的 129 个文件与本轮复制的 129 个文件逐文件完全一致：
文件数量 129、大小 915,480 bytes、全部 SHA-256 相同。P3-A 随后为修复独立候选缺陷
修改了 6 个文件，并新增本报告：

| 文件 | P3-A 原因 |
|---|---|
| `.github/workflows/ci.yml` | PUBLIC-only checkout 使用候选审计模式 |
| `docs/DASHBOARD.md` | 删除指向未发布 REVIEW 文档的死链 |
| `docs/PUBLISH_MANIFEST.md` | 说明 source-workspace 与 PUBLIC-only 审计语义 |
| `release/public_files.txt` | 纳入本报告 |
| `scripts/release_audit.py` | 增加 `--candidate`；要求 PUBLIC 齐全且 REVIEW 必须缺席 |
| `tests/test_repo_hygiene.py` | 用不存在的探针路径验证忽略规则，不再要求受限目录预先存在 |

因此最终候选相对 P2 为：**123 个原文件不变、6 个文件修复、1 个文件新增**。
这些变化只涉及发布封装、CI、测试和文档，没有修改研究算法、loss、优化器、
安全阈值或训练数据。

## 3. SHA-256 清单

以下为除本报告自身外的 129 个候选文件。报告不能把自身最终内容的 SHA-256 嵌入自身，
因此 `docs/P3A_VALIDATION.md` 按定义不在此表内；其哈希可在报告写完后单独计算。

```text
a08c5fc47b9dfa10056da6ae66e16cfc9b9792e19733fafef68e92b25ba46ca8  .github/ISSUE_TEMPLATE/bug_report.yml
f928b3a0564255b0cc2fe83b278658c15a9c31bedb1c662bea1bd57b143f0b76  .github/ISSUE_TEMPLATE/config.yml
bd4feb3319146d2fdd607bf19efbbc720ccc22882295ad7613fbd3d0f03334df  .github/ISSUE_TEMPLATE/feature_request.yml
d25e17341d17e820a107eb9659ee32b092fec24def257351a38d2125b7ee700c  .github/PULL_REQUEST_TEMPLATE.md
990914b0fa4c90a0e1fb57e00edb89a455899b676c2f9614948933bf29fe5a3f  .github/workflows/ci.yml
d2f5f5b66286d10683eca4c80e05445fc082b3ad03ed2bcc9d7e42d1db152f99  .gitignore
7b55f8e67b5623c4bef3fa691288da9437d79d3aba156de48d481db32ac7d16d  .python-version
cd85c79c5583bb04d587ab66a06635fad49795663ea388a3f529ba77e66641cf  CHANGELOG.md
55e696e426ce772296b27afadea15ea4b67d0ea3b3ce226692f547297243ec8c  CONTRIBUTING.md
9892007d6c8f8b28c00a48557289fa42a285915cb500b5cf01ec2bb0c15f197f  LICENSE
3fb2b8b7f9ac73b39c812c3ee8b57241ac90b22c31acc8eb9d58ca6f1512fb7e  README.md
e33215a55f6e1079d1259e56e278e175382b732b6ff16b29b13de2460eaed96e  THIRD_PARTY_NOTICES.md
dfd325eb8ff5f0f10631a41c8a7f2915b7137b27230e76548cd80e7279855b46  docs/ARCHITECTURE.md
8f0b887a710018438fa16a4a317d49ed3f1d991fc534b91f6b004195423acfa0  docs/DASHBOARD.md
6cde9e820c3fa2358ea8abb8ea59b1357fd105c8cda424fb6cc5db3ca9a847d9  docs/EXPERIMENTS.md
311b9a30a83f4e81d7ffaf46ce7d947bcefa30b5841f2a9ce3dcc43b69c6f1f1  docs/KNOWN_ISSUES.md
22713779f06dca39666fb122641954d66328ff5b29def7721d820ec9bccbde51  docs/P1_VALIDATION.md
16adceafe19fb923dab17aa2c75d0191a04f72974cc124d542e2e24125441a4e  docs/P2_VALIDATION.md
ff0dbadf4c21638e368dbfee1130e17fa97c438fc4bd1d6bdf404c9af5bd3c09  docs/PAPER_SPEC.md
229c6b0c1b0fba6227a4bcfa79f18faf7e99d9ffdcd2209c18b5dadb59fab953  docs/PUBLISH_MANIFEST.md
51a2553aadc4a0bbe3f21ced4ba2adc711755dadc22e73f41b530e467c887c70  docs/QUICKSTART.md
f83da3e567e208e0208af39ae71e256b5ed2cbf470bb2cd4c86be3397ec0d399  docs/RELEASE_CHECKLIST.md
73d00cdd0aeaf4bcee610960b6576180ab40507b6d64ace2fd8bdedb533121f6  docs/REPRODUCTION.md
a78933feb7b01cc7434017985a26eef41d61d24a56156e9e05eea772a2727482  docs/REPRODUCTION_PLAN.md
75ba262d53419062d8cfb87b122421064ddb2c532ba71c2093efe7b96ba1b09f  docs/REPRODUCTION_STATUS.md
b3d98221290d37fb0adc77693b4d51419581909ecf5f4d961ae5154344486d54  docs/REVIEW_LOG.md
36ea65ed3e07a0af3318341e1a1416c69f3cada9d27b758ac058a7d2046544e6  docs/assets/low_vram_512_900_resources.svg
61a42dbeba9d36db9d778409027f3361e4f95df7d36fc3a6f2e83d41a1f00d15  experiments/__init__.py
bbc01568d1edb84c4ccbbe4620dd1893b9a9826388b3362e473975c9e307febb  experiments/low_vram_vibed/README.md
9b811d61dacab268f52a4a02d527e656f4dae1286e4b0479c25a28fdbcc44177  experiments/low_vram_vibed/__init__.py
f5711f590e0a7b000076a00036ea4311ba27c75de8395d8149426bb548ff1309  experiments/low_vram_vibed/checkpoint.py
4b62a098cef316822a1b1b423cca56f18b3520c596a0b1c34765548abfd9ac8b  experiments/low_vram_vibed/config.py
5ae4af99f137dab808176bfdd9dabc955c1ea8f7c1be41ec58be5743d6519897  experiments/low_vram_vibed/configs/experimental_768_900.json
17007e2f02496f5572eb0950ae0b9116c8800d826532f82718b788a36773466c  experiments/low_vram_vibed/configs/smoke_16_510.json
63f67dd6c2d39279af482d9a5788ee98d96b7e62fcb4aef2ef9348bb1c641ed0  experiments/low_vram_vibed/configs/untested_1024_900.json
45f1fe260cfc46dfb3ceb461b8802c14eed176403c4aa407fc7d1dc3624e7319  experiments/low_vram_vibed/configs/untested_formal_512_14000.json
4d7c2978f706520738d379d16e2c47194011f27637e90a8f5c151a9404bfc250  experiments/low_vram_vibed/configs/verified_512_900.json
be42e21cea39f70169b4bbd45f1e987485dea3068738216b473e8ec3ad1b7391  experiments/low_vram_vibed/fetch_upstream.py
45dd74b078a4ad18b200d449df4a3c353e83ec4c6dd3cc23d829af3de3e9f483  experiments/low_vram_vibed/finish.py
1603e1b15951ed91888a839314ea98d02f362f8540eba7b3cdb4c5ff82f80e0a  experiments/low_vram_vibed/perf.py
6d7c042a0c73fab06a770c03cd36a5680c7a513e569979ce2963fdda25c5aaed  experiments/low_vram_vibed/provenance.py
211c95635142a96869e461dade7908f1de4bd0546aae601defadf60be169e0a0  experiments/low_vram_vibed/run.py
fc88f824171df4b450c2bbcf2195d7822a26c61d8138ee3838b1ed8839f74ddf  experiments/low_vram_vibed/smoke.py
9481cd504db93a1e7668eb89e7a67e789c04580560c3304458c16aad880bdf7d  experiments/low_vram_vibed/tests/test_profiles.py
4036c34190c7f9c48c5415d45185526ec91b5ad9f8ed2afcdf9db5d2fc0ef58a  experiments/low_vram_vibed/tests/test_wrapper_cli.py
f058b609573772c535903e14fe3db7c147c49571ca460cf696799ed5bc3724ed  experiments/low_vram_vibed/upstream.json
feb76af5085a53b988be8f4940a54b69af8c6a99fdd4012bc3ba712bfd1b1ca0  monitoring/__init__.py
5048e4ede784c4c29ea93ce7e724b4850ad3bbddc1e71636408f907c9ed894d7  monitoring/eta.py
7c71fd2a263106b42c31f13aa3486e183c5cb425296724e7652efb36c62c83ce  monitoring/index.html
50fde889ccf48c36ea3c17f80de794c80c11dcd620068cef288023f3443b67d3  monitoring/resources.py
16eaa6f00d9733a3d2dcdbd0e33c361501c72f0fcc1a81838e7e718ddcbd57e3  monitoring/server.py
4188953025865a9044b8ee1382e61ffba9f934dbcea2fae7e101905f05e0fa45  monitoring/status.py
cc9bce9a1b318c60b7cdf5d7bb7b0bf66bf80519bd8e7adc056a3abfe41958af  monitoring/vibed.py
150b3dbcaf5bee8427781fc4215963b1cc12e7e77d1e0fb74ce92d43668a73b2  pyproject.toml
0340c66ce7c5a2062c7b7c54843c08f93f01d6c13248b867c2b06444568bdf53  release/public_files.txt
67f00bc1f4929eb3a6a10dc7375bea67c99bafb4638d160a66be7c06f26d6bf7  release/review_files.txt
fd17c15654b89082ecd8cb544f69c78d66d9b7c872ee4a469cfcedddc5f883c7  scripts/bench_imagination.py
8a2d4b0609d8fab3de3e045c45fdd74dbaae77633613cc1dc4e214b45a0dff23  scripts/bench_sim_speed.py
a3fd8a011f4df1ff00227787a4ba2d3bf7464c15faba65b87edf64cf90bb53ee  scripts/data/build_library.py
b56990148d95710438816131ef3f2ffcb8d7692adfc94600c6d51f66953c664e  scripts/data/csv_to_npz_batch.py
2066d94a5bb3e6eb0abd7fc23f3efa99adf1ec9b07ff6e04712cd34ad0baa789  scripts/data/filter_bones_seed.py
2b3aa734f3f3096ffb7d186db5280ee6d93e42ad03540e6e5a99c80c2c5d347b  scripts/diag_drift.py
a55af1c84945133ab7340efb2e869f40e2edda3df89667b3433cdf06483e414c  scripts/eval_benchmark.py
25859b322f290eaeb7e5ecf27ef206d00e1bba6f39ee1c9ad0233e5dba54e45c  scripts/eval_push.py
770f1ec70198ab362018ca5ae886e2f4e4973979ef0939c56e1ed640b31c39f7  scripts/play.py
bbba1f57cbab0d03167560791f6225bd683648a500f978a884a8494599523a41  scripts/plot_vibed_resources.py
16404d0b7f054701a94c940a14cf0f3aa1b5ba6ae937e882978d566185f956d7  scripts/release_audit.py
36ba9d359b6184fe2a4514df06d90e16c05e5edc1976a24f35d4936747f37e07  scripts/tb_tail.py
e772797e9137cd86f79933662f3082604838ecc81d80b2290b3fd03039bed39f  scripts/vibed_check.py
2c3a6bba4beadcb5a254bdb8a56df54c76d4e648e10bd8d30327a2ef65763e3b  scripts/vibed_finish.py
e329572ce163c0704e935ad27b8044cdc28b5aa98fb05c0ae52f33cc3eae12c8  scripts/vibed_perf_report.py
5af45237e8addce2b685966be1fcd3dee573873f1ba4e41483438152c3100a52  scripts/vibed_run.py
125f22c257d97507d23ebfb893b5afc51031273f46c9dbbc079800df93064111  src/supermimic/__init__.py
a76ab80d738f2b706ea3f030a1a6fa2a4f44dfb4e6454224ed45d666f9ab3992  src/supermimic/config.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  src/supermimic/data/__init__.py
219d7c3a6ac317939f684e64a6f5b10d6fe7246f44bcf9ecfbe38041027f1306  src/supermimic/data/motion_convert.py
8f1b64cac80fca0a8fe548c0190eb1bfdd1b5f399c44f01d5e30b6e409d0784a  src/supermimic/data/recorder.py
e9689eda57ff95c2cf5f618c1e29d533f67390647e05fe91ad3504dc41c6d3b0  src/supermimic/data/replay_buffer.py
1489391ed86aefc970651989774178018a94a020830b711b2bbb9e3ac94c715d  src/supermimic/envs/__init__.py
1aff867e972ba837cc66f61dced65aefc7a16430b21a9520c7a23423e7c97c24  src/supermimic/envs/actions.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  src/supermimic/envs/mdp/__init__.py
8dfab184c80903a930133d9c632c9aa04a1e78a9c3b7e6547d9eda95e2310dc7  src/supermimic/envs/mdp/commands.py
359261b2330b8eb5961559e27ac105e053643c780a0ec91085354637c7ede966  src/supermimic/envs/mdp/motion_library.py
7783bc1715269b4c011a2492557716e2ed59a7de7869452a64d748c6e1e94cea  src/supermimic/envs/mdp/observations.py
34f53e7164097427b93cb5da7cdea755597b61a4ae389801eea6ddf7401a7407  src/supermimic/envs/mdp/rewards.py
6335cfe6995b69b3b38d3441b7caca8156bd3b7643d2b2d6691b22276cb7a9b0  src/supermimic/envs/mdp/terminations.py
9e4d05a5fc2e12453bfa4cb14aba936f32cd7935f5a093e4c9109c98b8e618d5  src/supermimic/envs/sim_context.py
59d119ec4c7bee6403d0f8dddc4237c8d8a32cc6054711afbb3ae7ff683fb4b6  src/supermimic/envs/state_io.py
54c3bc7a81221b9e4e1a94935bed1040427af1b715ab46e33f10190403914404  src/supermimic/envs/tracking_env_cfg.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  src/supermimic/eval/__init__.py
93cccf356f511fe045e6850b5a34a89bd7c7ae78f9e05951d71b4fb9e9ec2280  src/supermimic/eval/benchmark.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  src/supermimic/imagination/__init__.py
83be5834e305714deb37d04cca08087ce7f8fe31981b95060f7a5ec4377f4be0  src/supermimic/imagination/compiled.py
958f90b0364deaa76de64d4ce3d7c8b124af0bc9a13a93ceb2e1b8c8039ea86a  src/supermimic/imagination/feedback.py
3c93ec24c0f26db7bd4d60c5da50bc4a4d711a70a72ba0c9dfc7b078f082f774  src/supermimic/imagination/objective.py
08d17fd65cdce4e55c8fdecd8ba25d85573fda262d784f38b42f0b580a22fd8f  src/supermimic/imagination/policy_trainer.py
f217001b4cc70114f0197d79833dd55c00170e67e6b6e16d070fb4e383448aac  src/supermimic/imagination/rollout.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  src/supermimic/kinematics/__init__.py
4635eea9db60cc1f0541a1ed480986392984dbf8e83802775bb3d53665a91657  src/supermimic/kinematics/g1_fk.py
e4120edd12b5fdf97a1927a6d4a14b392d2d2736308bb473f6ffa89219aa0c47  src/supermimic/kinematics/rotations.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  src/supermimic/policy/__init__.py
0340fbaf8139c2078dc6f0065625ee7d6aea5ccc964d72e35808973e2e33ce79  src/supermimic/policy/nets.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  src/supermimic/scripts/__init__.py
8afeeda3739bf2200b9bdf7b148442de19b1a0d07689a475734ae5ef744d72f2  src/supermimic/scripts/train.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  src/supermimic/training/__init__.py
ec1e52eb91160444913516a0e4973af65678aa0c6e9c761f04ee4b8ceeb855a6  src/supermimic/training/checkpoint.py
ebf2d6d37ce6102f55941c0ab328c9deb4021964c46f7bd35a8bc1bb767f5a21  src/supermimic/training/distributed.py
bdc355e38c2c5fac4efb04d1c164ca9c9e359480b28e6272a81d0089794a5164  src/supermimic/training/loop.py
369edd3044ebf5cb8794f0bb31730024ea007bfab4994ab6ba909eedf91c0b9b  src/supermimic/training/numerics.py
3848bc4432d6f87bc81d93660dff0cbe7491122f4f0413c42808be27cef6c2ee  src/supermimic/training/schedule.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  src/supermimic/world_model/__init__.py
ce21b40a69c6abddebd85e7e2f000fadfd37f9bebbdecd5d61510e1f68736cd7  src/supermimic/world_model/dynamics.py
1af9d3e47e2914fc0ff4154ba0cb2c53413b75cebdb81eb4d3aeed8928582e22  src/supermimic/world_model/heads.py
5e2cbc177056f010a1f4df80d9a3b4cf3ec4b5e84f0ff6a2c05d195500019c72  src/supermimic/world_model/state_spec.py
3f38c3045e227889f66169f0cdfa783d93820a2d44812c03b38c7388ac8ab211  src/supermimic/world_model/wm_trainer.py
24a6157e285584fd1f8433360cc93b2c0b5fe68395fa46ccc4358109ce0e7ba2  src/supermimic/world_model/world_model.py
acba94677b6bdcd9a9350e659ed00e8eb970df0ee8a030dde15397808a69adc8  tests/test_analytic_heads.py
83aa4d895908ecfc522385b86f20bed9db4e363c768655e8d7cdc5e13d8955ef  tests/test_benchmark.py
50c9e31f0c48989718a32bab920d214abe4b596c09da905141b8d991139c7a2c  tests/test_dashboard.py
50e90cf43b3e301e102d51d3f9b8eded58b82bc0ac049bcf0c163bd4e352e8bf  tests/test_env_smoke.py
fe69cfa469880cc13186c473834d583c6b9af498f9eaf22003353ffd6251fc6b  tests/test_eta.py
9c204b346806ba8f7d52bb1e8ee66b5c7bb97107364fe6b83b5b95a4a491c13a  tests/test_g1_fk.py
b1200a8da6410436966cdca78f8c4212f59a20cb39508db69b682673577c9e56  tests/test_imagination.py
e6de1fdc4469143325cfeb194804062a222986353142a91b6fcb15bf4731b790  tests/test_motion_convert.py
b40c8baa93718147a91d3bd695509b9d0a6a05283fdd0136a81e113c263d72d3  tests/test_motion_library_compact.py
e8ddb82f8371736920b92a4fa3a3343fc9da52c2bb85b48998d1417dfd443881  tests/test_numerics.py
0fd7c7286d32baf5530c90f81cf2a89da7b0b70b67997007637d3b6aaf5b8c5d  tests/test_repo_hygiene.py
73c97c06b078847c5c02be7720c238602c94b742ff1ad2f3de508f0d5fdd6b50  tests/test_world_model.py
0b7f650ed31337967af38d1735380631f2da020f6aaec913bd8d5fb048e7732b  uv.lock
```

## 4. 本地 Git 状态

- 仓库已初始化：`/tmp/SuperMimic-LowVRAM-P3A-20261027/.git`
- branch：`main`，unborn
- 本地 commit hash：**无**
- remote：无
- tag：无
- Git 作者/提交者身份：当前环境未配置 `user.name` 或 `user.email`

未创建 commit 是刻意的安全结果：P3-A 要求在阻断项处理完成后才提交，而版权归属和发布授权
仍是 BLOCKED。禁止通过新 Git 历史抹除原作者的 CuboiLeo/Yuxi Liu 历史。

## 5. 独立环境与测试

测试环境不是原工作区的简单替换。候选拥有自己的 `.venv`，其中安装了从候选构建的
`supermimic==0.1.0` wheel 和 `sm-train` entry point；CUDA/PyTorch/pytest 等已安装依赖
只通过只读 site-packages 路径借用。验证时确认：

```text
supermimic -> /tmp/SuperMimic-LowVRAM-P3A-20261027/.venv/lib/python3.12/site-packages/supermimic/__init__.py
experiments -> /tmp/SuperMimic-LowVRAM-P3A-20261027/experiments/__init__.py
torch 2.14.1+cu130
```

结果分类：

| 检查 | 结果 | 证据/边界 |
|---|---|---|
| 完整新环境 `uv sync --frozen` | BLOCKED | 离线缓存缺 `torch==2.14.1+cu130` wheel；未下载大型 CUDA 依赖 |
| 候选 wheel 构建 | PASS | sdist 和 wheel 均成功 |
| wheel 安装与 entry point | PASS | `supermimic==0.1.0`、`sm-train` 可读 |
| Ruff | PASS | `All checks passed!` |
| 基础 pytest | PASS | 34 passed、20 skipped、1 warning |
| Low-VRAM profile 配置加载 | PASS | 5 profiles：1 verified、1 experimental、3 untested |
| CPU Smoke Test | PASS | policy 输出 `[2, 29]` 且有限；`experiments/` 无禁止产物 |
| 上游 fetch dry-run | PASS | 命令只指向固定 `zita-ch` repo 和 commit |
| 已有上游来源检查 | PASS | commit `a1508d4...`、remote、license、clean 工作树均匹配 |
| README/CLI 静态检查 | PASS | 必需章节、相对链接、YAML、SVG 均通过 |
| 仓库卫生与隐私扫描 | PASS | PUBLIC/REVIEW 分类正确，无敏感命中 |
| 源码包内容 | PASS | wheel/sdist 无数据、日志、checkpoint 或 `external/` |
| GitHub Actions 实际运行 | SKIP | 未创建/推送远程仓库 |
| GPU/CUDA 和真实数据回归 | SKIP | 本轮禁止 GPU 压力测试，候选也不包含受限数据 |
| 训练、长跑、大数据下载 | SKIP | 按任务限制未启动 |

20 个 pytest skip 全部是显式条件：15 个需要 CUDA 或 CUDA+数据，4 个需要 LAFAN1 CSV，
1 个需要外部 `supermimic_vibed` checkout。不能用 P2 原工作区的 39 passed/15 skipped
替代本结果，也不能把 skip 当作 pass。

首次封装备份还发现并修复了两个真实 FAIL：PUBLIC-only checkout 中 release audit 对 REVIEW
缺失报错，以及死链指向未发布 REVIEW。修复后两者均通过；最终没有残留测试 FAIL。

## 6. 许可证、版权与署名审查

| 项目 | 结论 | 状态 |
|---|---|---|
| 根 LICENSE | MIT，`Copyright (c) 2026 Yuxi Liu` | 文件内一致 PASS |
| 原仓库历史 | 5 个 commit 均记录为 Yuxi Liu / CuboiLeo GitHub noreply 身份 | 仓库证据 PASS；法律归属 BLOCKED |
| CuboiLeo 关系 | origin 与提交身份同属 CuboiLeo 名称，remote 指向 `CuboiLeo/SuperMimic-Reproduced` | 账号/作者本人关系需人工确认 BLOCKED |
| 独立 mjlab 实现的发布权 | README 声称 from-scratch，但历史记录不是独立法律证明 | BLOCKED |
| `supermimic_vibed` | MIT，`Copyright (c) 2026 ETH Zurich, Chong Zhang`；固定 commit，未 vendored | PASS |
| mjlab | Apache-2.0，The MjLab Developers，固定 commit `8bb2bc9...` | 依赖记录 PASS；改写署名边界 BLOCKED |
| Isaac Lab | BSD-3-Clause，固定 commit；未装入候选 | PASS |
| `torchrunx` | mjlab 间接依赖，声明 GPL-3.0 metadata；未 vendored | source-only 仍待法律复核 BLOCKED |
| LAFAN1 G1 retargets | CC BY-NC-ND 4.0；没有 CSV/NPZ/派生库 | PASS |
| BONES-SEED / Unitree 素材 | 未包含；文档要求独立核对条款 | PASS |
| 图表 | `docs/assets/low_vram_512_900_resources.svg` 由本地真实 telemetry 生成，ARCHITECTURE 记录来源 | 无未署名上游媒体 PASS |
| 论文引用 | README 与 notices 给出 SuperMimic 作者、CoRL 2026、arXiv:2610.28480 | PASS |

不得只凭相似度推断原创性。本轮仅用静态比较定位需人工确认的文件：除关节名、body 名、
少量包装 API 外，以下文件在注释或实现中明确表达与 mjlab 的对应关系，尚不能由仓库记录
证明全部属于本项目作者独立创作：

- `src/supermimic/data/motion_convert.py`
- `src/supermimic/envs/mdp/commands.py`
- `src/supermimic/envs/mdp/rewards.py`
- `src/supermimic/envs/tracking_env_cfg.py`

这些文件标记为 **BLOCKED pending owner/license confirmation**。如果确认包含实质性改写，
必须保留 Apache-2.0 所需版权/许可证/变更说明，不能仅由根 MIT 覆盖。本轮没有自动改为
PUBLIC、没有添加新的 MIT 头，也没有删除相关代码。

## 7. README 与 GitHub Actions

README GitHub 展示检查通过：

- 标题、项目描述、非官方/alpha 状态明确。
- Installation、Quick Start、Features、Limitations、Low-VRAM、结果图表、Known Issues
  和 Roadmap 均存在。
- 架构 Mermaid 图和真实 telemetry SVG 由 PUBLIC 文档引用。
- 原论文引用和 `zita-ch/supermimic_vibed`/mjlab 等署名存在。
- 历史 5090 结果与当前 8GB 结果、短测与收敛声明的边界清楚。

GitHub Actions 静态检查通过：

- `permissions: contents: read`，没有额外写权限。
- Python 固定 3.12，uv 固定 `0.13.5`，依赖由 `uv.lock` frozen 安装。
- 只运行 Ruff、CPU pytest 和候选 release audit；无 GPU、训练、数据集或 secret 依赖。
- P3-A 修复后 workflow 调用 `release_audit.py --candidate`，适配 PUBLIC-only checkout。
- 远程 Actions 尚未运行，Mermaid/SVG 的 GitHub 实际渲染也未视觉确认。

## 8. 当前阻断项

1. **BLOCKED：** 作者本人尚未确认 Yuxi Liu、CuboiLeo 账号与本任务用户的身份关系。
2. **BLOCKED：** 作者尚未声明有权以 MIT 独立发布全部 130 个 PUBLIC 文件。
3. **BLOCKED：** 4 个明确与 mjlab 有实现/API 对应关系的文件未完成版权与 Apache-2.0
   署名边界确认。
4. **BLOCKED：** `torchrunx` GPL-3.0 metadata 与整个锁定依赖图尚未完成法律复核。
5. **BLOCKED：** 因上述权利问题，候选 commit 尚未创建；Git 身份也未配置。
6. **环境限制：** 无网络缓存情况下不能重建完整 CUDA 环境；不影响已安装依赖上的 CPU
   回归，但不能宣称 fresh-environment install 已通过。
7. **待远程执行：** GitHub private staging 后的 Actions、secret scanning、dependency
   alerts 和渲染检查尚未运行。

已有训练不稳定、768/正式 512 profile 未完成、1024 未测试、15+ 个 GPU/数据测试跳过等，
是必须在 alpha 文档中保留的已知限制，不应通过放宽阈值或替换测试结果解决。

## 9. 是否可进入私有 GitHub staging

**NO。** 代码封装和 CPU 候选质量已通过，但版权归属、独立发布授权、mjlab 相关文件署名
和依赖法律复核尚未解除。进入私有 staging 仍需用户明确授权；本任务没有执行任何远程操作。

## 10. 需要用户人工确认

1. 确认 Yuxi Liu 与 GitHub `CuboiLeo` 账号/本任务用户是同一权利主体。
2. 确认有权把全部拟公开的原创代码、文档和图表以根 MIT 许可独立发布。
3. 确认与历史 CuboiLeo 仓库的贡献关系，并同意不抹除原 Git 归属。
4. 对上述 4 个 mjlab 相关文件确认：完全独立创作，或列出需要保留/补充的 Apache-2.0
   attribution、license text 和修改说明。
5. 确认 PUBLIC 中不存在尚未署名的其他实质性改编或素材。
6. 完成 `torchrunx` 和锁定依赖图的 legal review；继续坚持 source-only，不打包环境/wheel 集合。
7. 批准最终 130 文件 PUBLIC 清单，并确认 P3-A 的 6 个封装修复。
8. 配置候选仓库的 Git 作者/提交者身份并明确授权创建本地 commit。
9. 只有以上确认完成后，再单独授权创建私有 GitHub staging；仍不得自动 push 或 Release。

**READY FOR PRIVATE GITHUB STAGING: NO**
