"""Connection tests for :class:`haco.ssh.SSHClient` against the in-process server."""

from __future__ import annotations

from pathlib import Path

import asyncssh
import pytest

from haco.errors import AuthError, RemoteCommandError
from haco.models import HostProfile
from haco.ssh import SSHClient
from tests.support.ssh_server import SSHServerInfo


def _profile(server: SSHServerInfo, **overrides: object) -> HostProfile:
    data: dict[str, object] = {
        "name": "test",
        "host": server.host,
        "port": server.port,
        "user": "tester",
        "known_hosts": None,
    }
    data.update(overrides)
    return HostProfile.model_validate(data)


async def test_key_auth(ssh_server: SSHServerInfo) -> None:
    profile = _profile(ssh_server, auth="key", key_path=ssh_server.client_key_path)
    async with SSHClient(profile) as client:
        result = await client.run("echo hi")
    assert result.exit_status == 0
    assert result.stdout.strip() == "hi"


async def test_password_auth_env(ssh_server: SSHServerInfo, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HACO_SSH_PASSWORD", ssh_server.good_password)
    profile = _profile(ssh_server, auth="password")
    async with SSHClient(profile) as client:
        result = await client.run("echo hi")
    assert result.exit_status == 0


async def test_password_auth_provider(ssh_server: SSHServerInfo) -> None:
    profile = _profile(ssh_server, auth="password")
    client = SSHClient(profile, password_provider=lambda: ssh_server.good_password)
    await client.connect()
    try:
        result = await client.run("echo hi")
        assert result.exit_status == 0
    finally:
        await client.close()


async def test_bad_password(ssh_server: SSHServerInfo) -> None:
    profile = _profile(ssh_server, auth="password")
    client = SSHClient(profile, password_provider=lambda: "wrong-pw")
    with pytest.raises(AuthError):
        await client.connect()


async def test_bad_key(ssh_server: SSHServerInfo, tmp_path: Path) -> None:
    bad_key = asyncssh.generate_private_key("ssh-ed25519")
    bad_key_path = tmp_path / "bad_key"
    bad_key.write_private_key(str(bad_key_path))
    profile = _profile(ssh_server, auth="key", key_path=str(bad_key_path))
    client = SSHClient(profile)
    with pytest.raises(AuthError):
        await client.connect()


async def test_run_nonzero(ssh_server: SSHServerInfo) -> None:
    profile = _profile(ssh_server, auth="key", key_path=ssh_server.client_key_path)
    async with SSHClient(profile) as client:
        result = await client.run("false")
        assert result.exit_status == 1
        assert result.stdout == ""
        with pytest.raises(RemoteCommandError):
            await client.run("false", check=True)


def test_profile_never_holds_password() -> None:
    for forbidden in ("password", "secret", "token"):
        assert forbidden not in HostProfile.model_fields
