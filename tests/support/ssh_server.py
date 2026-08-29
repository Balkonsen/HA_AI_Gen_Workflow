"""An in-process :mod:`asyncssh` server for exercising :class:`haco.ssh.SSHClient`.

The ``ssh_server`` fixture starts a real SSH server on ``127.0.0.1`` on an
ephemeral port. It accepts a connection when either:

* the client presents the public key generated at fixture setup, or
* the client presents the password :data:`GOOD_PASSWORD`.

Command execution is a tiny fixed dispatch (no real shell):

======================  ==================================
command                 result
======================  ==================================
``echo hi``             stdout ``hi``, exit 0
``false``               exit 1
anything else           stderr ``not found``, exit 127
======================  ==================================

An SFTP subsystem rooted at a per-fixture temp directory is also served, for
later phases that move files.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from pathlib import Path

import asyncssh
import pytest

GOOD_PASSWORD = "test-pw"

_DISPATCH: dict[str, tuple[str, str, int]] = {
    # command: (stdout, stderr, exit_status)
    "echo hi": ("hi\n", "", 0),
    "false": ("", "", 1),
}
_UNKNOWN = ("", "not found\n", 127)


@dataclass(frozen=True)
class SSHServerInfo:
    """Connection details for the running test server."""

    host: str
    port: int
    client_key_path: str
    good_password: str


class _TestSSHServer(asyncssh.SSHServer):
    """Accepts the known password; public keys are checked via authorized_client_keys."""

    def __init__(self, password: str) -> None:
        self._password = password

    def begin_auth(self, username: str) -> bool:
        return True

    def password_auth_supported(self) -> bool:
        return True

    def validate_password(self, username: str, password: str) -> bool:
        return password == self._password


class _ChrootSFTPServer(asyncssh.SFTPServer):
    def __init__(self, chan: asyncssh.SSHServerChannel[bytes], root: str) -> None:
        super().__init__(chan, chroot=root.encode())


async def _handle_process(process: asyncssh.SSHServerProcess[str]) -> None:
    command = process.command or ""
    stdout, stderr, status = _DISPATCH.get(command, _UNKNOWN)
    if stdout:
        process.stdout.write(stdout)
    if stderr:
        process.stderr.write(stderr)
    process.exit(status)


def _server_factory(password: str) -> Callable[[], asyncssh.SSHServer]:
    def factory() -> asyncssh.SSHServer:
        return _TestSSHServer(password)

    return factory


def _sftp_factory(root: str) -> Callable[[asyncssh.SSHServerChannel[bytes]], asyncssh.SFTPServer]:
    def factory(chan: asyncssh.SSHServerChannel[bytes]) -> asyncssh.SFTPServer:
        return _ChrootSFTPServer(chan, root)

    return factory


@pytest.fixture
async def ssh_server(tmp_path: Path) -> AsyncIterator[SSHServerInfo]:
    """Start an asyncssh server on an ephemeral port; stop it on teardown."""
    host_key = asyncssh.generate_private_key("ssh-ed25519")
    client_key = asyncssh.generate_private_key("ssh-ed25519")

    client_key_path = tmp_path / "client_key"
    client_key.write_private_key(str(client_key_path))
    client_key.write_public_key(str(tmp_path / "client_key.pub"))

    authorized_keys = tmp_path / "authorized_keys"
    authorized_keys.write_bytes(client_key.export_public_key())

    sftp_root = tmp_path / "sftp"
    sftp_root.mkdir()

    acceptor = await asyncssh.create_server(
        _server_factory(GOOD_PASSWORD),
        "127.0.0.1",
        0,
        server_host_keys=[host_key],
        authorized_client_keys=str(authorized_keys),
        process_factory=_handle_process,
        sftp_factory=_sftp_factory(str(sftp_root)),
    )
    try:
        yield SSHServerInfo(
            host="127.0.0.1",
            port=acceptor.get_port(),
            client_key_path=str(client_key_path),
            good_password=GOOD_PASSWORD,
        )
    finally:
        acceptor.close()
        await acceptor.wait_closed()
