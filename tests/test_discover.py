"""Discovery tests driven by a scripted fake SSH client.

:class:`FakeSSH` matches each command against a dict of prefixes and returns the
mapped :class:`~haco.ssh.CmdResult`; anything unmatched exits 1. That is enough
to reproduce every install layout without a real host.
"""

from __future__ import annotations

import pytest

from haco.discover import discover
from haco.errors import DiscoveryError
from haco.models import HostProfile
from haco.ssh import CmdResult


class FakeSSH:
    """A scripted stand-in for :class:`haco.ssh.SSHClient` (``run`` only)."""

    def __init__(self, script: dict[str, CmdResult]) -> None:
        self._script = script
        self.calls: list[str] = []

    async def run(self, cmd: str, *, check: bool = False) -> CmdResult:
        self.calls.append(cmd)
        for prefix in sorted(self._script, key=len, reverse=True):
            if cmd == prefix or cmd.startswith(prefix + " "):
                return self._script[prefix]
        return CmdResult(exit_status=1, stdout="", stderr="")


def _ok(stdout: str = "") -> CmdResult:
    return CmdResult(exit_status=0, stdout=stdout, stderr="")


def _profile(**overrides: object) -> HostProfile:
    data: dict[str, object] = {"name": "t", "host": "h", "user": "root"}
    data.update(overrides)
    return HostProfile.model_validate(data)


async def test_discover_haos() -> None:
    fake = FakeSSH(
        {
            "command -v ha": _ok("/usr/bin/ha"),
            "test -d /homeassistant": _ok(),
        }
    )
    facts = await discover(fake, _profile())
    assert facts.install_type == "haos"
    assert facts.config_dir == "/homeassistant"
    assert facts.config_check_cmd == "ha core check"
    assert facts.restart_cmd == "ha core restart"
    assert facts.notes  # HAOS 2025.11 check_config caveat


async def test_discover_container() -> None:
    fake = FakeSSH(
        {
            "command -v docker": _ok("/usr/bin/docker"),
            "docker ps --format": _ok("homeassistant ghcr.io/home-assistant/home-assistant:stable\n"),
            "docker inspect -f": _ok("/srv/ha/config:/config /srv/ha/media:/media "),
            "test -d /srv/ha/config": _ok(),
        }
    )
    facts = await discover(fake, _profile())
    assert facts.install_type == "container"
    assert facts.container_name == "homeassistant"
    assert facts.config_dir == "/srv/ha/config"
    assert facts.config_check_cmd == (
        "docker exec homeassistant python -m homeassistant --script check_config -c /config"
    )
    assert facts.restart_cmd == "docker restart homeassistant"


async def test_discover_core() -> None:
    fake = FakeSSH(
        {
            "command -v hass": _ok("/opt/ha/venv/bin/hass\n"),
            'printf %s "$HOME"': _ok("/home/ha"),
            "test -d /home/ha/.homeassistant": _ok(),
        }
    )
    facts = await discover(fake, _profile(user="ha"))
    assert facts.install_type == "core"
    assert facts.config_dir == "/home/ha/.homeassistant"
    assert "/opt/ha/venv/bin/hass --script check_config" in facts.config_check_cmd
    assert facts.restart_cmd == "systemctl restart home-assistant@ha"


async def test_discover_undetectable() -> None:
    fake = FakeSSH({})
    with pytest.raises(DiscoveryError) as excinfo:
        await discover(fake, _profile())
    assert "install type" in str(excinfo.value)


async def test_discover_profile_overrides_win() -> None:
    # FakeSSH would report haos, but every field is overridden in the profile.
    fake = FakeSSH(
        {
            "command -v ha": _ok("/usr/bin/ha"),
            "test -d /homeassistant": _ok(),
        }
    )
    profile = _profile(
        install_type="core",
        config_dir="/x",
        config_check_cmd="mycheck",
        restart_cmd="myrestart",
    )
    facts = await discover(fake, profile)
    assert facts.install_type == "core"
    assert facts.config_dir == "/x"
    assert facts.config_check_cmd == "mycheck"
    assert facts.restart_cmd == "myrestart"
    assert facts.container_name is None
    assert fake.calls == []  # overrides are used verbatim, host is never touched
