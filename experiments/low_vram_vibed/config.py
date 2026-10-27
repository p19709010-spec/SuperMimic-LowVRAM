"""Load and validate status-labelled low-VRAM experiment profiles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parents[1]
CONFIG_DIR = PACKAGE_DIR / "configs"
UPSTREAM_PATH = PACKAGE_DIR / "upstream.json"

STATUS_VALUES = frozenset({"verified", "experimental", "untested"})
REQUIRED_FIELDS = frozenset(
    {
        "name",
        "status",
        "scope",
        "upstream_commit",
        "run_name",
        "num_envs",
        "wm_batch",
        "pi_batch",
        "horizon",
        "iterations",
        "checkpoint_every",
        "max_seconds",
        "require_zero_swap",
        "resource_interval",
        "gpu_free_min_mib",
        "max_system_swap_growth_mib",
        "upstream_source_modified",
        "verified_on",
        "evidence",
        "limitations",
    }
)


class ProfileError(ValueError):
    """Raised when an experiment profile is incomplete or unsafe."""


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ProfileError(f"{path}: expected a JSON object")
    return value


def load_upstream(path: Path = UPSTREAM_PATH) -> dict[str, Any]:
    upstream = _read_json(path)
    for key in (
        "repository",
        "commit",
        "license",
        "copyright",
        "checkout",
        "isaaclab_repository",
        "isaaclab_commit",
        "integration",
    ):
        if not isinstance(upstream.get(key), str) or not upstream[key]:
            raise ProfileError(f"{path}: missing non-empty string {key!r}")
    if len(upstream["commit"]) != 40:
        raise ProfileError(f"{path}: upstream commit must be a full 40-character SHA")
    return upstream


def validate_profile(
    profile: dict[str, Any], upstream: dict[str, Any] | None = None
) -> dict[str, Any]:
    missing = sorted(REQUIRED_FIELDS.difference(profile))
    if missing:
        raise ProfileError(f"profile {profile.get('name', '<unknown>')!r} misses {missing}")
    if profile["status"] not in STATUS_VALUES:
        raise ProfileError(f"profile {profile['name']!r}: invalid status {profile['status']!r}")
    if profile["upstream_commit"] != (upstream or load_upstream())["commit"]:
        raise ProfileError(
            f"profile {profile['name']!r}: upstream commit does not match upstream.json"
        )
    if profile["upstream_source_modified"] is not False:
        raise ProfileError(
            f"profile {profile['name']!r}: source modification is not allowed in the wrapper layer"
        )
    if profile["horizon"] != 32:
        raise ProfileError(
            f"profile {profile['name']!r}: this compatibility layer preserves upstream H=32"
        )

    integer_fields = (
        "num_envs",
        "wm_batch",
        "pi_batch",
        "iterations",
        "checkpoint_every",
        "max_seconds",
    )
    for key in integer_fields:
        value = profile[key]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ProfileError(f"profile {profile['name']!r}: {key} must be a positive integer")
    if profile["checkpoint_every"] <= 0:
        raise ProfileError(f"profile {profile['name']!r}: checkpoint_every must be positive")

    if profile["require_zero_swap"] is not True:
        raise ProfileError(f"profile {profile['name']!r}: require_zero_swap must stay enabled")
    if profile["gpu_free_min_mib"] < 512:
        raise ProfileError(f"profile {profile['name']!r}: GPU reserve must be at least 512 MiB")
    if profile["max_system_swap_growth_mib"] < 0:
        raise ProfileError(
            f"profile {profile['name']!r}: Swap growth allowance must be nonnegative"
        )
    if not 0.5 <= profile["resource_interval"] <= 30:
        raise ProfileError(f"profile {profile['name']!r}: resource interval must be 0.5-30 seconds")
    if not isinstance(profile["evidence"], list) or not all(
        isinstance(item, str) for item in profile["evidence"]
    ):
        raise ProfileError(f"profile {profile['name']!r}: evidence must be a list of paths")
    if profile["status"] != "verified" and profile["verified_on"] is not None:
        raise ProfileError(
            f"profile {profile['name']!r}: only verified profiles may set verified_on"
        )
    if profile["status"] == "verified" and (not profile["verified_on"] or not profile["evidence"]):
        raise ProfileError(
            f"profile {profile['name']!r}: verified profiles need a date and evidence"
        )
    return profile


def load_profile(path_or_name: str | Path) -> dict[str, Any]:
    candidate = Path(path_or_name)
    if candidate.suffix != ".json" or not candidate.is_absolute():
        named = CONFIG_DIR / (
            candidate.name if candidate.suffix == ".json" else f"{candidate.name}.json"
        )
        candidate = named
    profile = _read_json(candidate)
    return validate_profile(profile)


def all_profiles() -> list[dict[str, Any]]:
    upstream = load_upstream()
    profiles = [
        validate_profile(_read_json(path), upstream) for path in sorted(CONFIG_DIR.glob("*.json"))
    ]
    names = [profile["name"] for profile in profiles]
    if len(names) != len(set(names)):
        raise ProfileError("duplicate low-VRAM profile names")
    return profiles
