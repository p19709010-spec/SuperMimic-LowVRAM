# Release Checklist

Use this checklist for the first source-only alpha. Checked items reflect P3-A.2 local
evidence; unchecked items require a separate private-staging/public-release authorization.

## Worktree and Ownership

- [x] Current branch, HEAD, tracked modifications, untracked files, ignored files, remotes,
  nested repositories, and large-file/LFS risks were inspected.
- [x] All 14 upstream-tracked modifications were reviewed and preserved.
- [x] A recovery backup exists and its checksum manifest passed.
- [x] The root `Copyright (c) 2026 Yuxi Liu` upstream MIT notice is preserved.
- [x] The project is identified as a derivative of CuboiLeo/SuperMimic-Reproduced.
- [x] LOCAL, derived, compatibility-layer, and REVIEW boundaries are documented per file.
- [ ] User approves the final regenerated `release/public_files.txt`.
- [ ] Owner decides whether any REVIEW file should be redacted and promoted later.
- [ ] A clean release commit/branch strategy is chosen manually; no automatic staging is used.

## Legal and Provenance

- [x] The pinned `supermimic_vibed` remote, commit, clean source state, and MIT notice were verified.
- [x] mjlab and Isaac Lab source pins and licenses were recorded.
- [x] The mjlab Apache-2.0 license and four correspondence notices are included.
- [x] `torchrunx==0.4.0` GPL-3.0 metadata was traced through mjlab and marked non-vendored.
- [x] Source-only release avoids conveying `torchrunx`, an environment, wheel set, or binary.
- [x] No bundled virtual environment or binary distribution is in the source candidate.
- [ ] Unitree, LAFAN1, BONES-SEED, and any upstream media terms are rechecked before adding assets.

## Data and Privacy

- [x] `external/`, datasets, checkpoints, logs, backups, and environments are Git-ignored.
- [x] No tracked file is currently ignored.
- [x] No tracked model/data artifact was found.
- [x] Public documentation has no local username, home path, token, or private key finding.
- [x] The release audit scans the PUBLIC file list without printing suspected secret values.
- [ ] Final scan is rerun immediately before staging the release commit.
- [ ] GitHub secret scanning, push protection, and dependency alerts are enabled after repository setup.

## File Manifest and Size

- [x] PUBLIC and REVIEW lists are disjoint and cover all nonignored files.
- [x] No PUBLIC file exceeds 5 MiB.
- [x] No LFS pointer or nested Git repository is present in the PUBLIC list.
- [x] A dry-run candidate is materialized outside the workspace.
- [ ] Final PUBLIC tree hash and file count are recorded for the exact release commit.
- [ ] Release archive contains only the approved PUBLIC list, never the whole dirty worktree.

## Documentation and Commands

- [x] English README separates Track A, Track B, historical results, current evidence, and untested work.
- [x] Quick start, reproduction status, known issues, architecture, contributing, changelog,
  issue templates, and PR template exist.
- [x] All commands shown in the README were checked against current CLI help or exercised locally.
- [ ] Any command marked Untested is either tested on the target machine or explicitly retained as alpha documentation.
- [ ] README links, Mermaid diagrams, and the SVG render correctly on GitHub.
- [ ] Citation metadata is checked against the paper record.

## Tests and CI

- [x] Candidate CPU pytest passes with explicit CUDA/data skips.
- [x] Ruff error/Pyflakes gate passes.
- [x] Low-VRAM no-GPU smoke passes with the pinned checkout.
- [x] Release audit passes.
- [ ] The new GitHub Actions workflow is green on GitHub.
- [ ] At least one authorized GPU/data regression is run before any performance claim.
- [ ] No formal training or high-resource stress test is launched solely for release preparation.

## Repository Settings

- [ ] Confirm the new repository name/description while leaving the CuboiLeo remote untouched.
- [ ] Confirm the repository starts private until the owner explicitly changes visibility.
- [ ] Enable branch protection for `main`.
- [ ] Enable secret scanning, Dependabot/security updates, and private vulnerability reporting.
- [ ] Add topics, but do not use badges or claims that imply paper-level reproduction.
- [ ] Confirm all required checks point to the committed `CI` workflow.

## Release Execution — Requires Separate Explicit Approval

- [ ] Manually review and stage the exact PUBLIC file list; never use `git add .`.
- [ ] Inspect `git diff --cached` for binary files, restricted assets, and accidental deletions.
- [ ] Configure the new account's Git identity and create the release commit after approval.
- [ ] Push only after separate explicit authorization.
- [ ] Create the GitHub Release/tag `v0.1.0-alpha` only after CI and manual review pass.
- [ ] Publish release notes using the exact limitations in the README.

## Stop Conditions

Stop and do not publish if any of the following occurs:

- unclassified nonignored file;
- suspected credential or private path finding;
- restricted dataset/model/log/checkpoint in the candidate;
- license or ownership uncertainty;
- manifest/content mismatch;
- failing test or CI;
- attempt to weaken a numerical/resource threshold;
- any request to bundle the external checkout or virtual environment.
