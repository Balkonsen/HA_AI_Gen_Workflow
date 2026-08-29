"""Local, secret-free persistence for :class:`HostProfile`.

Profiles are stored one-per-file as TOML under the user config directory
(``$XDG_CONFIG_HOME/haco`` or ``~/.config/haco`` on POSIX, ``%APPDATA%\\haco``
on Windows). The written file only ever contains the fields of
:class:`HostProfile`, which by design carries no secret material.
"""

from __future__ import annotations

import os
import sys
import tomllib
from pathlib import Path
from typing import Any

import tomli_w

from haco.errors import ProfileError, ProfileNotFound
from haco.models import HostProfile

_FORBIDDEN_KEYS = frozenset({"password", "token", "secret"})


def config_root() -> Path:
    """Return the haco config directory, creating it if needed.

    POSIX honours ``$XDG_CONFIG_HOME`` (falling back to ``~/.config``); Windows
    uses ``%APPDATA%``. The directory is created with mode ``0o700`` on POSIX.
    """
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        root = Path(base) if base else Path.home() / "AppData" / "Roaming"
    else:
        base = os.environ.get("XDG_CONFIG_HOME")
        root = Path(base) if base else Path.home() / ".config"

    path = root / "haco"
    path.mkdir(parents=True, exist_ok=True)
    if os.name == "posix":
        path.chmod(0o700)
    return path


def profile_path(name: str) -> Path:
    """Return the on-disk path for the profile called ``name``."""
    return config_root() / f"{name}.toml"


def save_profile(profile: HostProfile) -> Path:
    """Write ``profile`` to disk atomically and return its path."""
    data: dict[str, Any] = profile.model_dump(exclude_none=True)

    leaked = _FORBIDDEN_KEYS.intersection(data)
    if leaked:
        raise ProfileError(f"refusing to write profile: forbidden key(s) {sorted(leaked)}")

    path = profile_path(profile.name)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as fh:
        tomli_w.dump(data, fh)
    os.replace(tmp, path)
    if os.name == "posix":
        path.chmod(0o600)
    return path


def load_profile(name: str) -> HostProfile:
    """Load and validate the profile called ``name``.

    Raises :class:`ProfileNotFound` when no such file exists.
    """
    path = profile_path(name)
    try:
        with open(path, "rb") as fh:
            data = tomllib.load(fh)
    except FileNotFoundError as exc:
        raise ProfileNotFound(name) from exc
    return HostProfile(**data)


def list_profiles() -> list[str]:
    """Return the sorted names of every stored profile."""
    return sorted(p.stem for p in config_root().glob("*.toml"))
