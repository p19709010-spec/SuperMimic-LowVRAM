from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.release_audit import _restricted_reason

ROOT = Path(__file__).resolve().parents[1]


def _git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def test_repository_metadata_is_available():
    if not (ROOT / ".git").exists():
        pytest.skip("source tree has no Git metadata")
    assert _git("rev-parse", "--is-inside-work-tree").returncode == 0


def test_publish_restricted_directories_are_ignored():
    if not (ROOT / ".git").exists():
        pytest.skip("source tree has no Git metadata")
    for path in ("external", "data", "logs", ".local_backups"):
        completed = _git("check-ignore", "-q", "--no-index", f"{path}/probe")
        assert completed.returncode == 0, f"{path} must be ignored"


def test_no_tracked_file_is_now_ignored():
    if not (ROOT / ".git").exists():
        pytest.skip("source tree has no Git metadata")
    completed = _git("ls-files", "-ci", "--exclude-standard")
    assert completed.returncode == 0
    assert completed.stdout.strip() == ""


def test_no_model_or_data_artifacts_are_tracked():
    if not (ROOT / ".git").exists():
        pytest.skip("source tree has no Git metadata")
    completed = _git("ls-files", "*.pt", "*.pth", "*.ckpt", "*.npz", "*.npy", "*.safetensors")
    assert completed.returncode == 0
    assert completed.stdout.strip() == ""


def test_release_audit_distinguishes_source_packages_from_data_assets():
    assert _restricted_reason("src/supermimic/data/replay_buffer.py") is None
    assert _restricted_reason("scripts/data/build_library.py") is None
    assert _restricted_reason("data/motion.npz") == "restricted path"
    assert _restricted_reason("src/supermimic/data/motion.npz") == "restricted file type .npz"


def test_derivative_attribution_is_preserved():
    license_text = (ROOT / "LICENSE").read_text()
    readme = (ROOT / "README.md").read_text()
    notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text()

    assert "Copyright (c) 2026 Yuxi Liu" in license_text
    assert "SuperMimic-LowVRAM contributors" in license_text
    assert "CuboiLeo/SuperMimic-Reproduced" in readme
    assert "community-maintained derivative" in readme
    assert "zita-ch/supermimic_vibed" in readme
    assert (ROOT / "third_party/mjlab/LICENSE").is_file()
    assert "Apache License" in (ROOT / "third_party/mjlab/LICENSE").read_text()
    assert "torchrunx" in notices
