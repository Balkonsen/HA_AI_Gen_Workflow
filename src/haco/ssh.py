"""Async SSH wrapper around :mod:`asyncssh`.

:class:`SSHClient` opens one authenticated connection to a Home Assistant host
described by a :class:`~haco.models.HostProfile`, and exposes command execution
plus an SFTP handle for later phases (discovery, check, pull, apply).

Auth material is never taken from the profile file:

* ``auth="key"`` uses the private key referenced by ``profile.key_path``.
* ``auth="password"`` resolves the password from an explicit ``password_provider``
  callback, then ``$HACO_SSH_PASSWORD``, then an interactive ``getpass`` prompt
  when stdin is a TTY. If none are available it raises :class:`AuthError`.
"""

from __future__ import annotations

import getpass
import os
import sys
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Self

import asyncssh

from haco.errors import AuthError, ConnectionError, HostKeyError, RemoteCommandError
from haco.models import HostProfile

_STDERR_TAIL = 800


@dataclass(frozen=True)
class CmdResult:
    """Outcome of a single remote command."""

    exit_status: int
    stdout: str
    stderr: str


class SSHClient:
    """An authenticated async SSH session to one Home Assistant host."""

    def __init__(
        self,
        profile: HostProfile,
        *,
        password_provider: Callable[[], str] | None = None,
    ) -> None:
        self._profile = profile
        self._password_provider = password_provider
        self._conn: asyncssh.SSHClientConnection | None = None

    @property
    def profile(self) -> HostProfile:
        return self._profile

    def resolve_password(self) -> str:
        """Return the SSH password from provider, env, or an interactive prompt.

        Never reads the profile file. Raises :class:`AuthError` when no source
        is available (e.g. non-interactive run with ``$HACO_SSH_PASSWORD`` unset).
        """
        if self._password_provider is not None:
            return self._password_provider()
        env = os.environ.get("HACO_SSH_PASSWORD")
        if env is not None:
            return env
        if sys.stdin.isatty():
            return getpass.getpass(f"SSH password for {self._profile.user}@{self._profile.host}: ")
        raise AuthError("no password available (set HACO_SSH_PASSWORD)")

    async def connect(self) -> None:
        """Open the SSH connection, translating asyncssh failures to haco errors."""
        profile = self._profile
        options: dict[str, Any] = {
            "port": profile.port,
            "username": profile.user,
        }
        # Only override asyncssh's default when the profile names a file. Passing
        # ``known_hosts=None`` to asyncssh DISABLES host-key verification (MITM
        # risk); omitting the key lets it fall back to ~/.ssh/known_hosts + the
        # system files.
        if profile.known_hosts is not None:
            options["known_hosts"] = profile.known_hosts
        if profile.auth == "key":
            if not profile.key_path:
                raise AuthError("profile uses auth=key but no key_path is set")
            options["client_keys"] = [profile.key_path]
            options["password"] = None
        else:
            options["client_keys"] = None
            options["password"] = self.resolve_password()

        try:
            self._conn = await asyncssh.connect(profile.host, **options)
        except asyncssh.PermissionDenied as exc:
            raise AuthError(f"authentication failed for {profile.user}@{profile.host}") from exc
        except asyncssh.HostKeyNotVerifiable as exc:
            raise HostKeyError(f"host key for {profile.host} could not be verified") from exc
        except (OSError, asyncssh.Error) as exc:
            raise ConnectionError(f"could not connect to {profile.host}:{profile.port}: {exc}") from exc

    async def run(self, cmd: str, *, check: bool = False) -> CmdResult:
        """Run ``cmd`` on the host and return its exit status, stdout, and stderr.

        A non-existent remote command yields a non-zero ``exit_status`` rather
        than raising. When ``check`` is true a non-zero status raises
        :class:`RemoteCommandError`.
        """
        conn = self._require_conn()
        result = await conn.run(cmd, check=False)
        exit_status = result.exit_status if result.exit_status is not None else -1
        stdout = result.stdout if isinstance(result.stdout, str) else ""
        stderr = result.stderr if isinstance(result.stderr, str) else ""
        if check and exit_status != 0:
            tail = stderr.strip()[-_STDERR_TAIL:]
            raise RemoteCommandError(f"remote command failed (exit {exit_status}): {cmd}\n{tail}")
        return CmdResult(exit_status=exit_status, stdout=stdout, stderr=stderr)

    @asynccontextmanager
    async def sftp(self) -> AsyncIterator[asyncssh.SFTPClient]:
        """Yield an SFTP client bound to this connection (used by later phases)."""
        conn = self._require_conn()
        async with conn.start_sftp_client() as sftp_client:
            yield sftp_client

    async def close(self) -> None:
        """Close the connection if open. Safe to call more than once."""
        if self._conn is not None:
            self._conn.close()
            await self._conn.wait_closed()
            self._conn = None

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    def _require_conn(self) -> asyncssh.SSHClientConnection:
        if self._conn is None:
            raise ConnectionError("not connected; call connect() first")
        return self._conn
