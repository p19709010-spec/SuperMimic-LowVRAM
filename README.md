# SuperMimic-LowVRAM

**SuperMimic-LowVRAM is a community-maintained derivative of CuboiLeo's
SuperMimic-Reproduced, focused on low-VRAM experimentation, training safeguards,
reproducibility, and developer tooling for consumer GPUs.**

> **Status: release-candidate documentation, alpha quality.** This is an unofficial
> community derivative, not an official implementation by the SuperMimic paper authors.
> The main implementation is based on CuboiLeo's
> [SuperMimic-Reproduced](https://github.com/CuboiLeo/SuperMimic-Reproduced). It has not
> demonstrated stable end-to-end training or an independently revalidated full benchmark.
> The planned repository is `p19709010-spec/SuperMimic-LowVRAM`; the Python package remains
> `supermimic`.

## Overview

This repository has two deliberately separate tracks:

- **Track A — CuboiLeo-derived mjlab implementation.** The main codebase comes from
  [CuboiLeo/SuperMimic-Reproduced](https://github.com/CuboiLeo/SuperMimic-Reproduced)
  at commit `d9be385b3eeb13a638fb33fb200d3bfd9be9839f`, with local modifications for
  safeguards, evaluation accounting, resource monitoring, tests, and documentation.
- **Track B — Low-VRAM compatibility layer.** A non-invasive wrapper around the pinned
  third-party [`zita-ch/supermimic_vibed`](https://github.com/zita-ch/supermimic_vibed)
  implementation. It adds profiles, provenance checks, resource stop guards, checkpoint
  inspection, and postprocessing. It does not merge or modify upstream training code.

Track B results are never presented as verification of Track A, and short execution
checks are never presented as convergence evidence.

## Upstream Projects

- **Main implementation:** [CuboiLeo/SuperMimic-Reproduced](https://github.com/CuboiLeo/SuperMimic-Reproduced),
  based on commit `d9be385b3eeb13a638fb33fb200d3bfd9be9839f` and its original MIT notice.
- **Low-VRAM training dependency:** [zita-ch/supermimic_vibed](https://github.com/zita-ch/supermimic_vibed),
  pinned to commit `a1508d42c9d1699a52e8233ab16d08c488441ab9` and used through a separate,
  unmodified checkout.
- **Simulation framework:** [mujocolab/mjlab](https://github.com/mujocolab/mjlab), pinned to
  commit `8bb2bc9e187797689ec82c78c35019afd2fd0376`.
- **Method:** *SuperMimic: Scaling Humanoid Whole-Body Control with One Differentiable
  World Model* ([arXiv:2610.28480](https://arxiv.org/abs/2610.28480), CoRL 2026).

The detailed file-level boundary is in
[docs/CONTRIBUTION_PROVENANCE.md](docs/CONTRIBUTION_PROVENANCE.md).

## Key Features

The world-model, BPTT, environment, data, training, and evaluation foundations are
inherited from CuboiLeo's project. This derivative adds and documents:

- fail-stop numerical checks that preserve diagnostics instead of silently skipping or
  clipping unsafe updates;
- atomic checkpoint writes and finite-value checks for network and optimizer state;
- resource-bounded low-VRAM profiles and process/cgroup telemetry;
- provenance checks around an unmodified `supermimic_vibed` checkout;
- checkpoint validation, evaluation-accounting corrections, and additional CPU tests;
- release auditing, CI, architecture documentation, and reproducibility records.

The provenance document distinguishes inherited code, local modifications, local additions,
and files still under REVIEW.

## Project Structure

```text
src/supermimic/                 Track A implementation
experiments/low_vram_vibed/     Track B profiles, provenance, wrappers, and tests
monitoring/                     Local resource telemetry and dashboard utilities
scripts/                        Data, evaluation, low-VRAM, and release tooling
tests/                          CPU tests with explicit CUDA/data skips
docs/                           Architecture, quick start, status, and release documents
external/                       Clean third-party checkout; ignored and never published
data/ logs/ checkpoints/        Restricted/local assets; ignored and never published
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for diagrams of the two tracks, the
low-VRAM launch flow, and the fail-stop protection path.

## Implementation Tracks

### Track A — CuboiLeo-derived mjlab Implementation

Track A is based on CuboiLeo's implementation in `src/supermimic/`. This derivative keeps
the inherited architecture and credits it explicitly; it does not describe the whole
implementation as locally authored or from scratch. The current workspace adds safeguards,
diagnostics, tests, and documentation around that implementation. The 509-step continuous
run encountered non-finite critic metrics, and Actor-feedback instability remains
unresolved. No stable unattended training run exists.

This code is suitable for alpha review as an engineering reproduction, not as a claim of
paper-level tracking quality. See [docs/REPRODUCTION.md](docs/REPRODUCTION.md) and
[docs/REPRODUCTION_STATUS.md](docs/REPRODUCTION_STATUS.md).

### Our Extensions

The locally verifiable additions are grouped as:

- **Training safety:** numerical fail-stop checks, diagnostic preservation, atomic
  checkpoints, finite optimizer-state checks, and resumed-run warmup.
- **Evaluation:** terminal-state accounting, full-reference return normalization, explicit
  tracking errors, and regression tests.
- **Low-VRAM tooling:** profiles, cgroup/Swap/GPU guards, lifecycle status, checkpoint
  inspection, postprocessing wrappers, and pinned provenance checks.
- **Developer tooling:** release auditing, CPU CI, issue/PR templates, repository hygiene,
  architecture diagrams, validation reports, and a measured resource chart.

These additions are not presented as upstream CuboiLeo features.

### Implementation Differences

- Track A remains an mjlab/MuJoCo Warp implementation derived from CuboiLeo's codebase.
- Track B does not merge `supermimic_vibed`; it supervises a clean external checkout.
- Track B results are not evidence for Track A, and short resource tests are not evidence
  of convergence or a complete paper reproduction.
- Historical RTX 5090 numbers are separated from current RTX 5060 Ti experiments.

### Track B — Low-VRAM Compatibility Layer

Track B keeps the upstream training networks, losses, reward definitions, observations,
and update order unchanged. The wrapper refuses to run when the upstream checkout is
missing, dirty, or at the wrong commit, and refuses to start outside its resource guards.

The 512/256/512 profile completed a 900-iteration short test with a finite checkpoint.
The 768 profile stopped at iteration 570 after the whole-system Swap guard detected
76 KiB of growth. The 1024 profile was not run. A 14,000-iteration formal launch stopped
after about six seconds when whole-system Swap grew by 23.816 MiB. These are resource and
execution results, not convergence results.

## Installation

### Requirements

- Linux with Python 3.12 and [`uv`](https://docs.astral.sh/uv/).
- An NVIDIA GPU and compatible driver only for CUDA simulation/training. CPU tests do not
  require CUDA and skip CUDA/data-dependent cases explicitly.
- The Track B upstream environment has separate Isaac Lab requirements. Follow the pinned
  upstream instructions; this repository does not vendor that environment.

```bash
git clone https://github.com/p19709010-spec/SuperMimic-LowVRAM.git
cd SuperMimic-LowVRAM
uv sync --frozen --group dev
```

The main dependencies are locked in `uv.lock`. The mjlab source is pinned to
`8bb2bc9e187797689ec82c78c35019afd2fd0376`.

Some shells export a ROS Python path that conflicts with this environment. Prefix local
commands with `env -u PYTHONPATH` if needed.

## Quick Start

Run the CPU regression suite:

```bash
env -u PYTHONPATH CUDA_VISIBLE_DEVICES='' uv run pytest -q -rs
```

Validate all low-VRAM profiles, the pinned checkout, and a small CPU policy forward pass:

```bash
env -u PYTHONPATH CUDA_VISIBLE_DEVICES='' \
  uv run --no-sync python experiments/low_vram_vibed/smoke.py --require-upstream
```

The smoke check expects the pinned checkout at `external/supermimic_vibed/`. If it is not
present, inspect the fetch plan first:

```bash
env -u PYTHONPATH uv run --no-sync python experiments/low_vram_vibed/fetch_upstream.py --dry-run
```

Then fetch only the pinned top-level checkout:

```bash
env -u PYTHONPATH uv run --no-sync python experiments/low_vram_vibed/fetch_upstream.py
```

The helper does not download data, weights, or the nested Isaac Lab repository. Follow the
upstream README for those separate installation steps. Dataset and model assets are not
distributed by this repository.

See [docs/QUICKSTART.md](docs/QUICKSTART.md) for the full installation, data-provenance,
CLI, and troubleshooting guide.

## Low-VRAM Experiments

Profiles live in [`experiments/low_vram_vibed/configs/`](experiments/low_vram_vibed/configs/).
Status is part of the configuration and is validated by the test suite.

| Profile | Status | Configuration | What it establishes |
|---|---|---|---|
| `verified_512_900` | Verified | 512 env / WM 256 / Policy 512 / H=32 / 900 iterations | One short run completed within the guard and produced a finite checkpoint |
| `experimental_768_900` | Experimental | 768 / 384 / 768 / H=32 / 900 iterations | Reached iteration 570, then stopped after 76 KiB system Swap growth |
| `untested_1024_900` | Untested | 1024 / 512 / 1024 / H=32 / 900 iterations | No execution evidence |
| `untested_formal_512_14000` | Untested | 512 / 256 / 512 / H=32 / 14,000 iterations | Prior formal launch stopped at startup on Swap growth |
| `smoke_16_510` | Untested | 16 / 32 / 32 / H=32 / 510 iterations | Template only |

A profile launch is **not** a normal unguarded quick start. The wrapper requires an
effective cgroup with at most 4 GiB RAM and, for these profiles, `memory.swap.max=0`. The
following invocation is illustrative and has not been re-run as an end-to-end profile
launch during P2; the environment must be prepared first:

```bash
# Untested in this exact profile-wrapper form. Run only inside the documented cgroup.
env -u PYTHONPATH python scripts/vibed_run.py \
  --config verified_512_900 --run-name <unique-run-name>
```

Do not weaken the stop thresholds to make a run start. Do not run training, evaluation,
or rendering concurrently with the resource monitor.

## Reproduction Status

| Area | Current status |
|---|---|
| Track A CPU regression | Passing; CUDA/data tests are skipped on CPU-only machines |
| Track A short WM/BPTT runs | Executed; finite short runs retained |
| Track A long training | Not achieved; Actor feedback instability remains unresolved |
| Track B 512 short run | Completed; resource guard and finite checkpoint verified |
| Track B 768 short run | Partial; stopped at iteration 570 by the Swap guard |
| Track B 1024 and formal 14k | 1024 untested; formal launch stopped at startup |
| Full paper benchmark | Not revalidated in this workspace |
| RTX 5090 records | Historical records only; original artifacts are not retained here |

## Experimental Results

### RTX 5060 Ti 8GB — Track B short runs

| Run | Completed iterations | Outcome | GPU sample peak | Stop condition |
|---|---:|---|---:|---|
| 128 / 64 / 128, H=32, 14,000 | 14,000 | Finite training; normalized return 0.597475; 18/40 clips failed | Not retained in this summary | Completed, but materially below upstream quality |
| 256 / 128 / 256, H=32, 900 | 900 | Finite checkpoint; throughput comparison recorded | 3387 MiB | Completed |
| 512 / 256 / 512, H=32, 900 | 900 | Finite checkpoint; 297.10 s | 5412 MiB | Completed; no system Swap growth in the measured window |
| 768 / 384 / 768, H=32, 900 | 570 | Partial; checkpoint not verified | 6780 MiB | 76 KiB whole-system Swap growth |
| 1024 / 512 / 1024, H=32, 900 | 0 | Not run | — | Deliberately skipped |
| 512 formal, 14,000 | 0 | No formal result | 2200 MiB before stop | 23.816 MiB whole-system Swap growth after 6.1 s |

![Low-VRAM resource telemetry for the 512/256/512 short run](docs/assets/low_vram_512_900_resources.svg)

The chart is derived from retained local telemetry and shows resource behavior only. It
does not show tracking quality, convergence, or a formal benchmark.

### RTX 5090 — Historical author records

The following numbers appear in the historical experiment log, but their original logs
and checkpoints are not retained in this workspace. They must not be described as current,
independently revalidated, or RTX 5060 Ti results.

| Historical experiment | Setting | Reported result | Caveat |
|---|---|---|---|
| e2 | LAFAN1 40 clips, paper observation | Normalized return 0.56, 9/40 failed | Historical; not revalidated |
| e3 | Anchor-relative observation | 0.824 / 0.904, 5/40 / 3/40 failed | Different observation definition from the paper |
| e5 | BONES-SEED compact library | 0.934 / 0.935 on a 2,000-clip subset | Historical; BONES-SEED assets absent locally |
| e6/e7 | Multi-GPU / single-GPU records | Incomplete | Not current cross-hardware validation |

See [docs/REPRODUCTION.md](docs/REPRODUCTION.md) and
[docs/EXPERIMENTS.md](docs/EXPERIMENTS.md) for the evidence policy and detailed records.

## Known Limitations

- Stable long training has not been demonstrated.
- Actor feedback can grow after repeated updates even while losses remain finite; lower
  learning rate did not establish a fix.
- The formal 512 low-VRAM launch did not pass the zero-Swap startup gate.
- The 768 profile stopped before completing its short test; 1024 is untested.
- A clean source candidate skips 20 tests because CUDA, external upstream data/checkout,
  or both are unavailable; the exact count is environment-dependent.
- Historical RTX 5090 logs/checkpoints and BONES-SEED assets are absent.
- LAFAN1 G1 retargets are CC BY-NC-ND 4.0 and must not be redistributed with this code.
- Local robot videos, motion data, G1 assets, and checkpoints remain restricted; see
  [docs/DEMO_CATALOG.md](docs/DEMO_CATALOG.md).
- The indirect `torchrunx` dependency advertises GPL-3.0 metadata. It is not vendored;
  do not distribute a bundled virtual environment or binary package without legal review.

See [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) for workarounds and issue-reporting
guidance.

## Roadmap

- [ ] Reproduce the Track A Actor-feedback failure from retained diagnostics and test a
  clearly named experimental variant without changing the paper loss by default.
- [ ] Make the zero-Swap low-VRAM launch deterministic on the target host.
- [ ] Re-run the 512 short profile and 768 capacity probe when resources permit.
- [ ] Retain independently inspectable GPU evidence for a stable long run.
- [ ] Revalidate the benchmark protocol and publish only reproducible result tables.
- [ ] Complete dependency and asset license review before any tagged release.
- [ ] Add authorized demo media only after the user confirms rights to the underlying data.

## Original Authors and Acknowledgements

The original SuperMimic-Reproduced implementation and architecture were created in
CuboiLeo's upstream project and are attributed there to Yuxi Liu under MIT. The low-VRAM
track builds on `zita-ch/supermimic_vibed`, attributed there to ETH Zurich and Chong Zhang
under MIT.

The method is from the SuperMimic paper by Q. Liao, Y. Shao, J. Long, K. Zakka, R. Horowitz,
P. Abbeel, and K. Sreenath. This project also builds on mjlab, MuJoCo/MuJoCo Warp, Isaac
Lab, PyTorch, and their respective communities. It is not affiliated with or endorsed by
the paper authors, CuboiLeo, `zita-ch`, or mjlab's maintainers.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for attribution and license text.

## Citation

```bibtex
@inproceedings{liao2026supermimic,
  title     = {SuperMimic: Scaling Humanoid Whole-Body Control with One Differentiable World Model},
  author    = {Liao, Q. and Shao, Y. and Long, J. and Zakka, K. and Horowitz, R. and Abbeel, P. and Sreenath, K.},
  booktitle = {Conference on Robot Learning (CoRL)},
  year      = {2026},
  url       = {https://arxiv.org/abs/2610.28480}
}
```

## Licensing and Third-Party Assets

The root [MIT License](LICENSE) preserves the upstream
`Copyright (c) 2026 Yuxi Liu` notice and adds the project contributor notice; it does not
claim that all inherited code was authored by this derivative's maintainer. Files with an
mjlab correspondence retain the Apache-2.0 attribution and license copy under
[`third_party/mjlab/`](third_party/mjlab/). `supermimic_vibed` remains MIT and unvendored.

Motion data, robot assets, checkpoints, logs, upstream demo media, and bundled environments
are not covered by this repository's MIT license. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and
[docs/CONTRIBUTION_PROVENANCE.md](docs/CONTRIBUTION_PROVENANCE.md).
