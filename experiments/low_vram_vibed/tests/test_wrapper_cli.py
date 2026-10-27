from __future__ import annotations

import pytest

from experiments.low_vram_vibed.run import _apply_profile, build_parser


def test_verified_profile_is_applied_without_override():
    parser = build_parser()
    args = parser.parse_args(["--config", "verified_512_900"])
    profile = _apply_profile(parser, args)
    assert profile is not None
    assert profile["status"] == "verified"
    assert args.num_envs == 512
    assert args.horizon == 32
    assert args.run_name == "lowvram_512_900"


def test_untested_profile_requires_explicit_acknowledgement():
    parser = build_parser()
    args = parser.parse_args(["--config", "untested_1024_900"])
    with pytest.raises(SystemExit):
        _apply_profile(parser, args)
