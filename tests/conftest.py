"""Shared fixtures for the haco test suite."""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.support.ssh_server import ssh_server  # noqa: F401 - re-exported as a fixture

__all__ = ["ha_config_tree", "ssh_server", "tmp_config_home"]

_FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_config_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Repoint :func:`haco.profile.config_root` at an isolated tmp directory.

    Sets both ``XDG_CONFIG_HOME`` (POSIX) and ``APPDATA`` (Windows) so the test
    suite is platform-agnostic. Yields the ``haco`` subdirectory that
    ``config_root()`` will create and use.
    """
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path))
    yield tmp_path / "haco"


@pytest.fixture
def ha_config_tree(tmp_path: Path) -> Path:
    """Copy the representative HA config fixture tree into an isolated ``tmp_path``.

    Later plans' writer tests mutate the tree in place, so every test gets a
    throwaway copy rather than touching the committed fixture bytes. Returns the
    copy's root directory.
    """
    dest = tmp_path / "ha_config"
    shutil.copytree(_FIXTURES / "ha_config", dest)
    return dest
