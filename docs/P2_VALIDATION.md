# P2 Open-Source Release Preparation Validation

> **Superseded provenance note (P3-A.1, 2026-10-27):** This file is retained as a
> historical validation record. Its P2 assumption that Track A was an independent
> from-scratch implementation is incorrect. CuboiLeo/SuperMimic-Reproduced is the upstream
> base project. See `CONTRIBUTION_PROVENANCE.md` and `P3_DERIVATIVE_RELEASE_REVIEW.md` for
> the authoritative attribution and release decision.

Date: 2026-10-27

Status: **local release candidate only**. No repository visibility change, stage, commit,
push, tag, GitHub Release, or public upload was performed.

## Scope and Safety Boundary

- Branch: `main`; HEAD: `d9be385b3eeb13a638fb33fb200d3bfd9be9839f`.
- Existing remote: `https://github.com/CuboiLeo/SuperMimic-Reproduced.git`, unchanged.
- The worktree remains intentionally dirty with P1, P2, and pre-P2 changes.
- No formal training or high-resource stress test was started.
- No Actor, Critic, World Model, reward, loss, network, or safety-threshold definition was
  changed.
- No `git add .`, `git reset --hard`, `git clean -fdx`, stage, commit, push, or Release was
  run.
- Restricted data, checkpoints, logs, environments, upstream checkouts, and backups were
  not copied into the public candidate.
- `external/supermimic_vibed` remains a clean checkout at
  `a1508d42c9d1699a52e8233ab16d08c488441ab9` with the expected `zita-ch` remote.
- `external/supermimic_vibed/IsaacLab` remains at
  `46d6cc3d7b115906fad12efd372fbf69f4e3d3ed`.

The P1 recovery backup at `.local_backups/p1_20261027T100621/` was rechecked with
`sha256sum -c SHA256SUMS`; all three listed artifacts passed. The backup remains ignored
and is not part of the release candidate.

## P2 Changes

### Added or Replaced

Supported by the workspace state and this validation record:

- `README.md`: English GitHub-facing page with separate Track A and Track B descriptions.
- `docs/ARCHITECTURE.md`: Mermaid diagrams for track separation, low-VRAM launch, and the
  fail-stop protection path.
- `docs/QUICKSTART.md`, `docs/REPRODUCTION.md`, `docs/KNOWN_ISSUES.md`,
  `docs/PUBLISH_MANIFEST.md`, and `docs/RELEASE_CHECKLIST.md`.
- `docs/assets/low_vram_512_900_resources.svg`: measured telemetry chart, not a synthetic
  or reconstructed curve.
- `CONTRIBUTING.md`, `CHANGELOG.md`, and `THIRD_PARTY_NOTICES.md`.
- `.github/workflows/ci.yml` and the issue/PR templates under `.github/`.
- `scripts/release_audit.py` and `scripts/plot_vibed_resources.py`.
- `release/public_files.txt` and `release/review_files.txt`.
- This file, `docs/P2_VALIDATION.md`.

### Updated

- `docs/REPRODUCTION_STATUS.md` and `docs/EXPERIMENTS.md`: historical/current evidence
  boundaries and the 512/768 short-run status.
- `pyproject.toml`: Ruff gate limited to `E9` and `F` rather than an unreviewed
  repository-wide formatting rewrite.
- `tests/test_repo_hygiene.py`: a regression test for public source directories versus
  restricted data assets.
- `scripts/release_audit.py`: corrected a false positive that classified the project's own
  `src/supermimic/data/` and `scripts/data/` code as restricted asset directories.
- `docs/QUICKSTART.md`: verified dashboard command uses `python -m monitoring.server` and
  the actual `--log-root` option.
- Safe lint cleanup removed unused imports or variables only in `monitoring/resources.py`,
  `scripts/actor_feedback_experiment.py`, `scripts/data/filter_bones_seed.py`,
  `scripts/local_render.py`, `scripts/local_stability.py`,
  `src/supermimic/data/motion_convert.py`, `src/supermimic/imagination/feedback.py`,
  `src/supermimic/policy/nets.py`, `src/supermimic/training/loop.py`, and
  `tests/test_analytic_heads.py`.

## P2-A Worktree and Provenance Audit

The nonignored inventory is fully classified by the release lists. Nested Git repositories
were found only under ignored `external/` and `logs/` paths. Git LFS is not installed and no
tracked or candidate file contains an LFS pointer. The largest nonignored file is
`uv.lock` at approximately 266 KiB; no candidate file exceeds 5 MiB.

The six pre-P2 source/test modifications were reviewed without reverting or staging them:

| File | Change | Evidence and publication boundary |
|---|---|---|
| `src/supermimic/data/replay_buffer.py` | Store `done` from the transition source row | CPU termination-label coverage; public as experimental source |
| `src/supermimic/eval/benchmark.py` | Terminal-state accounting and normalized-return denominator | CPU benchmark-accounting tests; CUDA/data integration skipped |
| `src/supermimic/imagination/policy_trainer.py` | Numerical guards and actor-step ordering | CPU guard/learning-rate tests; full BPTT not run here |
| `src/supermimic/training/loop.py` | Fail-stop, checkpoint, and resume-warmup handling | Checkpoint and guard tests; GPU resume test skipped |
| `src/supermimic/world_model/wm_trainer.py` | Finite backward-path guard | Generic numerical tests; no long world-model run in P2 |
| `tests/test_imagination.py` | Resume-update regression | Explicitly skips without CUDA and LAFAN1 data |

No restricted asset dependency, credential, private home path, or obvious copied block was
found in these changes. The evidence is sufficient for alpha source review, not for a
stability or convergence claim.

## P2-A License Review

| Component | Finding | Release consequence |
|---|---|---|
| Project source | Root MIT notice names Copyright (c) 2026 Yuxi Liu; all five existing commits are attributed to Yuxi Liu | Owner must explicitly confirm identity and the right to license all included project code |
| `supermimic_vibed` | MIT, Copyright (c) 2026 ETH Zurich, Chong Zhang; checkout is not vendored | Attribution reproduced in `THIRD_PARTY_NOTICES.md`; install by pinned upstream revision |
| mjlab | Apache-2.0, pinned to commit `8bb2bc9e187797689ec82c78c35019afd2fd0376` | Dependency only; retain its notices |
| Isaac Lab | BSD-3-Clause, pinned upstream checkout | Not bundled in the source candidate |
| `torchrunx` | Indirect mjlab dependency advertising GPL-3.0 metadata | Source-only candidate may proceed to owner review; bundled environment, binaries, or wheels are blocked pending legal review |
| LAFAN1 G1 retargets | CC BY-NC-ND 4.0 | Documentation only; no CSV, NPZ, or derived library is included |
| BONES-SEED | Independent terms not established here | No data or derived library is included |
| Unitree G1 assets | BSD-3-Clause per upstream attribution | No model or mesh asset is included |

Matching text alone is not treated as proof of originality. No new MIT header was added to
third-party or uncertain code. No severe license or data-leak blocker was found for a
source-only candidate, but owner confirmation and legal review of the locked dependency
graph remain release gates.

## Validation Commands and Results

All executable checks below were CPU-only unless noted. `PYTHONPATH` was unset to avoid
loading host ROS packages.

```bash
env -u PYTHONPATH UV_CACHE_DIR=/tmp/supermimic-uv uv run --no-sync ruff check .
```

Result: `All checks passed!`

```bash
env -u PYTHONPATH CUDA_VISIBLE_DEVICES='' \
  MPLCONFIGDIR=/tmp/supermimic-mpl UV_CACHE_DIR=/tmp/supermimic-uv \
  uv run --no-sync pytest -q -rs
```

Result: `39 passed, 15 skipped, 1 warning in 4.35s`. The skips are explicit CUDA or
CUDA-plus-LAFAN1 cases. A skip is not a pass for those paths.

```bash
env -u PYTHONPATH CUDA_VISIBLE_DEVICES='' \
  MPLCONFIGDIR=/tmp/supermimic-mpl UV_CACHE_DIR=/tmp/supermimic-uv \
  uv run --no-sync python experiments/low_vram_vibed/smoke.py --require-upstream
```

Result: five profiles validated; pinned commit, remote, and clean source state confirmed;
policy output shape `[2, 29]` and finite; no forbidden artifacts under `experiments/`.

```bash
env -u PYTHONPATH CUDA_VISIBLE_DEVICES='' UV_CACHE_DIR=/tmp/supermimic-uv \
  uv run --no-sync python experiments/low_vram_vibed/fetch_upstream.py --dry-run
```

Result: pinned checkout already present and clean.

```bash
git diff --check
git ls-files -ci --exclude-standard
```

Result: no whitespace errors; no tracked file is ignored.

CLI help was exercised for `experiments/low_vram_vibed/{run,finish,smoke}.py`,
`scripts/vibed_run.py`, `scripts/data/csv_to_npz_batch.py`,
`scripts/plot_vibed_resources.py`, and `supermimic.scripts.train`. The documented dashboard
help path was verified as `python -m monitoring.server --log-root ... --port ...`. A
three-second loopback bind could not be completed because the execution sandbox blocks
socket creation; this is an environment limitation, not a code-path success claim.

Static documentation checks passed: all relative Markdown links in PUBLIC files resolve,
the SVG parses as XML, and all four GitHub YAML documents parse successfully. GitHub-side
Mermaid rendering and the remote Actions run remain unverified until a repository push is
explicitly authorized.

## Manifest and Candidate Audit

The read-only audit command is:

```bash
env -u PYTHONPATH UV_CACHE_DIR=/tmp/supermimic-uv \
  uv run --no-sync python scripts/release_audit.py \
  --public-list release/public_files.txt \
  --review-list release/review_files.txt
```

The audit verifies list coverage and disjointness, restricted paths and suffixes, file
size, symlinks, LFS pointers, suspected credentials, private home paths, personal email
addresses, and the absence of `external/` from PUBLIC. Final counts and the tree digest are
emitted by the command on every run. They are intentionally not cached in this file
because this file is part of the payload being hashed, which would make an embedded digest
self-referential.

The candidate dry run uses:

```bash
env -u PYTHONPATH UV_CACHE_DIR=/tmp/supermimic-uv \
  uv run --no-sync python scripts/release_audit.py \
  --public-list release/public_files.txt \
  --review-list release/review_files.txt \
  --materialize /tmp/supermimic-release-candidate-p2-20261027
```

The destination must be new or empty and is outside the workspace. Materialization copies
only PUBLIC files; it does not stage Git content or modify the workspace.

## Publication Boundary

- **PUBLIC:** the exact source and documentation paths in `release/public_files.txt`, after
  owner confirmation and successful final audit/CI.
- **REVIEW:** the 19 evidence or machine-specific documents/scripts in
  `release/review_files.txt`; excluded from the first source candidate.
- **PRIVATE:** `external/`, `data/`, logs, checkpoints, replay buffers, failure
  diagnostics, local backups, virtual environments, secrets, private assets, and raw run
  telemetry.
- **GENERATED:** caches, build output, TensorBoard events, resource CSVs, rendered media,
  and temporary materializations.

## Known Residual Issues

1. Track A actor-feedback growth is unresolved; no stable long unattended run exists.
2. The formal 512 low-VRAM profile did not pass the zero-Swap startup gate; 768 stopped at
   iteration 570; 1024 is untested.
3. Fifteen CPU tests remain skipped because CUDA and/or LAFAN1 data are unavailable.
4. Historical RTX 5090 logs/checkpoints and BONES-SEED assets are not retained here.
5. The owner has not yet explicitly confirmed copyright ownership and every PUBLIC file.
6. The GPL-3.0 metadata on indirect `torchrunx` blocks bundled binary/environment
   distribution without legal review.
7. The GitHub Actions workflow has not run on GitHub, and Mermaid/GitHub rendering has not
   been visually verified.
8. Broader formatting and historical lint debt outside the `E9`/`F` gate remains
   intentionally untouched.
9. The worktree is still dirty and must be staged manually from the PUBLIC list, never with
   `git add .`.

## P3 and Release Recommendation

Do not enter P3 as part of this task. The current state supports a **source-only,
`v0.1.0-alpha` release candidate** after the owner confirms ownership, approves the PUBLIC
list, runs the final checklist, and obtains a green CI run. It does not support an
unqualified public release, a stable-reproduction claim, or a bundled binary/environment
release.
