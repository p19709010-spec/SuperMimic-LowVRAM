# Publish Manifest

P3-A.2 updates the P2 publication boundary to identify this project as a derivative of
`CuboiLeo/SuperMimic-Reproduced@d9be385`. It does not authorize a push, tag, Release, or
upload.

The authoritative file-level lists are:

- **PUBLIC candidate:** [`release/public_files.txt`](../release/public_files.txt)
- **REVIEW, excluded from the first candidate:** [`release/review_files.txt`](../release/review_files.txt)

`scripts/release_audit.py` verifies that these two lists are disjoint and contain no
detected credentials, private home paths, personal email addresses, large files, or LFS
pointers. Source-workspace mode also requires every listed REVIEW file to be present and
classifies every nonignored file. PUBLIC-only candidates use `--candidate`, which requires
all PUBLIC files, rejects any present REVIEW file, and does not require the deliberately
excluded REVIEW payload. The PUBLIC list is what a future release may include after the
checklist is approved; it is not an instruction to stage or publish now.

## PUBLIC

These groups are proposed for the first source-only alpha after owner and license review:

- Root metadata and policy files: `LICENSE`, `.gitignore`, `.python-version`,
  `pyproject.toml`, `uv.lock`, `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, and
  `THIRD_PARTY_NOTICES.md`.
- Track A source under `src/supermimic/`, tests under `tests/`, and the general
  data/evaluation/render/benchmark scripts listed in `release/public_files.txt`. These
  include inherited upstream files, local modifications, and local additions distinguished
  in `docs/CONTRIBUTION_PROVENANCE.md`.
- Track B source under `experiments/low_vram_vibed/`, thin `scripts/vibed_*.py` wrappers,
  and the resource/status helpers under `monitoring/` required by that module.
- Public documentation: architecture, quick start, reproduction, status, known issues,
  paper specification, plan, review log, P1/P2 validation, dashboard and demo
  provenance, the 768 Swap Guard diagnosis, manifest, release checklist, contribution
  provenance, P3 derivative review, and the real-data SVG resource chart.
- GitHub automation and community templates under `.github/`.
- Release auditing files under `release/` and `scripts/release_audit.py`.
- The Apache-2.0 mjlab license and correspondence notice under `third_party/mjlab/`.

PUBLIC means the content is technically within the proposed source boundary and has no
known restricted asset or privacy leak. It does not mean every performance claim has been
validated. Alpha limitations remain in the README and known-issues document.

## REVIEW

REVIEW files are retained locally but excluded from the first public candidate until the
owner reviews their provenance, privacy, and evidence value:

- `docs/ACTOR_FEEDBACK_STABILITY.md`
- `docs/LOCAL_REPRODUCTION.md`
- `docs/OPEN_SOURCE_AUDIT.md`
- `docs/STABILITY_RECOVERY.md`
- `docs/VIBED_ETA_AND_256.md`
- `docs/VIBED_MIGRATION.md`
- `docs/VIBED_VRAM_SCALING.md`
- `scripts/actor_feedback_experiment.py`
- `scripts/actor_step_counterfactual.py`
- `scripts/checkpoint_memory_probe.py`
- `scripts/inspect_stability_failure.py`
- `scripts/local_dashboard_check.py`
- `scripts/local_plot.py`
- `scripts/local_render.py`
- `scripts/local_smoke.py`
- `scripts/local_stability.py`
- `scripts/local_validate_data.py`
- `scripts/monitored_train.py`
- `scripts/pull_and_eval.sh`

Reasons include detailed local run identifiers, machine-specific diagnostics, historical
workflow paths, or evidence that has not yet been independently reviewed for public use.
They may move to PUBLIC in a later version after redaction and owner approval.

## PRIVATE

The following must never enter the public candidate or a release archive:

- `external/`, including the pinned checkout and nested Isaac Lab Git repository.
- `data/`, including LAFAN1 CSV/NPZ files, BONES-SEED content, compact libraries, and
  robot assets.
- `logs/`, `checkpoints/`, replay buffers, failure diagnostics, TensorBoard events,
  generated videos, plots derived from restricted data, and benchmark artifacts.
- `.local_backups/`, local recovery archives, and Git state snapshots.
- `.venv/`, other virtual environments, caches, compiled bytecode, and build output.
- `.aws/`, `.agents/`, `.codex/`, `.ssh/`, `.env*`, private keys, certificates, and any
  credential-bearing file.
- Complete upstream demo media or any asset whose redistribution rights are unconfirmed.
- Local robot videos, motion trajectories, robot models, and generated screenshots.

These paths are covered by `.gitignore` and by the release audit's restricted checks.
`git add .` remains prohibited.

## GENERATED

The following are generated and must not be committed:

- `build/`, `dist/`, `*.egg-info/`, `__pycache__/`, `*.py[cod]`, `.pytest_cache/`,
  `.ruff_cache/`, and `.cache/`.
- `logs/`, `runs/`, `outputs/`, `experiments/**/outputs/`, TensorBoard files, resource
  CSVs, checkpoints, and rendered media.
- Temporary candidate materializations outside the workspace.

`uv.lock` is a generated dependency lock, but it is intentionally retained as PUBLIC source
metadata because it defines the tested dependency graph.

The SVG under `docs/assets/` is generated from retained telemetry but is intentionally
included as a reviewed documentation asset. Its provenance is documented in
`docs/ARCHITECTURE.md`.

## Modification and Contribution Review

The worktree contains 14 tracked files modified relative to
`d9be385b3eeb13a638fb33fb200d3bfd9be9839f`, including the six source/test changes that
predate P2. They have not been staged, committed, reverted, or silently discarded. The full
classification, including 54 unchanged upstream files and 62 local additions before the
P3-A.2 attribution patch, is in `docs/CONTRIBUTION_PROVENANCE.md`.

| File | Provenance | Restricted dependency / privacy | Current evidence | P2 disposition |
|---|---|---|---|---|
| `src/supermimic/data/replay_buffer.py` | Same repository author history; original engineering change | None found; no absolute paths/tokens | CPU termination-label test | PUBLIC as experimental source; no stability claim |
| `src/supermimic/eval/benchmark.py` | Same repository author history; original evaluation-accounting change | None found | CPU normalized-return/summary tests; CUDA integration skip | PUBLIC as experimental source; benchmark not claimed revalidated |
| `src/supermimic/imagination/policy_trainer.py` | Same repository author history; numerical guard and actor-step ordering changes | None found | CPU learning-rate/guard tests; full BPTT unavailable on CPU | PUBLIC as experimental source; instability remains documented |
| `src/supermimic/training/loop.py` | Same repository author history; fail-stop, checkpoint, and resume-warmup engineering changes | None found | Checkpoint and guard tests; GPU resume test skipped | PUBLIC as experimental source; long-run evidence absent |
| `src/supermimic/world_model/wm_trainer.py` | Same repository author history; fail-stop backward path | None found | Generic finite-gradient tests; no direct long WM run in P2 | PUBLIC as experimental source; no convergence claim |
| `tests/test_imagination.py` | Same repository author history; resume-update regression added | None found | Test exists but skips without CUDA + LAFAN1 | PUBLIC as a test; skip is explicit |

The Git history contains five upstream commits, all attributed to `Yuxi Liu`; the root
LICENSE preserves that upstream copyright and MIT terms. This repository is not that upstream
project and does not attribute inherited work to the new GitHub account.

## Third-Party and License Review

| Component | License / condition | Publication action |
|---|---|---|
| CuboiLeo-derived Track A | Root MIT, Copyright (c) 2026 Yuxi Liu | Preserve notice; local changes documented separately |
| Local project additions | Root MIT, contributor notice | Publish only reviewed PUBLIC additions |
| `zita-ch/supermimic_vibed` @ `a1508d4` | MIT, Copyright (c) 2026 ETH Zurich, Chong Zhang | Not vendored; metadata and license reproduced in notices |
| mjlab @ `8bb2bc9` | Apache-2.0, Copyright 2025 The mjlab Developers | Pinned dependency; license copy and file notices included |
| Isaac Lab | BSD-3-Clause | Separate external environment; not bundled |
| PyTorch, Warp, MuJoCo, MuJoCo Warp | Apache-2.0 / multi-license PyTorch distribution | Not bundled; retain dependency notices |
| `torchrunx==0.4.0` | GPL-3.0 metadata (declared by mjlab, not imported by this project) | Source candidate does not convey its code; no bundled environment/binary |
| Unitree G1 model/meshes | BSD-3-Clause per upstream attribution | Not present in public candidate |
| LAFAN1 G1 retargets | CC BY-NC-ND 4.0 | Not redistributed; only acquisition/conversion docs |
| BONES-SEED | Terms require independent verification | Not present; no redistribution |

No matching code block is being used as proof of originality. The current source-only
candidate may proceed to private staging after the checks in
`P3_DERIVATIVE_RELEASE_REVIEW.md`. Bundled environments, binaries, datasets, and checkpoints
remain outside scope.

## Publication Decision

The PUBLIC list is a **release candidate**, not a published release. Actual GitHub
publication remains blocked until `docs/RELEASE_CHECKLIST.md` is approved. The recommended
first label is `v0.1.0-alpha`, with the README's explicit limitations and without a stable
reproduction claim.
