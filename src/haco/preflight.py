"""Permission preflight over SSH (CONN-07).

Before ``haco connect`` reports a host ready, :func:`permission_preflight`
confirms the SSH user can actually do the two things a later apply needs:

* **write the config directory** - ``test -w`` plus a real ``touch`` / ``rm`` of a
  throwaway dotfile (``test -w`` alone lies on some overlay/bind mounts), and
* **run the restart command** - the restart binary is on ``PATH`` and, when it
  needs root and the SSH user is not root, passwordless ``sudo`` is available.

A missing grant is returned as data (``ok=False`` with a remediation string in
``findings``), never raised - the CLI decides the exit code.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field

from haco.discover import CommandRunner, HostFacts

# Restart binaries that generally need root to restart a system-level HA.
_ROOT_BINS = frozenset({"systemctl", "docker", "ha"})


@dataclass(frozen=True)
class PreflightResult:
    """Outcome of the write + restart permission checks."""

    ok: bool
    can_write_config: bool
    can_restart: bool
    findings: list[str] = field(default_factory=list)


async def _remote_is_root(client: CommandRunner) -> bool:
    res = await client.run("id -u")
    return res.exit_status == 0 and res.stdout.strip() == "0"


async def _check_write(client: CommandRunner, config_dir: str) -> tuple[bool, str | None]:
    quoted = shlex.quote(config_dir)
    if (await client.run(f"test -w {quoted}")).exit_status != 0:
        return False, f"SSH user needs write on {config_dir}"
    probe = f"touch {quoted}/.haco_wtest && rm {quoted}/.haco_wtest"
    if (await client.run(probe)).exit_status != 0:
        return False, f"SSH user needs write on {config_dir}"
    return True, None


async def _check_restart(client: CommandRunner, restart_cmd: str, is_root: bool) -> tuple[bool, str | None]:
    try:
        tokens = shlex.split(restart_cmd)
    except ValueError:
        tokens = restart_cmd.split()
    restart_bin = tokens[0] if tokens else ""
    if not restart_bin:
        return False, "no restart command resolved for this host"

    if (await client.run(f"command -v {shlex.quote(restart_bin)}")).exit_status != 0:
        return False, f"{restart_bin} not found on PATH"

    if restart_bin in _ROOT_BINS and not is_root:
        if (await client.run("sudo -n true")).exit_status != 0:
            return False, f"passwordless sudo required for {restart_cmd!r}"
    return True, None


async def permission_preflight(client: CommandRunner, facts: HostFacts) -> PreflightResult:
    """Probe write access to the config dir and the ability to run the restart command."""
    findings: list[str] = []

    can_write, write_finding = await _check_write(client, facts.config_dir)
    if write_finding:
        findings.append(write_finding)

    is_root = await _remote_is_root(client)
    can_restart, restart_finding = await _check_restart(client, facts.restart_cmd, is_root)
    if restart_finding:
        findings.append(restart_finding)

    return PreflightResult(
        ok=can_write and can_restart,
        can_write_config=can_write,
        can_restart=can_restart,
        findings=findings,
    )
