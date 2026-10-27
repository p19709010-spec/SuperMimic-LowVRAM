from __future__ import annotations

import json

import pytest

from experiments.low_vram_vibed.config import (
    CONFIG_DIR,
    ProfileError,
    all_profiles,
    load_profile,
    load_upstream,
    validate_profile,
)
from experiments.low_vram_vibed.provenance import inspect_upstream


def test_profiles_validate_and_are_status_labelled():
    profiles = all_profiles()
    assert {profile["status"] for profile in profiles} <= {"verified", "experimental", "untested"}
    assert all(profile["horizon"] == 32 for profile in profiles)
    assert all(profile["upstream_source_modified"] is False for profile in profiles)
    assert len({profile["run_name"] for profile in profiles}) == len(profiles)


def test_verified_profile_is_only_a_short_test():
    verified = [profile for profile in all_profiles() if profile["status"] == "verified"]
    assert [profile["name"] for profile in verified] == ["verified_512_900"]
    assert verified[0]["scope"] == "short_test"
    assert verified[0]["evidence"]


def test_profile_rejects_changed_upstream_commit():
    profile = json.loads((CONFIG_DIR / "verified_512_900.json").read_text())
    profile["upstream_commit"] = "0" * 40
    with pytest.raises(ProfileError, match="upstream commit"):
        validate_profile(profile)


def test_profile_rejects_weakened_resource_guard():
    profile = load_profile("verified_512_900")
    profile["require_zero_swap"] = False
    with pytest.raises(ProfileError, match="require_zero_swap"):
        validate_profile(profile, load_upstream())


def test_local_upstream_provenance_when_checkout_exists():
    status = inspect_upstream()
    if not status["exists"]:
        pytest.skip("third-party checkout is not present")
    assert status["ready"], status.get("reason")
