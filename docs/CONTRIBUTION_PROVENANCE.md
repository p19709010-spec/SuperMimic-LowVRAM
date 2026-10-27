# Contribution and License Provenance

Date: 2026-10-27
Scope: local release candidate derived from CuboiLeo/SuperMimic-Reproduced

This document records file-level provenance from Git history and from the actual
working-tree diff. It is not a legal opinion and does not infer authorship from code
similarity alone.

## 1. Upstream baseline

| Item | Value |
|---|---|
| Upstream repository | `https://github.com/CuboiLeo/SuperMimic-Reproduced` |
| Base commit | `d9be385b3eeb13a638fb33fb200d3bfd9be9839f` |
| Base commit subject | `Add data package and data scripts that were excluded by an unanchored .gitignore pattern` |
| Upstream commits inspected | 5 |
| Upstream author recorded by Git | Yuxi Liu |
| Root license | MIT, `Copyright (c) 2026 Yuxi Liu` |
| Base license blob SHA-256 | `9892007d6c8f8b28c00a48557289fa42a285915cb500b5cf01ec2bb0c15f197f` |

The current worktree is based on that commit but its local changes were not committed in
the upstream repository. The project is therefore a derivative, not a newly independent
reimplementation. The new GitHub account `p19709010-spec` is not identified as Yuxi Liu or
as the author of the inherited upstream code.

## 2. Classification summary

Before the P3-A.2 attribution notices were added, comparison of the 130-file P2/P3-A PUBLIC
payload with the 69-file upstream Git tree produced:

| Category | Count | Meaning |
|---|---:|---|
| A. Upstream file unchanged | 54 | Byte-identical to `d9be385` |
| B. Upstream file locally modified | 14 | Upstream lineage plus a local diff |
| B/C. Local file added | 62 | Not present at `d9be385` |
| D. Upstream file outside PUBLIC | 1 | `scripts/pull_and_eval.sh`, retained in REVIEW |

P3-A.2 changes three of the previously unchanged Track A files only to add mjlab
correspondence notices. It also adds this provenance document, the final P3 review, and the
mjlab license/notice. The final regenerated candidate therefore has:

| Final category | Count |
|---|---:|
| A. Upstream tracks unchanged | 50 |
| B. Upstream tracks locally modified | 18 |
| B/C. Local files added | 66 |
| D. Upstream track outside PUBLIC | 1 |

The authoritative final count is recomputed after `release/public_files.txt` is updated.

## 3. A. Upstream implementation

The following inherited Track A areas come from CuboiLeo/SuperMimic-Reproduced:

- `src/supermimic/config.py`, policy/world-model networks, rollout and imagination logic;
- mjlab tracking environment, motion library, observations, rewards, terminations, actions,
  state I/O, and FK;
- the original world-model trainer, BPTT actor-critic trainer, training loop, distributed
  helpers, scheduler, evaluation, and replay buffer;
- upstream data conversion, data-building/filtering, benchmark, evaluation, play, and
  throughput scripts;
- the paper specification, reproduction plan, review log, experiment history, and original
  upstream tests.

At the final review, 51 upstream-tracked PUBLIC files remain byte-identical. They are
covered by the preserved root MIT notice, subject to any third-party notices embedded in
their dependency APIs.

## 4. B. Local modifications and additions

The following 18 upstream-tracked PUBLIC files have a local diff. Their inherited portions
remain upstream work; only the diff is a local contribution.

```text
.gitignore
LICENSE
README.md
docs/EXPERIMENTS.md
pyproject.toml
scripts/data/filter_bones_seed.py
src/supermimic/data/motion_convert.py
src/supermimic/data/replay_buffer.py
src/supermimic/envs/mdp/commands.py
src/supermimic/envs/mdp/rewards.py
src/supermimic/envs/tracking_env_cfg.py
src/supermimic/eval/benchmark.py
src/supermimic/imagination/policy_trainer.py
src/supermimic/policy/nets.py
src/supermimic/training/loop.py
src/supermimic/world_model/wm_trainer.py
tests/test_analytic_heads.py
tests/test_imagination.py
```

The substantive local deltas are:

- repository hygiene for external checkouts, data, logs, checkpoints, credentials, and
  generated state;
- replay termination labels stored on the transition source row;
- benchmark terminal-state accounting, full-reference return normalization, tracking
  errors, and explicit reset handling;
- finite-value guards before unsafe optimizer steps, diagnostics preservation, atomic
  checkpoint writes, and resumed-run replay warmup;
- independent actor/critic learning-rate scheduling and numerical-failure regression tests;
- derivative README, release documentation, lint scope, and mjlab attribution notices.

Pure lint removals in `scripts/data/filter_bones_seed.py`,
`src/supermimic/data/motion_convert.py`, `src/supermimic/policy/nets.py`, and
`tests/test_analytic_heads.py` are local edits but do not change model semantics.

The following 66 local files are additions. They are not attributed to the upstream author
as upstream features.

```text
.github/ISSUE_TEMPLATE/bug_report.yml
.github/ISSUE_TEMPLATE/config.yml
.github/ISSUE_TEMPLATE/feature_request.yml
.github/PULL_REQUEST_TEMPLATE.md
.github/workflows/ci.yml
CHANGELOG.md
CONTRIBUTING.md
THIRD_PARTY_NOTICES.md
docs/ARCHITECTURE.md
docs/CONTRIBUTION_PROVENANCE.md
docs/DASHBOARD.md
docs/KNOWN_ISSUES.md
docs/P1_VALIDATION.md
docs/P2_VALIDATION.md
docs/P3A_VALIDATION.md
docs/P3_DERIVATIVE_RELEASE_REVIEW.md
docs/PUBLISH_MANIFEST.md
docs/QUICKSTART.md
docs/RELEASE_CHECKLIST.md
docs/REPRODUCTION.md
docs/REPRODUCTION_STATUS.md
docs/assets/low_vram_512_900_resources.svg
experiments/__init__.py
experiments/low_vram_vibed/README.md
experiments/low_vram_vibed/__init__.py
experiments/low_vram_vibed/checkpoint.py
experiments/low_vram_vibed/config.py
experiments/low_vram_vibed/configs/experimental_768_900.json
experiments/low_vram_vibed/configs/smoke_16_510.json
experiments/low_vram_vibed/configs/untested_1024_900.json
experiments/low_vram_vibed/configs/untested_formal_512_14000.json
experiments/low_vram_vibed/configs/verified_512_900.json
experiments/low_vram_vibed/fetch_upstream.py
experiments/low_vram_vibed/finish.py
experiments/low_vram_vibed/perf.py
experiments/low_vram_vibed/provenance.py
experiments/low_vram_vibed/run.py
experiments/low_vram_vibed/smoke.py
experiments/low_vram_vibed/tests/test_profiles.py
experiments/low_vram_vibed/tests/test_wrapper_cli.py
experiments/low_vram_vibed/upstream.json
monitoring/__init__.py
monitoring/eta.py
monitoring/index.html
monitoring/resources.py
monitoring/server.py
monitoring/status.py
monitoring/vibed.py
release/public_files.txt
release/review_files.txt
scripts/plot_vibed_resources.py
scripts/release_audit.py
scripts/vibed_check.py
scripts/vibed_finish.py
scripts/vibed_perf_report.py
scripts/vibed_run.py
src/supermimic/imagination/feedback.py
src/supermimic/training/checkpoint.py
src/supermimic/training/numerics.py
tests/test_benchmark.py
tests/test_dashboard.py
tests/test_eta.py
tests/test_numerics.py
tests/test_repo_hygiene.py
third_party/mjlab/LICENSE
third_party/mjlab/NOTICE
```

The SVG is generated from retained project telemetry by
`scripts/plot_vibed_resources.py`. Its source run and non-convergence interpretation are
documented in `docs/ARCHITECTURE.md`; it contains no upstream demo media.

## 5. C. Third-party compatibility layer

Track B is a local compatibility layer over the separate
`zita-ch/supermimic_vibed` MIT project:

| Item | Value |
|---|---|
| Repository | `https://github.com/zita-ch/supermimic_vibed.git` |
| Pinned commit | `a1508d42c9d1699a52e8233ab16d08c488441ab9` |
| License | MIT |
| Copyright | Copyright (c) 2026 ETH Zurich, Chong Zhang |
| Integration | wrapper-only; checkout stays external and unmodified |

Local Track B files include the profiles and JSON metadata under
`experiments/low_vram_vibed/`, the provenance fetch/check scripts, resource and lifecycle
monitoring, checkpoint/postprocess wrappers, thin `scripts/vibed_*.py` entry points, and the
resource chart script. These wrappers do not copy the upstream training implementation.
The upstream checkout remains outside the candidate.

The low-VRAM results are therefore evidence for the wrapper around an unmodified third-party
implementation, not evidence for the CuboiLeo-derived Track A trainer.

## 6. D. REVIEW boundary

The following 19 files remain REVIEW and are excluded from the source candidate:

```text
docs/ACTOR_FEEDBACK_STABILITY.md
docs/LOCAL_REPRODUCTION.md
docs/OPEN_SOURCE_AUDIT.md
docs/STABILITY_RECOVERY.md
docs/VIBED_ETA_AND_256.md
docs/VIBED_MIGRATION.md
docs/VIBED_VRAM_SCALING.md
scripts/actor_feedback_experiment.py
scripts/actor_step_counterfactual.py
scripts/checkpoint_memory_probe.py
scripts/inspect_stability_failure.py
scripts/local_dashboard_check.py
scripts/local_plot.py
scripts/local_render.py
scripts/local_smoke.py
scripts/local_stability.py
scripts/local_validate_data.py
scripts/monitored_train.py
scripts/pull_and_eval.sh
```

Reasons include local run identifiers, machine-specific diagnostics, restricted evidence,
historical workflow paths, or unreviewed public evidence. No REVIEW file was promoted.

## 7. License treatment

- The upstream `Copyright (c) 2026 Yuxi Liu` notice remains the first copyright line in
  `LICENSE`.
- A separate `Modifications copyright (c) 2026 SuperMimic-LowVRAM contributors` notice marks
  the derivative contribution without replacing the upstream notice.
- Local additions are intended for source publication under the same MIT terms. The
  contributor statement and the user's derivative-publication instruction are the
  attribution record until an initial commit records a GitHub identity.
- `supermimic_vibed` remains MIT with ETH Zurich/Chong Zhang attribution in
  `THIRD_PARTY_NOTICES.md`.
- mjlab is Apache-2.0. Its full license is copied to `third_party/mjlab/LICENSE`.
  `third_party/mjlab/NOTICE` identifies the four CuboiLeo-derived correspondence files and
  the added file-level notices.
- No new MIT header was added to copied third-party source.

## 8. Evidence limits

Git history proves the upstream repository and commit contents. It cannot prove the
authorship of every line in an uncommitted local diff by itself. The user has stated that
the current work is a modification and extension of the third-party upstream project; this
document therefore records local deltas as project contributions without claiming the
entire files as newly authored.

The final initial commit must use the new GitHub account's configured identity and a message
that records the upstream repository and base commit. It must not be described as the
project's original creation.
