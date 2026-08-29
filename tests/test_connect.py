"""connect_and_probe orchestration tests.

``haco.connect.SSHClient`` is monkeypatched with an async-context-manager fake
that replays a scripted command map, so discovery + preflight + baseline check
run against one consistent host without a real server.
"""

from __future__ import annotations

import re

import pytest
from typer.testing import CliRunner

from haco import cli
from haco.check import CheckResult
from haco.cli import app
from haco.connect import ConnectReport, connect_and_probe
from haco.discover import HostFacts
from haco.errors import ConnectionError as HacoConnectionError
from haco.errors import DiscoveryError
from haco.models import HostProfile
from haco.preflight import PreflightResult
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


# --- CLI wiring -------------------------------------------------------------

_runner = CliRunner()


def _report(*, ready: bool) -> ConnectReport:
    facts = HostFacts(
        install_type="haos",
        config_dir="/homeassistant",
        config_check_cmd="ha core check",
        restart_cmd="ha core restart",
    )
    pf = PreflightResult(ok=ready, can_write_config=ready, can_restart=ready, findings=[])
    chk = CheckResult(ok=ready, exit_status=0 if ready else 1, errors=[] if ready else ["ERROR: boom"])
    return ConnectReport(facts=facts, preflight=pf, check=chk, ready=ready)


def _plain(text: str) -> str:
    """Strip ANSI escapes and collapse all whitespace so help text is searchable."""
    no_ansi = re.sub(r"\x1b\[[0-9;]*m", "", text)
    return re.sub(r"\s+", " ", no_ansi)


def test_connect_help_documents_name_and_password_stdin() -> None:
    result = _runner.invoke(app, ["connect", "--help"], env={"COLUMNS": "200"})
    assert result.exit_code == 0
    plain = _plain(result.output)
    assert "name" in plain.lower()
    assert "password-stdin" in plain


def test_connect_exits_zero_when_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "load_profile", lambda name: _profile())

    async def _fake(profile: HostProfile, *, password_provider: object = None) -> ConnectReport:
        return _report(ready=True)

    monkeypatch.setattr(cli, "connect_and_probe", _fake)
    result = _runner.invoke(app, ["connect", "hass"])
    assert result.exit_code == 0
    assert "READY" in result.output


def test_connect_exits_one_when_not_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "load_profile", lambda name: _profile())

    async def _fake(profile: HostProfile, *, password_provider: object = None) -> ConnectReport:
        return _report(ready=False)

    monkeypatch.setattr(cli, "connect_and_probe", _fake)
    result = _runner.invoke(app, ["connect", "hass"])
    assert result.exit_code == 1
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert "NOT READY" in result.output


def test_connect_exits_two_on_discovery_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "load_profile", lambda name: _profile())

    async def _fake(profile: HostProfile, *, password_provider: object = None) -> ConnectReport:
        raise DiscoveryError("could not determine install type")

    monkeypatch.setattr(cli, "connect_and_probe", _fake)
    result = _runner.invoke(app, ["connect", "hass"])
    assert result.exit_code == 2
    # exits cleanly - the DiscoveryError is turned into an exit code, not a traceback
    assert result.exception is None or isinstance(result.exception, SystemExit)
