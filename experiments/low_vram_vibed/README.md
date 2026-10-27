# Low-VRAM `supermimic_vibed` integration

This directory is the isolated compatibility layer for running the third-party
[`zita-ch/supermimic_vibed`](https://github.com/zita-ch/supermimic_vibed) implementation on
consumer GPUs. It is not merged into the independent `src/supermimic` implementation in the
repository root.

## Boundary and provenance

- Upstream repository: `https://github.com/zita-ch/supermimic_vibed.git`
- Pinned commit: `a1508d42c9d1699a52e8233ab16d08c488441ab9`
- Upstream license: MIT, Copyright (c) 2026 ETH Zurich, Chong Zhang
- Expected checkout: `external/supermimic_vibed/` (ignored by Git, never vendored)
- Upstream source policy: the three training networks, losses, rewards, observations and update
  order are unchanged. This layer adds only profiles, process/resource supervision, checkpoint
  inspection and postprocessing wrappers.
- If a future change requires editing upstream training source, stop and evaluate a separate Fork
  release instead of merging it here.

The exact pinned metadata is in [`upstream.json`](upstream.json). Repository-wide attribution and
license notes are in [`../../THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md).

## What is included

```text
experiments/low_vram_vibed/
  upstream.json                 pinned upstream repository and commits
  configs/                      verified / experimental / untested profiles
  config.py                     profile schema and safety validation
  provenance.py                 read-only checkout provenance checks
  fetch_upstream.py             dry-run or fetch the pinned checkout
  run.py                        resource-supervised upstream training wrapper
  checkpoint.py                 CPU checkpoint finite/count validation
  finish.py                     serial evaluation/render/plot wrapper
  perf.py                       native CSV throughput comparison
  smoke.py                      no-GPU profile/provenance/import smoke check
  tests/                        profile and provenance regression tests
```

The legacy paths `scripts/vibed_run.py`, `scripts/vibed_check.py`,
`scripts/vibed_finish.py` and `scripts/vibed_perf_report.py` remain as thin compatibility wrappers.
Shared process-tree/cgroup telemetry remains in `monitoring/` because it is also used by the
independent implementation's diagnostics.

## Profiles

| Profile | Status | Scope | Configuration |
|---|---|---|---|
| `smoke_16_510` | Untested | execution-chain smoke template | 16 env / WM 32 / Policy 32 / H=32 |
| `verified_512_900` | Verified | short execution/resource test | 512 env / WM 256 / Policy 512 / H=32 |
| `experimental_768_900` | Experimental | partial capacity test | 768 env / WM 384 / Policy 768 / H=32 |
| `untested_1024_900` | Untested | capacity probe | 1024 env / WM 512 / Policy 1024 / H=32 |
| `untested_formal_512_14000` | Untested | formal training template | 512 env / WM 256 / Policy 512 / 14,000 iterations |

`verified_512_900` means only that the 900-iteration run completed, remained under the configured
resource guard and produced a finite checkpoint. It does not establish convergence, tracking
quality or readiness for an unattended run.

The 768 profile stopped at iteration 570 after 76 KiB of whole-system Swap growth. The 1024 profile
was never run. The previous 512 formal launch stopped after about 6 seconds because whole-system
Swap grew by 23.816 MiB. See [`../../docs/REPRODUCTION_STATUS.md`](../../docs/REPRODUCTION_STATUS.md).

## Setup

The core repository and this compatibility layer intentionally use separate environments. The
upstream checkout was developed against Isaac Lab `46d6cc3d7b115906fad12efd372fbf69f4e3d3ed`; follow
the upstream README for its Isaac Lab, data and environment setup. Do not copy an upstream virtual
environment, model, replay or log directory into this repository.

Inspect the command without changing the filesystem:

```bash
env -u PYTHONPATH uv run --no-sync python experiments/low_vram_vibed/fetch_upstream.py --dry-run
```

Fetch the pinned top-level checkout only when explicitly intended:

```bash
env -u PYTHONPATH uv run --no-sync python experiments/low_vram_vibed/fetch_upstream.py
```

The fetch helper refuses to overwrite an existing directory and does not download data, weights or
the nested Isaac Lab checkout.

## Validation

This check does not allocate CUDA memory or start training:

```bash
env -u PYTHONPATH uv run --no-sync python experiments/low_vram_vibed/smoke.py --require-upstream
```

It validates every profile, verifies the clean pinned upstream checkout, checks that no model/data
artifacts were added under `experiments/`, and runs a small CPU policy forward pass.

## Running a profile

The wrapper still requires an externally configured, effective cgroup with at most 4 GiB RAM and,
for zero-Swap profiles, `memory.swap.max=0`. It also refuses a missing, dirty or wrong-commit
upstream checkout. Experimental and untested profiles additionally require `--allow-unverified`.

```bash
# Illustrative command only. P1 did not launch it.
env -u PYTHONPATH python scripts/vibed_run.py \
  --config verified_512_900 --run-name <new-unique-run-name>
```

Do not weaken resource thresholds to make a run start. Do not run this command outside the intended
cgroup. A successful short test is not evidence of stable long training.

## Data and publication rules

- LAFAN1 G1 retarget motions are CC BY-NC-ND 4.0 and are not redistributed by this repository.
- Do not commit `external/`, `data/`, `logs/`, checkpoints, replay buffers, videos or upstream demo
  assets.
- Do not describe this wrapper as a fork or official implementation. It is a separately maintained
  compatibility layer over an unmodified MIT-licensed third-party checkout.
