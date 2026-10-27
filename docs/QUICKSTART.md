# Quick Start

This guide separates commands exercised by the current CPU regression from commands that
require CUDA, datasets, separate upstream environments, or explicit resource guards.

## 1. Environment

Requirements:

- Python 3.12.
- `uv` for dependency and environment management.
- Linux for the documented CUDA workflows.
- An NVIDIA GPU and compatible driver only for simulation, evaluation, rendering, or
  training. CPU tests skip those cases when no GPU is available.

```bash
git clone https://github.com/CuboiLeo/SuperMimic-Reproduced.git
cd SuperMimic-Reproduced
uv sync --frozen --group dev
```

If the shell exports a conflicting ROS `PYTHONPATH`, use `env -u PYTHONPATH` on the
commands below.

## 2. CPU Verification

The CPU suite is the minimum release gate:

```bash
env -u PYTHONPATH CUDA_VISIBLE_DEVICES='' uv run pytest -q -rs
```

Tests that require CUDA, LAFAN1 NPZ files, or both are skipped explicitly. A skip is not a
pass for those behaviors.

Run the release audit before preparing a candidate:

```bash
env -u PYTHONPATH uv run python scripts/release_audit.py \
  --public-list release/public_files.txt \
  --review-list release/review_files.txt
```

## 3. Pinned Low-VRAM Checkout

The compatibility layer expects an unmodified checkout at:

```text
external/supermimic_vibed/
```

Inspect the exact fetch commands without changing the filesystem:

```bash
env -u PYTHONPATH uv run --no-sync \
  python experiments/low_vram_vibed/fetch_upstream.py --dry-run
```

Fetch the pinned top-level checkout:

```bash
env -u PYTHONPATH uv run --no-sync \
  python experiments/low_vram_vibed/fetch_upstream.py
```

The helper fetches commit `a1508d42c9d1699a52e8233ab16d08c488441ab9` and refuses to
overwrite an existing directory. It does not fetch motion data, model weights, logs, a
virtual environment, or the nested Isaac Lab repository.

Verify provenance, all profiles, and a CPU policy forward pass without allocating GPU
memory:

```bash
env -u PYTHONPATH CUDA_VISIBLE_DEVICES='' \
  uv run --no-sync python experiments/low_vram_vibed/smoke.py --require-upstream
```

Expected properties are a clean pinned checkout, five validated profiles, a finite
`[2, 29]` policy output, and no model/data artifacts under `experiments/`.

## 4. Upstream and Data Setup

Track B's upstream implementation has its own Isaac Lab, Unitree G1, and motion-data
requirements. These are intentionally outside this repository:

- Follow the pinned upstream `supermimic_vibed` README at the exact commit above.
- Obtain LAFAN1 G1 retargets from the documented upstream source and comply with
  CC BY-NC-ND 4.0. Do not redistribute the CSV, NPZ, or derived motion libraries.
- Obtain Unitree G1 assets under their own license and preserve notices.
- Verify BONES-SEED terms independently before downloading or redistributing anything.

This project does not provide a fully tested turnkey upstream environment installer. Mark
that path **Untested** until run and recorded on the target machine.

## 5. Track A Data Conversion

Track A consumes local data under `data/`, which is ignored by Git. A LAFAN1-derived
conversion can be inspected with:

```bash
env -u PYTHONPATH uv run python scripts/data/csv_to_npz_batch.py --help
env -u PYTHONPATH uv run python scripts/data/csv_to_npz_batch.py \
  --input-dir data/raw/lafan1/g1 \
  --output-dir data/npz/lafan1 \
  --input-fps 30 --output-fps 50 --workers 4
```

These commands are documented from the current CLI, but a fresh public checkout does not
contain data and cannot reproduce a full Track A run by itself.

## 6. Low-VRAM Profiles

Profiles are JSON files under `experiments/low_vram_vibed/configs/`. Their status values
have strict meanings:

- `verified`: the narrow documented execution/resource/checkpoint claim was observed.
- `experimental`: a run exists but stopped or is incomplete.
- `untested`: no execution evidence exists.

The launcher requires an effective cgroup with at most 4 GiB memory and, for the supplied
profiles, `memory.swap.max=0`. It also checks GPU reserve and whole-system Swap growth.
It is not safe to run the launcher from an unrestricted login shell.

Illustrative invocation, **not re-run as an exact profile-wrapper test during P2**:

```bash
# Untested in this exact form. Prepare the resource boundary first.
env -u PYTHONPATH python scripts/vibed_run.py \
  --config verified_512_900 --run-name <unique-run-name>
```

Never weaken a guard to make a run start. A completed short test is not evidence of
tracking quality or convergence.

## 7. Viewing Results

The local dashboard can be started with:

```bash
env -u PYTHONPATH uv run --no-sync python -m monitoring.server \
  --log-root logs --port 7860
```

Open `http://127.0.0.1:7860`. The server binds loopback only and does not load model
weights. Dashboard availability does not imply that a run exists.

For low-VRAM runs, records are written under the external checkout's ignored
`logs/<run-name>/` directory. To create a documentation chart from a real resource CSV:

```bash
env -u PYTHONPATH uv run python scripts/plot_vibed_resources.py \
  <path-to-resources.csv> <output.svg> --title "<run description>"
```

Do not recreate missing curves from memory or screenshots.

## 8. Troubleshooting

- **`upstream virtual environment is missing`**: follow the pinned upstream installation;
  this repository does not copy its environment.
- **`run only inside an effective <=4 GiB cgroup`**: configure the documented cgroup
  boundary rather than disabling the check.
- **`zero-swap run requires effective memory.swap.max=0`**: the zero-Swap feature must be
  available on the host; do not reinterpret the guard as a suggestion.
- **CUDA/data tests skipped**: install the required hardware/assets separately and rerun
  without `CUDA_VISIBLE_DEVICES=''` only when the run is authorized.
- **ROS import errors**: use `env -u PYTHONPATH` as shown above.
