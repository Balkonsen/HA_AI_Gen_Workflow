"""Shared fixtures for the haco test suite."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest


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
