# Reproduction Guide and Evidence Status

This document is the public evidence-oriented guide. It separates implementation, hardware,
and evidence quality. It does not claim that the full paper has been reproduced.

## Evidence Policy

- **Verified here**: a retained local artifact supports the narrow statement.
- **Partial / experimental**: execution evidence exists, but the run stopped or does not
  establish the intended outcome.
- **Historical, not revalidated**: a result is recorded in documentation, but the original
  log/checkpoint is not retained in this workspace.
- **Untested**: no execution evidence exists.

Short execution, a finite checkpoint, or a resource guard pass is not evidence of
convergence, tracking quality, or end-to-end reproduction.

## Track A — CuboiLeo-derived mjlab Implementation

Track A is the primary implementation inherited from
`CuboiLeo/SuperMimic-Reproduced@d9be385`. It includes upstream data conversion,
differentiable G1 FK, analytic heads, a world model, BPTT actor-critic, checkpointing,
evaluation, and local diagnostics; this derivative adds numerical guards, additional
tests, and release evidence. File-level authorship is recorded in
[`CONTRIBUTION_PROVENANCE.md`](CONTRIBUTION_PROVENANCE.md).

| Area | Status | Evidence boundary |
|---|---|---|
| LAFAN1 conversion and structural audit | Verified locally | 40 clips, 441,140 frames at 50 Hz; local audit retained outside Git |
| G1 FK and analytic heads | Verified locally | Comparisons against MuJoCo/mjlab in tests and retained logs |
| 16-environment reset/state playback | Verified locally | Short simulation evidence retained outside Git |
| World-model short training | Verified locally | Short optimizer run with finite outputs |
| H=8/16/32 short BPTT | Verified locally | Short execution and finite parameter changes only |
| 500-step checkpoint | Verified locally | Finite weights and optimizer state retained |
| 509-step continuous run | Failed | Non-finite critic metrics and action/reward growth |
| Actor-feedback stability | Unresolved | Guard stopped the run; lower learning rate did not establish a fix |
| Stable unattended training | Not achieved | No qualifying run |

The CPU suite exercises pure-Python and small numerical paths. CUDA/data tests are
present but skip when their prerequisites are absent. See `tests/` for the exact skips.

## Track B — Low-VRAM Compatibility Layer

Track B wraps, but does not modify, `zita-ch/supermimic_vibed` at commit
`a1508d42c9d1699a52e8233ab16d08c488441ab9`. The upstream license is MIT with copyright held
by ETH Zurich and Chong Zhang. The checkout remains outside Git in `external/`.

### RTX 5060 Ti 8GB results

| Configuration | Result | Stop condition | Interpretation |
|---|---|---|---|
| 128 / 64 / 128, H=32, 14,000 iterations | Completed finite training; normalized return 0.597475; 18/40 failed | None reported | Execution completed, but quality is materially below the upstream report |
| 256 / 128 / 256, H=32, 900 iterations | Completed; finite checkpoint; 291.12 s | None reported | Short execution/resource test |
| 512 / 256 / 512, H=32, 900 iterations | Completed; finite checkpoint; 297.10 s; GPU sample peak 5412 MiB | No system Swap growth in the measured window | Short execution/resource test, not convergence |
| 768 / 384 / 768, H=32, 900 iterations | Stopped at iteration 570 | 76 KiB whole-system Swap growth | Partial capacity probe; final checkpoint not verified |
| 1024 / 512 / 1024, H=32, 900 iterations | Not run | Deliberately skipped after 768 guard failure | Untested |
| 512 formal, 14,000 iterations | Stopped after 6.1 s at iteration 0 | 23.816 MiB whole-system Swap growth | No formal result |

The 512/256/512 run's real resource telemetry is shown in
[`ARCHITECTURE.md`](ARCHITECTURE.md) and was generated from a retained local `resources.csv`.

### What the profiles mean

- `verified_512_900` verifies only short execution, guard behavior, and finite checkpoint
  state on one machine.
- `experimental_768_900` records an incomplete run and a resource guard trigger.
- `untested_1024_900` and `untested_formal_512_14000` have no successful execution.

Do not merge Track B outcomes with Track A metrics. The networks, environment, and update
implementation are different.

## RTX 5090 Historical Records

The experiment log contains historical records from one or more RTX 5090 machines. Their
original logs and checkpoints are not retained in this workspace. They are useful only as
documented history.

| Record | Reported value | Qualification |
|---|---:|---|
| e2, paper observation | 0.56 return, 9/40 failed | Historical, not current verification |
| e3, anchor-relative observation | 0.824 / 0.904 return | Uses an observation variant that differs from the paper definition |
| e5, BONES-SEED subset | 0.934 / 0.935 on 2,000 clips | Historical; data and compact library absent locally |
| e6/e7 | Incomplete records | No current cross-hardware validation |

No RTX 5090 value is presented as current RTX 5060 Ti evidence.

## Reproducing the CPU Gate

```bash
env -u PYTHONPATH CUDA_VISIBLE_DEVICES='' uv run pytest -q -rs
```

Expected release-candidate behavior is a passing CPU suite with explicit skips. The exact
count is recorded in `P2_VALIDATION.md` after the final run; counts from older revisions
must not be reused.

## Revalidating Low-VRAM Provenance

```bash
env -u PYTHONPATH uv run --no-sync \
  python experiments/low_vram_vibed/fetch_upstream.py --dry-run
env -u PYTHONPATH CUDA_VISIBLE_DEVICES='' \
  uv run --no-sync python experiments/low_vram_vibed/smoke.py --require-upstream
```

The second command confirms the remote, commit, clean source state, profiles, CPU forward
pass, and absence of forbidden artifacts under `experiments/`.

## Reproduction Blockers

1. Stable long training has not been demonstrated.
2. Actor feedback instability remains unresolved.
3. The full benchmark has not been independently revalidated for the current workspace.
4. The formal low-VRAM launch did not pass the zero-Swap startup gate.
5. Historical logs/checkpoints and restricted datasets are unavailable for local review.
6. Dependency and asset licensing must be reviewed before a tagged release.

## Data and Asset Boundary

LAFAN1 G1 retargets are CC BY-NC-ND 4.0. BONES-SEED, Unitree assets, and upstream demo
media have separate terms. This repository distributes neither the datasets nor their
derived motion libraries, checkpoints, or videos. Follow the original providers' access
and usage conditions.
