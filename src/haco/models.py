"""The :class:`HostProfile` model.

By design this model has **no** ``password``, ``secret``, or ``token`` field.
SSH passwords are prompted for or read from ``HACO_SSH_PASSWORD`` at connect
time; private keys are referenced by path only, never by their bytes. A stored
profile therefore never contains secret material.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9_-]*$", min_length=1)]

InstallType = Literal["haos", "container", "core"]
AuthMode = Literal["key", "password"]


class HostProfile(BaseModel):
    """Connection settings for a single Home Assistant host."""

    model_config = ConfigDict(extra="forbid")

    name: Slug
    host: str
    port: int = 22
    user: str

    auth: AuthMode = "key"
    key_path: str | None = None
    """Filesystem path to a private key. Existence is checked at connect time, not here."""
    known_hosts: str | None = None
    """Path to a known_hosts file. ``None`` (the default) leaves asyncssh's own
    default in place: verify the host key against ``~/.ssh/known_hosts`` and the
    system files. It does NOT disable host-key checking."""

    install_type: InstallType | None = None
    """``None`` means autodetect at connect time."""
    container_name: str | None = None

    config_dir: str | None = None
    """Override for the discovered config directory; ``None`` discovers it."""
    config_check_cmd: str | None = None
    """Override for the per-type config-check command; ``None`` uses the default."""
    restart_cmd: str | None = None
    """Override for the per-type restart command; ``None`` uses the default."""

    staging_dir: str | None = None
    """Reserved for Phase 5 (host-side staging copy); accepted and stored now."""
