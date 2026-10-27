# Known Issues

## Training and Algorithm

### Actor feedback can become unstable

The CuboiLeo-derived Track A implementation can show growing action feedback after repeated actor
updates even while loss and gradient values remain finite. A lower learning rate delayed
but did not remove the growth. The failure path now preserves diagnostics and stops before
unsafe optimizer steps.

Do not present this as fixed. A future algorithm variant must be named separately and
compared with the paper objective; do not silently change the default loss or thresholds.

### No stable long unattended run

Short WM/BPTT runs have completed, but there is no qualifying stable long run. Absence of a
crash in a short run is not convergence evidence.

### Full paper benchmark is not revalidated

Historical RTX 5090 records lack retained logs/checkpoints in this workspace. Current
metrics must be rerun from an authorized environment before being compared with the paper.

## Low-VRAM Compatibility Layer

### The 512 formal profile stops at startup on Swap growth

The zero-Swap guard observed 23.816 MiB of whole-system Swap growth after about 6.1 s and
terminated the formal launch. The guard is intentionally strict and includes activity from
other processes on the host. Do not weaken it merely to start training.

### The 768 profile is incomplete

The short run reached iteration 570 and stopped after 76 KiB of whole-system Swap growth.
Its final checkpoint was not verified. This is not a completed 900-iteration result.

### The 1024 profile is untested

Capacity was not increased after the 768 guard failure.

### Profile-wrapper invocation needs explicit resource preparation

The launcher refuses to run without an effective cgroup and the configured Swap/GPU
reserves. A plain terminal invocation is expected to fail closed. The exact wrapper/profile
launch was not re-executed during P2.

## Platform and Dependencies

### CUDA/data tests are skipped on CPU-only systems

The CPU regression cannot validate simulation, GPU numerics, or real-data integration.
CI runs the CPU-safe subset only.

### `torchrunx` has GPL-3.0 metadata

`torchrunx` is an indirect dependency of mjlab. It is not vendored in this repository.
Do not publish a bundled virtual environment or binary distribution without legal review.

### `uv.lock` pins a CUDA-oriented PyTorch source on Linux

The lock file and package indexes are tied to the development environment. Reproducing on a
different driver or CPU-only installation may require a reviewed environment change.

### Track B depends on an external environment

Isaac Lab and upstream dependencies are not vendored. The public repository cannot provide a
one-command Track B install until that environment is independently tested and documented.

## Data and Assets

- LAFAN1 G1 retargets are CC BY-NC-ND 4.0 and are not redistributed here.
- BONES-SEED and Unitree assets must be obtained through their own channels and terms.
- No checkpoint, replay buffer, training log, failure diagnostic, or demo video is included.

## Reporting

Use the issue templates in `.github/ISSUE_TEMPLATE/`. Include the implementation track,
commit, hardware, exact command, expected/actual behavior, and a sanitized summary of the
guard or exception. Never attach restricted datasets, model weights, raw credentials, or
private host paths.
