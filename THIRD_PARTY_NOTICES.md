# Third-Party Notices

This repository is an unofficial community derivative. It is not affiliated with or endorsed by
the authors of the SuperMimic paper, CuboiLeo, `zita-ch`, or the third-party projects listed below.

## Base project: `CuboiLeo/SuperMimic-Reproduced`

Track A is based on the public project:

- Repository: <https://github.com/CuboiLeo/SuperMimic-Reproduced>
- Base commit: `d9be385b3eeb13a638fb33fb200d3bfd9be9839f`
- Original license: MIT
- Copyright notice: Copyright (c) 2026 Yuxi Liu

The original MIT text and copyright line are preserved in the root [`LICENSE`](LICENSE). The
current worktree contains local modifications and additions that were not commits in the uploaded
base version. [`docs/CONTRIBUTION_PROVENANCE.md`](docs/CONTRIBUTION_PROVENANCE.md) records the
file-level comparison against the base commit. The derivative does not claim the inherited
architecture or implementation as its own.

## SuperMimic paper and method

Q. Liao, Y. Shao, J. Long, K. Zakka, R. Horowitz, P. Abbeel, K. Sreenath, *SuperMimic: Scaling
Humanoid Whole-Body Control with One Differentiable World Model*, CoRL 2026,
[arXiv:2610.28480](https://arxiv.org/abs/2610.28480).

The paper PDF and author code/model assets are not distributed in this repository.

## `zita-ch/supermimic_vibed`

The optional low-VRAM compatibility layer targets the unmodified third-party checkout:

- Repository: <https://github.com/zita-ch/supermimic_vibed>
- Pinned commit: `a1508d42c9d1699a52e8233ab16d08c488441ab9`
- Copyright: Copyright (c) 2026 ETH Zurich, Chong Zhang
- License: MIT

The checkout is not vendored in this repository. The MIT notice is reproduced here for attribution:

```text
MIT License

Copyright (c) 2026 ETH Zurich, Chong Zhang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Simulation and software dependencies

The main project pins these third-party dependencies; their own licenses remain in force:

- `mjlab`: Apache-2.0, Copyright 2025 The mjlab Developers, pinned to
  `8bb2bc9e187797689ec82c78c35019afd2fd0376`. The full Apache-2.0 text is included at
  [`third_party/mjlab/LICENSE`](third_party/mjlab/LICENSE), and the correspondence notice is at
  [`third_party/mjlab/NOTICE`](third_party/mjlab/NOTICE).
- Isaac Lab (optional low-VRAM upstream environment): BSD-3-Clause, pinned upstream to
  `46d6cc3d7b115906fad12efd372fbf69f4e3d3ed`.
- MuJoCo, MuJoCo Warp and Warp: Apache-2.0.
- PyTorch: combination of Apache-2.0, BSD, MIT and LLVM-exception components.
- NumPy, SciPy and pandas: BSD-family licenses.
- TensorBoard, pyarrow and huggingface-hub: Apache-2.0.
- tyro: MIT. tqdm: MPL-2.0 and MIT.
- `torchrunx==0.4.0` is an unconditional dependency declared by the pinned `mjlab`, and its package
  metadata advertises GPL-3.0. It is not imported by this repository, copied into the candidate, or
  included in a bundled environment, wheel, or binary release. The source-only candidate conveys
  only lock-file metadata and expects users to obtain dependencies separately. Do not distribute a
  bundled environment or binary artifact without a separate copyleft compliance review.

This summary is not a complete dependency-license audit. Regenerate and review it from the lock file
before a release.

## Robot and motion assets

- Unitree G1 description and meshes: the upstream `supermimic_vibed` README identifies the relevant
  assets as BSD-3-Clause. Preserve Unitree's notices when using or redistributing those assets.
- LAFAN1 motion captures and G1 retargets: CC BY-NC-ND 4.0 (Ubisoft La Forge). This repository does
  not redistribute the CSV, NPZ or derived motion libraries. Commercial use is not granted by the
  project's MIT license.
- BONES-SEED: download and redistribution terms must be verified independently before use or
  publication. No BONES-SEED data or derived library is distributed here.
- Upstream demonstration GIFs, videos, rendered images and checkpoints remain subject to their own
  provenance and are not automatically covered by this repository's MIT license.

## mjlab correspondence

The following inherited files explicitly reference or implement semantics corresponding to
`mjlab`'s Apache-2.0 licensed tracking APIs:

- `src/supermimic/data/motion_convert.py`
- `src/supermimic/envs/mdp/commands.py`
- `src/supermimic/envs/mdp/rewards.py`
- `src/supermimic/envs/tracking_env_cfg.py`

They are part of the CuboiLeo-derived Track A code, not vendored `mjlab` files. This derivative
retains mjlab's copyright/license attribution and adds prominent file-level notices. Any claims
about authorship of those files remain traceable to the upstream project and the local diff; no
new claim of independent creation is made.

## Project license and attribution policy

The root [`LICENSE`](LICENSE) preserves the upstream `Copyright (c) 2026 Yuxi Liu` notice and
records the local contributor notice. It applies to repository work to the extent permitted by the
contributors and does not override the Apache-2.0, BSD, GPL, data, or asset terms described above.

Track A is a derivative of CuboiLeo/SuperMimic-Reproduced. Track B is a separately maintained
compatibility layer over an unmodified `supermimic_vibed` checkout. The two upstream projects are
not described as having been written by this repository's maintainer.

## Release-only boundary

The public source candidate does not include `external/`, virtual environments, datasets,
checkpoints, logs, replay buffers, failure diagnostics, model exports, demos, or generated
media. In particular, no `torchrunx` source is vendored and no third-party environment is packaged.
Source-only distribution and dependency installation remain subject to the licenses of every
installed package.
