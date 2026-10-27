# Contributing to SuperMimic-LowVRAM

This project is an alpha-stage, unofficial derivative of
`CuboiLeo/SuperMimic-Reproduced`. Contributions are welcome when they preserve the upstream
attribution, the separation between Track A and Track B, and make evidence easier to verify.

## Scope and Boundaries

- **Track A** changes belong under `src/supermimic/`, `tests/`, or Track A scripts/docs.
- **Track B** changes belong under `experiments/low_vram_vibed/` or thin `scripts/vibed_*`
  compatibility wrappers.
- Do not modify upstream `supermimic_vibed` source in place. If a change requires editing
  its training implementation, discuss a separate Fork and preserve its MIT history.
- Do not merge Track A and Track B metrics or claim that one validates the other.
- Do not weaken numerical or resource stop thresholds to make a test or run pass.
- Do not add datasets, checkpoints, replay buffers, model weights, logs, or private assets.

## Reporting Bugs

Use the GitHub issue templates. Include:

- implementation track and commit;
- Python, CUDA/driver, GPU, and OS versions;
- exact command and profile;
- expected and observed behavior;
- whether the failure is a guard stop, exception, incorrect metric, or documentation bug;
- sanitized excerpts only. Do not upload raw credentials, private paths, restricted data,
  checkpoints, or complete logs.

## Development Setup

```bash
uv sync --frozen --group dev
env -u PYTHONPATH CUDA_VISIBLE_DEVICES='' uv run pytest -q -rs
env -u PYTHONPATH uv run ruff check .
env -u PYTHONPATH uv run python scripts/release_audit.py
```

Tests that need CUDA or LAFAN1 data must remain explicitly skipped when prerequisites are
missing. A skip must not be converted into a pass without running the underlying case.

## Pull Requests

- Keep changes focused and describe which track they affect.
- Preserve the paper objective and defaults unless a separately named algorithm variant is
  proposed and reviewed.
- Add or update tests for behavior changes where feasible without restricted assets.
- Update status/evidence documents when changing a claim or profile status.
- Keep the public file classification consistent with `release/public_files.txt` and
  `release/review_files.txt`.
- Confirm that no local path, token, personal information, restricted artifact, nested Git
  repository, or large file enters the public candidate.
- Run the release audit before requesting review.

## License and Provenance

New contributions are accepted under the root MIT license. By submitting a contribution,
you confirm that you have the right to license it under those terms and that it does not
include unauthorized third-party code or assets. The original Yuxi Liu copyright notice is
preserved. Do not add an MIT header to third-party source or relicense upstream assets.
Third-party dependencies and data retain their own terms; see `THIRD_PARTY_NOTICES.md` and
`docs/CONTRIBUTION_PROVENANCE.md`.

## Security and Privacy

Do not open a public issue containing a live credential. Revoke the credential first, then
report only the affected file/rule and a sanitized summary. The release audit intentionally
prints rule names and locations without copying discovered secret values.
