"""Tests for the HostProfile model and its local persistence."""

from __future__ import annotations

from pathlib import Path

import pytest

from haco.errors import ProfileNotFound
from haco.models import HostProfile
from haco.profile import list_profiles, load_profile, profile_path, save_profile


def _sample() -> HostProfile:
    return HostProfile(
        name="hass-lab",
        host="10.0.0.5",
        user="root",
        key_path="~/.ssh/id_ed25519",
        install_type="haos",
    )


def test_round_trip(tmp_config_home: Path) -> None:
    original = _sample()
    path = save_profile(original)
    assert path == profile_path("hass-lab")
    assert load_profile("hass-lab") == original


def test_missing_profile_raises(tmp_config_home: Path) -> None:
    with pytest.raises(ProfileNotFound):
        load_profile("nope")


def test_written_file_has_no_secret_text(tmp_config_home: Path) -> None:
    save_profile(_sample())
    text = profile_path("hass-lab").read_text(encoding="utf-8")
    assert "password" not in text
    assert "token" not in text
    assert "secret" not in text


def test_name_validation() -> None:
    with pytest.raises(ValueError):
        HostProfile(name="Bad Name", host="h", user="u")
    HostProfile(name="hass-lab", host="h", user="u")


def test_list_profiles(tmp_config_home: Path) -> None:
    assert list_profiles() == []
    save_profile(_sample())
    save_profile(HostProfile(name="other", host="h", user="u"))
    assert list_profiles() == ["hass-lab", "other"]
