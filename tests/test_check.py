"""Baseline config-check parsing tests, driven by a scripted fake SSH client."""

from __future__ import annotations

from haco.check import run_config_check
from haco.discover import HostFacts
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


def _facts(install_type: str = "core", **overrides: object) -> HostFacts:
    data: dict[str, object] = {
        "install_type": install_type,
        "config_dir": "/config",
        "config_check_cmd": "check-cmd",
        "restart_cmd": "systemctl restart home-assistant@ha",
    }
    data.update(overrides)
    return HostFacts(**data)  # type: ignore[arg-type]


async def test_clean_check_is_ok() -> None:
    fake = FakeSSH(
        {
            "check-cmd": CmdResult(
                exit_status=0, stdout="Testing configuration at /config\nConfiguration valid!\n", stderr=""
            )
        }
    )
    result = await run_config_check(fake, _facts())
    assert result.ok is True
    assert result.errors == []
    assert result.warnings == []


async def test_error_line_makes_not_ok() -> None:
    out = "Failed config\n  General Errors:\n    - Integration 'foo' not found\nERROR: invalid config\n"
    fake = FakeSSH({"check-cmd": CmdResult(exit_status=1, stdout=out, stderr="")})
    result = await run_config_check(fake, _facts())
    assert result.ok is False
    assert result.errors  # non-empty
    assert any("foo" in e for e in result.errors)


async def test_nonzero_exit_without_error_token_still_not_ok() -> None:
    fake = FakeSSH({"check-cmd": CmdResult(exit_status=2, stdout="something went wrong\n", stderr="")})
    result = await run_config_check(fake, _facts())
    assert result.ok is False
    assert result.errors  # a line is synthesised so the caller has something to show


async def test_haos_path_bug_line_is_a_warning_not_an_error() -> None:
    bug = (
        "ERROR:homeassistant.config:Error loading /config/configuration.yaml: "
        "[Errno 2] No such file or directory: '/config/configuration.yaml'"
    )
    fake = FakeSSH({"check-cmd": CmdResult(exit_status=1, stdout=bug + "\n", stderr="")})
    result = await run_config_check(fake, _facts(install_type="haos"))
    assert result.errors == []
    assert any("156294" in w for w in result.warnings)
