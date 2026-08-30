"""Home Assistant install-type discovery over an SSH connection.

:func:`discover` runs a handful of read-only probe commands on the host to work
out which Home Assistant layout it is (``haos`` / ``container`` / ``core``),
then resolves the concrete config directory, config-check command, and restart
command from :data:`haco.hosttypes.DEFAULTS`. Every resolved field yields to the
matching :class:`~haco.models.HostProfile` override - an override is used
verbatim and, when all of them are set, discovery makes no SSH calls at all.
"""

from __future__ import annotations

import posixpath
import shlex
from collections.abc import Coroutine, Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol

from haco.errors import DiscoveryError
from haco.hosttypes import DEFAULTS, CmdContext, InstallType
from haco.models import HostProfile
from haco.ssh import CmdResult

_HA_NAME_HINTS = ("homeassistant", "home-assistant")
_HAOS_CHECK_CAVEAT = (
    "HAOS 'ha core check' had a config-path bug in 2025.11 (home-assistant/core#156294); "
    "if it reports a missing configuration.yaml that exists at the resolved config_dir, "
    "set the config_dir / config_check_cmd overrides rather than treating it as a failure."
)


class CommandRunner(Protocol):
    """The slice of :class:`haco.ssh.SSHClient` that discovery needs."""

    def run(self, cmd: str, *, check: bool = False) -> Coroutine[Any, Any, CmdResult]: ...


@dataclass(frozen=True)
class HostFacts:
    """Everything later phases need to talk to one Home Assistant install."""

    install_type: InstallType
    config_dir: str
    config_check_cmd: str
    restart_cmd: str
    container_name: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class _Detected:
    install_type: InstallType
    container_name: str | None = None
    venv_bin: str | None = None


def _match_ha_container(ps_output: str) -> str | None:
    """Return the first container name whose name or image looks like Home Assistant."""
    for raw in ps_output.splitlines():
        line = raw.strip()
        if not line:
            continue
        name = line.split()[0]
        if any(hint in line.lower() for hint in _HA_NAME_HINTS):
            return name
    return None


async def detect_type(client: CommandRunner) -> _Detected | None:
    """Probe the host and classify the Home Assistant install, or ``None``.

    Order: ``ha`` on PATH -> haos; else ``docker`` present with an HA container
    -> container; else ``hass`` resolvable -> core.
    """
    if (await client.run("command -v ha")).exit_status == 0:
        return _Detected("haos")

    if (await client.run("command -v docker")).exit_status == 0:
        ps = await client.run("docker ps --format '{{.Names}} {{.Image}}'")
        if ps.exit_status == 0:
            name = _match_ha_container(ps.stdout)
            if name is not None:
                return _Detected("container", container_name=name)

    hass = await client.run("command -v hass")
    hass_path = hass.stdout.strip()
    if hass.exit_status == 0 and hass_path:
        return _Detected("core", venv_bin=posixpath.dirname(hass_path))

    return None


async def resolve_config_dir(client: CommandRunner, candidates: Iterable[str]) -> str | None:
    """Return the first candidate that is a directory holding ``configuration.yaml``."""
    for candidate in candidates:
        quoted = shlex.quote(candidate)
        probe = f"test -d {quoted} && test -f {quoted}/configuration.yaml"
        if (await client.run(probe)).exit_status == 0:
            return candidate
    return None


async def _remote_home(client: CommandRunner) -> str:
    res = await client.run('printf %s "$HOME"')
    return res.stdout.strip() or "/root"


async def _remote_hass_bin(client: CommandRunner) -> str | None:
    res = await client.run("command -v hass")
    path = res.stdout.strip()
    if res.exit_status == 0 and path:
        return posixpath.dirname(path)
    return None


async def _container_config_bind(client: CommandRunner, container: str) -> str | None:
    """Return the host path bind-mounted at ``/config`` inside ``container``."""
    fmt = "{{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}"
    res = await client.run(f"docker inspect -f {shlex.quote(fmt)} {shlex.quote(container)}")
    if res.exit_status != 0:
        return None
    for pair in res.stdout.split():
        source, sep, dest = pair.rpartition(":")
        if sep and dest == "/config":
            return source
    return None


def _expand_home(candidate: str, home: str) -> str:
    if candidate == "$HOME":
        return home
    if candidate.startswith("$HOME/"):
        return posixpath.join(home, candidate[len("$HOME/") :])
    return candidate


async def _candidates_for_type(
    client: CommandRunner, itype: InstallType, container_name: str | None
) -> tuple[str, ...]:
    defaults = DEFAULTS[itype]
    if itype == "core":
        home = await _remote_home(client)
        return tuple(_expand_home(c, home) for c in defaults.config_dir_candidates)
    if itype == "container":
        assert container_name is not None
        bind = await _container_config_bind(client, container_name)
        if bind:
            return (bind, *defaults.config_dir_candidates)
        return defaults.config_dir_candidates
    return defaults.config_dir_candidates


async def discover(client: CommandRunner, profile: HostProfile) -> HostFacts:
    """Resolve :class:`HostFacts` for ``profile``, honoring every override.

    Raises :class:`~haco.errors.DiscoveryError` when the install type, the
    Home Assistant container, or the config directory cannot be determined and
    the profile does not supply it.
    """
    detected = await detect_type(client) if profile.install_type is None else None

    if profile.install_type is not None:
        itype: InstallType = profile.install_type
    elif detected is not None:
        itype = detected.install_type
    else:
        raise DiscoveryError("could not determine install type - set install_type in the profile")

    container_name: str | None = None
    if itype == "container":
        container_name = profile.container_name or (detected.container_name if detected else None)
        if container_name is None:
            raise DiscoveryError(
                "Docker is present but no Home Assistant container was found - set container_name in the profile"
            )

    if profile.config_dir:
        config_dir = profile.config_dir
    else:
        candidates = await _candidates_for_type(client, itype, container_name)
        found = await resolve_config_dir(client, candidates)
        if found is None:
            raise DiscoveryError(
                f"no config directory found for install_type={itype!r}; tried {list(candidates)} - "
                "set config_dir in the profile"
            )
        config_dir = found

    config_check_cmd = profile.config_check_cmd
    restart_cmd = profile.restart_cmd
    if config_check_cmd is None or restart_cmd is None:
        venv_bin = detected.venv_bin if detected else None
        if itype == "core" and venv_bin is None:
            venv_bin = await _remote_hass_bin(client)
        ctx = CmdContext(
            config_dir=config_dir,
            container_name=container_name,
            venv_bin=venv_bin,
            user=profile.user,
        )
        defaults = DEFAULTS[itype]
        if config_check_cmd is None:
            config_check_cmd = defaults.check_cmd(ctx)
        if restart_cmd is None:
            restart_cmd = defaults.restart_cmd(ctx)

    notes: list[str] = []
    if itype == "haos":
        notes.append(_HAOS_CHECK_CAVEAT)

    return HostFacts(
        install_type=itype,
        config_dir=config_dir,
        config_check_cmd=config_check_cmd,
        restart_cmd=restart_cmd,
        container_name=container_name,
        notes=notes,
    )
