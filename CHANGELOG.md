# Changelog

All notable changes are recorded here. The format follows Keep a Changelog, and versioning
will use semantic versioning after the first public release.

## [Unreleased]

### Added

- English GitHub-facing README, quick-start guide, architecture diagrams, reproduction
  guide, known-issues document, contribution guide, issue templates, and pull-request
  template.
- Read-only release audit with explicit PUBLIC/REVIEW file lists, secret/path scanning,
  restricted-extension checks, large-file checks, and an isolated candidate
  materialization dry run.
- Lightweight CPU GitHub Actions workflow for Ruff, pytest, and release hygiene.
- Real RTX 5060 Ti resource telemetry chart derived from the retained 512/256/512 short-run
  CSV.
- Expanded low-VRAM compatibility module with pinned provenance, profiles, guards,
  checkpoint checks, and CPU smoke tests.
- Dashboard resource histories for GPU VRAM, RAM, and Swap, including first threshold
  crossings and historical-run comparison from real `resources.csv` files.
- Demo provenance panel and catalog covering Track A/B, checkpoint iteration, data,
  model, run mode, real evaluation metrics, incomplete work, and media authorization.
- Checkpoint formatter detection for upstream weight-only `ckpt_*.pt` files and
  resumable `last.pt` files, with finite/structure checks and tests.
- Read-only 768 Swap Guard diagnosis documenting whole-host accounting, concurrent
  host-memory movement, current thresholds, and proposed attribution/debounce options.

### Changed

- The project is now explicitly identified as a community derivative of
  CuboiLeo/SuperMimic-Reproduced, with file-level provenance and upstream version recorded.
- The upstream Yuxi Liu MIT notice is preserved, and local contributor attribution is
  recorded separately in `LICENSE`.
- mjlab correspondence is documented in four source files and backed by a complete
  Apache-2.0 license and notice under `third_party/mjlab/`.
- Documentation now separates RTX 5090 historical records, RTX 5060 Ti 8GB evidence, and
  untested functionality.
- CI lint scope is limited to error-level Ruff and Pyflakes checks to avoid an unreviewed
  repository-wide formatting rewrite.
- Removed safe unused imports/variables reported by the lint gate; no learning objective,
  network architecture, or safety threshold was changed.
- Kept strict resource thresholds unchanged; 768 remains experimental and the proposed
  suppression policy requires explicit approval.

### Security

- Git ignores external checkouts, local backups, datasets, checkpoints, model artifacts,
  logs, virtual environments, credentials, and generated experiment outputs.
- Public-document privacy scan replaced local user/home details with portable placeholders.

## [0.1.0-alpha] - Candidate, not released

This version is a local release candidate only. It must not be pushed, tagged, or published
until the owner and license checks in `docs/RELEASE_CHECKLIST.md` are complete.
