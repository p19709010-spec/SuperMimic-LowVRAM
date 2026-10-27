# P3 Derivative Release Review

Date: 2026-10-27 (Europe/Berlin)
Scope: P3-A.1 provenance/license remediation and P3-A.2 candidate regeneration
Remote operations: none

## Decision

**READY FOR PRIVATE GITHUB STAGING: YES**

The source-only candidate can proceed to P3-B after the user explicitly authorizes private
staging and supplies/approves the new-account Git identity. This decision does not authorize
creating the remote repository, committing with an unconfirmed identity, pushing, changing
visibility, creating a Release, or publishing.

## 1. Persistent candidate preservation

The P3-A candidate was copied before provenance remediation from:

```text
/tmp/SuperMimic-LowVRAM-P3A-20261027
```

to:

```text
~/SuperMimic-LowVRAM-P3A-20261027
```

The original `/tmp` candidate remains in place. The initial copy contained 259 files and
2.7 MiB. A recursive directory comparison reported no differences. The normalized
path/content digest for both copies was:

```text
4ecece82cc6d9d8d1c52e68d98185b93feed23b57baf349546307ce2221c7c3d
```

The persistent path was subsequently regenerated for P3-A.2. No original CuboiLeo remote,
branch, HEAD, worktree, or backup was changed.

## 2. Upstream and local contribution boundary

The upstream baseline is:

| Field | Value |
|---|---|
| Repository | `https://github.com/CuboiLeo/SuperMimic-Reproduced` |
| Base commit | `d9be385b3eeb13a638fb33fb200d3bfd9be9839f` |
| Upstream files | 69 |
| Upstream commits | 5, recorded as authored by Yuxi Liu |
| Upstream license | MIT, Copyright (c) 2026 Yuxi Liu |

Before P3-A.2 attribution notices, the 130-file P3-A PUBLIC payload compared with the
upstream commit as follows:

| Category | Count |
|---|---:|
| Upstream file unchanged | 54 |
| Upstream file locally modified | 14 |
| Local PUBLIC file added | 62 |
| Upstream tracked file outside PUBLIC | 1 |

After the four required mjlab correspondence notices and four new provenance/license files,
the final 134-file PUBLIC payload is:

| Final category | Count |
|---|---:|
| Upstream-tracked file unchanged | 50 |
| Upstream-tracked file locally modified | 18 |
| Local file added | 66 |
| Upstream-tracked REVIEW file | 1 |

The 18 locally modified upstream files are listed in
[`CONTRIBUTION_PROVENANCE.md`](CONTRIBUTION_PROVENANCE.md), together with the 66 local
additions and all 19 REVIEW files.

### Inherited from CuboiLeo

The core Track A architecture and implementation are inherited from CuboiLeo:

- world model, policy, critic, BPTT/GAE imagination and training foundations;
- mjlab environment, FK, observations, rewards, terminations, actions, state I/O and
  motion library;
- distributed training, schedules, replay, evaluation and data tooling;
- upstream paper specification, reproduction plan, experiment history, and tests.

The candidate never attributes these inherited files wholesale to
`p19709010-spec`, to the current maintainer, or to a new initial repository.

### Verified local contributions

The actual local diff and added files support the following contribution categories:

- **Training safeguards:** fail-stop finite checks, diagnostic capture, atomic checkpoints,
  optimizer-state checks, actor/critic learning-rate correction, and resumed-run warmup.
- **Evaluation:** terminal-state accounting, full-reference normalization, tracking-error
  output, explicit reset handling, and regressions.
- **Low-VRAM wrapper:** profiles, cgroup/Swap/GPU guards, process lifecycle, checkpoint
  inspection, postprocessing, and pinned provenance checks around an unmodified
  `supermimic_vibed`.
- **Engineering/release:** resource telemetry, dashboard, release audit, CPU CI, issue/PR
  templates, architecture and reproduction docs, validation reports, provenance report, and
  measured resource chart.

These are local deltas, not a claim that all enclosing source files were locally authored.

## 3. MIT and upstream notice

The root `LICENSE` now contains both:

```text
Copyright (c) 2026 Yuxi Liu
Modifications copyright (c) 2026 SuperMimic-LowVRAM contributors
```

The upstream copyright is unchanged and remains first. The contributor line identifies local
work without replacing the original owner or claiming the entire inherited project.
The root MIT terms remain byte-compatible with the upstream grant.

`CONTRIBUTING.md`, `README.md`, `THIRD_PARTY_NOTICES.md`, and
`docs/CONTRIBUTION_PROVENANCE.md` all identify CuboiLeo/SuperMimic-Reproduced as the main
implementation's upstream. No new Git history was created; the candidate Git repository is
still an unborn `main` with no commit or remote.

## 4. `supermimic_vibed` compatibility layer

| Field | Value |
|---|---|
| Repository | `https://github.com/zita-ch/supermimic_vibed.git` |
| Commit | `a1508d42c9d1699a52e8233ab16d08c488441ab9` |
| License | MIT |
| Copyright | Copyright (c) 2026 ETH Zurich, Chong Zhang |
| Integration | wrapper only; external checkout is unmodified |

The upstream checkout is not copied into the candidate. Its remote, commit, clean tracked
state, and MIT copyright text were verified. Track B results remain separate from the
CuboiLeo-derived Track A implementation.

## 5. mjlab and the four correspondence files

The inherited files with explicit mjlab API or semantic correspondence are:

1. `src/supermimic/data/motion_convert.py`
2. `src/supermimic/envs/mdp/commands.py`
3. `src/supermimic/envs/mdp/rewards.py`
4. `src/supermimic/envs/tracking_env_cfg.py`

The review does not infer originality from similarity percentages. It records that those
files themselves state the mjlab correspondence and uses that documented relationship for
attribution.

Remediation:

- copied the complete Apache-2.0 text to `third_party/mjlab/LICENSE`;
- added `third_party/mjlab/NOTICE` with mjlab source, pinned revision, copyright, and all
  four file paths;
- added a prominent source-file notice to each of the four files;
- retained the CuboiLeo upstream lineage and did not add an MIT-only claim over mjlab code.

mjlab is pinned to `8bb2bc9e187797689ec82c78c35019afd2fd0376`, version 1.6.0, Apache-2.0,
Copyright 2025 The mjlab Developers. No upstream `mjlab` source checkout is included.

## 6. `torchrunx` release impact

`mjlab==1.6.0` declares `torchrunx>=0.3.4`; `uv.lock` resolves `torchrunx==0.4.0`, whose
package metadata advertises GPL-3.0. This project does not import `torchrunx`, copy its
source, or distribute a virtual environment, wheel set, or executable bundle containing it.

Conclusion: **not a blocker for the planned source-only GitHub repository**. It remains a
blocker for any future bundled environment, binary, image, or release archive that conveys
`torchrunx`; that separate distribution form would require copyleft compliance review.

## 7. PUBLIC manifest adjustment

The prior PUBLIC list had 130 files. P3-A.1/A.2 adds:

```text
docs/CONTRIBUTION_PROVENANCE.md
docs/P3_DERIVATIVE_RELEASE_REVIEW.md
third_party/mjlab/LICENSE
third_party/mjlab/NOTICE
```

The final PUBLIC count is **134**. No REVIEW file was promoted. The 19 REVIEW entries remain
excluded, including `scripts/pull_and_eval.sh`.

No `external/`, data, log, checkpoint, replay buffer, virtual environment, cache, backup,
private agent directory, or credential file is in the PUBLIC payload.

## 8. Candidate checks

All checks below ran against the isolated staging candidate, not as a replacement for the
original dirty-workspace result.

| Check | Result | Detail |
|---|---|---|
| Ruff | PASS | `All checks passed!` |
| CPU pytest | PASS | 35 passed, 20 skipped, 1 warning |
| Low-VRAM profile load | PASS | 5 profiles: verified/experimental/untested labels valid |
| CPU policy Smoke | PASS | finite `[2, 29]` output; no forbidden artifacts |
| Upstream provenance | PASS | pinned `zita-ch` commit and clean checkout |
| Upstream fetch plan | PASS | only pinned top-level checkout; no data/weights |
| README/attribution assertions | PASS | upstream, derivative, vibed, license checks |
| License files | PASS | root MIT and complete Apache-2.0 present |
| Markdown relative links | PASS | checked after final report insertion |
| YAML and SVG | PASS | 4 GitHub YAML files parse; SVG is valid XML |
| Release audit | PASS | exact PUBLIC-only mode after final report |
| Wheel/sdist build | PASS | source distributions contain only reviewed payload |
| Wheel install | PASS | `supermimic==0.1.0`, `sm-train` entry point |
| Full fresh CUDA environment sync | BLOCKED | offline cache lacks locked PyTorch wheel |
| GitHub Actions remote run | SKIP | repository not created or pushed in P3-A |
| GPU/data/training regression | SKIP | prohibited in this stage; no training started |

The clean candidate's 20 skips are:

- 11 tests requiring CUDA only;
- 4 tests requiring CUDA and LAFAN1 data;
- 4 motion tests requiring LAFAN1 CSV data;
- 1 profile-provenance test requiring the external `supermimic_vibed` checkout.

### P2 vs P3 test counts

P2's **39 passed / 15 skipped** was measured in the original workspace with restricted
LAFAN1 data and the external `supermimic_vibed` checkout available. Those passed results are
valid for that environment but are not substituted for the isolated candidate.

The pre-P3-A.2 isolated candidate had **34 passed / 20 skipped**: four LAFAN1-backed tests and
one external-checkout provenance test became explicit skips, while CPU-only cases still
passed. P3-A.2 adds one attribution regression test, producing **35 passed / 20 skipped**.
No skipped case is reported as passed.

## 9. Repository state and hash

Final persistent candidate path:

```text
~/SuperMimic-LowVRAM-P3A-20261027
```

The destructive source tree at `/tmp/SuperMimic-LowVRAM-P3A-20261027` remains preserved as
the pre-remediation candidate and historical audit location.

Because a document cannot contain its own final SHA-256, the stable content digest below
excludes only this report:

```text
files: 133
bytes: 970,683
path/content SHA-256: 59f8566cb78a72b9d1b7bdfb98a4147e50ae4b201b7762b1f200785bf00b0efb
```

The final 134-file release-audit tree digest including this report is reported in the P3-A
completion message after all files are synchronized and audited.

No local commit exists yet. The candidate repository is an unborn `main`, with no remote and
no tag. A P3-B commit must first record:

- upstream `CuboiLeo/SuperMimic-Reproduced@d9be385b3eeb13a638fb33fb200d3bfd9be9839f`;
- the reviewed derivative scope;
- the new account's confirmed Git author identity.

## 10. P3-B entry conditions

P3-A.2 is complete, so no source/license blocker remains for source-only private staging.
P3-B still requires:

1. user approval of the final 134-file PUBLIC list;
2. confirmation/configuration of the `p19709010-spec` Git identity;
3. explicit authorization to create `p19709010-spec/SuperMimic-LowVRAM` as a private
   repository;
4. explicit authorization for the exact local commit history and push.

Until those are provided, no remote repository, commit, push, tag, Release, or visibility
change may be performed.

**READY FOR PRIVATE GITHUB STAGING: YES**
