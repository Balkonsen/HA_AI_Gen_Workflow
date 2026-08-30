"""Permission-preflight tests, driven by a scripted fake SSH client."""

from __future__ import annotations

from haco.discover import HostFacts
from haco.preflight import permission_preflight
from haco.ssh import CmdResult


class FakeSSH:
    """Scripted stand-in for :class:`haco.ssh.SSHClient` (``run`` only)."""

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


def _facts(**overrides: object) -> HostFacts:
    data: dict[str, object] = {
        "install_type": "core",
        "config_dir": "/config",
        "config_check_cmd": "check-cmd",
        "restart_cmd": "systemctl restart home-assistant@ha",
    }
    data.update(overrides)
    return HostFacts(**data)  # type: ignore[arg-type]


async def test_writable_dir_and_available_restart_bin_is_ok() -> None:
    fake = FakeSSH(
        {
            "test -w /config": _ok(),
            "touch /config/.haco_wtest": _ok(),
            "id -u": _ok("0"),  # root -> no sudo needed
            "command -v systemctl": _ok("/usr/bin/systemctl"),
        }
    )
    result = await permission_preflight(fake, _facts())
    assert result.ok is True
    assert result.can_write_config is True
    assert result.can_restart is True
    assert result.findings == []


async def test_non_writable_dir_names_the_dir() -> None:
    fake = FakeSSH(
        {
            "test -w /config": CmdResult(exit_status=1, stdout="", stderr=""),
            "id -u": _ok("0"),
            "command -v systemctl": _ok("/usr/bin/systemctl"),
        }
    )
    result = await permission_preflight(fake, _facts())
    assert result.ok is False
    assert result.can_write_config is False
    assert any("/config" in f for f in result.findings)


async def test_missing_sudo_for_root_restart_is_not_ok() -> None:
    fake = FakeSSH(
        {
            "test -w /config": _ok(),
            "touch /config/.haco_wtest": _ok(),
            "id -u": _ok("1000"),  # not root
            "command -v systemctl": _ok("/usr/bin/systemctl"),
            "sudo -n true": CmdResult(exit_status=1, stdout="", stderr=""),
        }
    )
    result = await permission_preflight(fake, _facts())
    assert result.ok is False
    assert result.can_restart is False
    assert any("sudo" in f for f in result.findings)
