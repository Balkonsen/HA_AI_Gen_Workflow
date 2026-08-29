"""connect_and_probe orchestration tests.

``haco.connect.SSHClient`` is monkeypatched with an async-context-manager fake
that replays a scripted command map, so discovery + preflight + baseline check
run against one consistent host without a real server.
"""

from __future__ import annotations

import pytest

from haco.connect import connect_and_probe
from haco.errors import ConnectionError as HacoConnectionError
from haco.models import HostProfile
from haco.ssh import CmdResult


def _ok(stdout: str = "") -> CmdResult:
    return CmdResult(exit_status=0, stdout=stdout, stderr="")


class FakeClient:
    """Async-context fake with the same ``run`` prefix-matching as the other suites."""

    def __init__(self, script: dict[str, CmdResult]) -> None:
        self._script = script
        self.calls: list[str] = []

    def __call__(self, profile: HostProfile, *, password_provider: object = None) -> FakeClient:
        # Used as the SSHClient(...) constructor replacement.
        return self

    async def __aenter__(self) -> FakeClient:
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False

    async def run(self, cmd: str, *, check: bool = False) -> CmdResult:
        self.calls.append(cmd)
        for prefix in sorted(self._script, key=len, reverse=True):
            if cmd == prefix or cmd.startswith(prefix + " "):
                return self._script[prefix]
        return CmdResult(exit_status=1, stdout="", stderr="")


class RaisingClient:
    def __call__(self, profile: HostProfile, *, password_provider: object = None) -> RaisingClient:
        return self

    async def __aenter__(self) -> RaisingClient:
        raise HacoConnectionError("could not connect to 10.0.0.9:22")

    async def __aexit__(self, *exc: object) -> bool:
        return False

    async def run(self, cmd: str, *, check: bool = False) -> CmdResult:  # pragma: no cover
        return CmdResult(exit_status=0, stdout="", stderr="")


def _profile() -> HostProfile:
    return HostProfile.model_validate({"name": "hass", "host": "10.0.0.9", "user": "root"})


def _healthy_haos_script() -> dict[str, CmdResult]:
    return {
        "command -v ha": _ok("/usr/bin/ha"),
        "test -d /homeassistant": _ok(),
        "test -w /homeassistant": _ok(),
        "touch /homeassistant/.haco_wtest": _ok(),
        "id -u": _ok("0"),
        "ha core check": _ok("Testing configuration at /homeassistant\nConfiguration valid!\n"),
    }


async def test_healthy_host_is_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeClient(_healthy_haos_script())
    monkeypatch.setattr("haco.connect.SSHClient", fake)
    report = await connect_and_probe(_profile())
    assert report.ready is True
    assert report.facts.install_type == "haos"
    assert report.preflight.ok is True
    assert report.check.ok is True


async def test_failing_preflight_is_not_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    script = _healthy_haos_script()
    script["test -w /homeassistant"] = CmdResult(exit_status=1, stdout="", stderr="")
    fake = FakeClient(script)
    monkeypatch.setattr("haco.connect.SSHClient", fake)
    report = await connect_and_probe(_profile())
    assert report.ready is False
    assert report.preflight.ok is False
    assert report.check.ok is True  # the report is still fully populated


async def test_failing_check_is_not_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    script = _healthy_haos_script()
    script["ha core check"] = CmdResult(exit_status=1, stdout="ERROR: invalid configuration\n", stderr="")
    fake = FakeClient(script)
    monkeypatch.setattr("haco.connect.SSHClient", fake)
    report = await connect_and_probe(_profile())
    assert report.ready is False
    assert report.preflight.ok is True
    assert report.check.ok is False
    assert report.check.errors


async def test_connection_error_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("haco.connect.SSHClient", RaisingClient())
    with pytest.raises(HacoConnectionError):
        await connect_and_probe(_profile())
