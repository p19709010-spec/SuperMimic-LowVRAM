# Reproduction and validation status

Updated: 2026-10-27 (P3 derivative provenance review). This document separates evidence by
implementation and hardware. It must not be read as a claim that the full paper has been
reproduced or that the inherited implementation is locally authored. Public navigation and
release boundaries are documented in
[`REPRODUCTION.md`](REPRODUCTION.md), [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md), and
[`PUBLISH_MANIFEST.md`](PUBLISH_MANIFEST.md).

## Evidence definitions

- **Verified here**: a retained artifact in this workspace supports the stated narrow claim.
- **Partial / experimental**: a run or diagnostic exists, but it stopped, is incomplete, or does not
  establish the intended end-to-end outcome.
- **Historical, not revalidated**: a number appears in a document, but its original log or checkpoint
  is not retained in this workspace.
- **Untested**: no execution evidence exists.

## Track A: CuboiLeo-derived mjlab implementation

| Area | Status | Evidence or limitation |
|---|---|---|
| LAFAN1 conversion and structural audit | Verified here | 40 clips, 441,140 frames at 50 Hz; `logs/local_20261025_data/audit.json` |
| G1 FK and analytic heads | Verified here | MuJoCo/analytic comparisons in tests and local logs |
| 16-environment reset/state playback | Verified here | `logs/local_20261025_sim16/` |
| World-model short training | Verified here | `logs/local_20261025_wm16b/` |
| H=8/16/32 short BPTT execution | Verified here for short runs only | parameter changes and finite outputs; not convergence |
| 500-step checkpoint | Verified here | finite weights/Adam state; no replay/RNG in checkpoint |
| 509-step continuous run | Failed | non-finite critic metrics and action/reward growth |
| Actor-feedback stability | Unresolved | protection triggered; lower learning rate did not establish a fix |
| Stable unattended long training | Not achieved | no qualifying run |

The main implementation is inherited from
`CuboiLeo/SuperMimic-Reproduced@d9be385` and is exercised by the project's CPU tests, with
CUDA-dependent tests skipped when no GPU is available. The low-VRAM adapter is separate.
See [`CONTRIBUTION_PROVENANCE.md`](CONTRIBUTION_PROVENANCE.md) for the file-level boundary.

## Track B: `supermimic_vibed` low-VRAM compatibility layer

| Run or check | Hardware | Result | Status |
|---|---|---|---|
| 128 env / WM 64 / Policy 128, 14,000 iterations | RTX 5060 Ti 8GB | Completed finite training; normalized return 0.597475, 18/40 failed | Completed, but materially below upstream-reported quality |
| 256 env / WM 128 / Policy 256, 900 iterations | RTX 5060 Ti 8GB | Completed; finite checkpoint; throughput comparison recorded | Short test verified |
| 512 env / WM 256 / Policy 512, 900 iterations | RTX 5060 Ti 8GB | Completed in 297.10 s; finite checkpoint; GPU sample peak 5412 MiB; no system Swap growth in window | Short test verified |
| 768 env / WM 384 / Policy 768 | RTX 5060 Ti 8GB | Stopped at iteration 570 after 76 KiB whole-system Swap growth | Partial; not checkpoint-verified |
| 1024 env / WM 512 / Policy 1024 | RTX 5060 Ti 8GB | Not run after the 768 resource gate failed | Untested |
| 512 env formal 14,000-iteration launch | RTX 5060 Ti 8GB | Stopped after about 6 s on 23.816 MiB whole-system Swap growth | No formal result |

The compatibility layer works only through an external, unmodified `supermimic_vibed` checkout at
commit `a1508d42c9d1699a52e8233ab16d08c488441ab9`. Its profiles and usage are documented in
[`experiments/low_vram_vibed/README.md`](../experiments/low_vram_vibed/README.md).

## Track C: RTX 5090 historical records

`docs/EXPERIMENTS.md` contains e1/e2/e3/e5/e6/e7/e8-era records from one or more RTX 5090 machines.
Those logs and checkpoints are not retained in the current workspace. In particular:

- The reported e3 anchor-observation score around 0.904 is a historical author record.
- The reported e5 BONES-SEED subset result is a historical author record.
- e6/e7 records are incomplete and are not current cross-hardware validation.
- BONES-SEED data and the compact library are absent from this workspace, so those results cannot be
  rerun or revalidated locally without a new authorized data setup.

No RTX 5090 historical number is presented as a result from the current RTX 5060 Ti machine.

## Current public claim

The defensible public claim is:

> This repository is a community derivative of CuboiLeo/SuperMimic-Reproduced. It adds
> numerical and engineering diagnostics plus a separate low-VRAM compatibility layer for an
> unmodified third-party implementation. Component and short-run checks pass, but stable long
> training and full end-to-end reproduction have not been demonstrated.

## Remaining blockers

1. No stable unattended training run.
2. No current, independently verifiable full paper benchmark on the documented hardware.
3. The Actor feedback instability remains unresolved for the Track A implementation.
4. The 512 formal low-VRAM profile did not pass the zero-Swap startup gate.
5. Historical 5090 artifacts and BONES-SEED data are not retained locally.
6. Dependency and data-license notices need a final release audit.

## Publication boundary

Publishable after review: the documented upstream-derived source, reviewed local contributions,
tests, profiles, and documentation without local paths or private run data.

Never publish: LAFAN1 CSV/NPZ files, BONES-SEED assets, Unitree meshes unless separately licensed,
checkpoints, replay buffers, logs, failure diagnostics, videos, upstream virtual environments, or the
`external/supermimic_vibed` checkout.
