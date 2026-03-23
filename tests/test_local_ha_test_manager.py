"""Unit tests for tools/ha_local_test/manage_local_ha_test.py command wiring."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_manager_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "tools" / "ha_local_test" / "manage_local_ha_test.py"
    spec = importlib.util.spec_from_file_location("manage_local_ha_test", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cmd_health_invokes_health_script(monkeypatch):
    manager = _load_manager_module()
    captured = {}

    def fake_run(command, *, cwd=None):
        captured["command"] = command
        captured["cwd"] = cwd
        return 0

    monkeypatch.setattr(manager, "run_command", fake_run)

    rc = manager.cmd_health()

    assert rc == 0
    assert captured["command"][0] == manager.sys.executable
    assert captured["command"][1] == str(manager.HEALTH_CHECK)


def test_cmd_api_smoke_without_token(monkeypatch):
    manager = _load_manager_module()
    captured = {}

    def fake_run(command, *, cwd=None):
        captured["command"] = command
        captured["cwd"] = cwd
        return 0

    monkeypatch.setattr(manager, "run_command", fake_run)
    monkeypatch.delenv("HA_TEST_TOKEN", raising=False)

    rc = manager.cmd_api_smoke()

    assert rc == 0
    assert captured["command"] == [manager.sys.executable, str(manager.API_TOKEN_SMOKE)]


def test_cmd_api_smoke_with_token(monkeypatch):
    manager = _load_manager_module()
    captured = {}

    def fake_run(command, *, cwd=None):
        captured["command"] = command
        captured["cwd"] = cwd
        return 0

    monkeypatch.setattr(manager, "run_command", fake_run)
    monkeypatch.setenv("HA_TEST_TOKEN", "token-value")

    rc = manager.cmd_api_smoke()

    assert rc == 0
    assert captured["command"] == [
        manager.sys.executable,
        str(manager.API_TOKEN_SMOKE),
        "--token",
        "token-value",
    ]


def test_cmd_token_bootstrap_invokes_helper(monkeypatch):
    manager = _load_manager_module()
    captured = {}

    def fake_run(command, *, cwd=None):
        captured["command"] = command
        captured["cwd"] = cwd
        return 0

    monkeypatch.setattr(manager, "run_command", fake_run)

    rc = manager.cmd_token_bootstrap()

    assert rc == 0
    assert captured["command"] == [
        manager.sys.executable,
        str(manager.TOKEN_BOOTSTRAP),
        "--export-env",
    ]


def test_cmd_token_prune_invokes_helper(monkeypatch):
    manager = _load_manager_module()
    captured = {}

    def fake_run(command, *, cwd=None):
        captured["command"] = command
        captured["cwd"] = cwd
        return 0

    monkeypatch.setattr(manager, "run_command", fake_run)

    rc = manager.cmd_token_prune()

    assert rc == 0
    assert captured["command"] == [
        manager.sys.executable,
        str(manager.TOKEN_PRUNE),
        "--export-env",
    ]


def test_cmd_quality_gate_runs_expected_sequence(monkeypatch):
    manager = _load_manager_module()
    calls = []

    monkeypatch.setattr(manager, "cmd_status", lambda: calls.append("status") or 0)
    monkeypatch.setattr(manager, "cmd_health", lambda: calls.append("health") or 0)
    monkeypatch.setattr(manager, "cmd_dry_run", lambda: calls.append("dry-run") or 0)
    monkeypatch.setattr(
        manager, "cmd_api_smoke", lambda: calls.append("api-smoke") or 0
    )
    monkeypatch.setenv("HA_TEST_TOKEN", "token-value")

    rc = manager.cmd_quality_gate()

    assert rc == 0
    assert calls == ["status", "health", "dry-run", "api-smoke"]


def test_cmd_quality_gate_skips_api_smoke_without_token(monkeypatch):
    manager = _load_manager_module()
    calls = []

    monkeypatch.setattr(manager, "cmd_status", lambda: calls.append("status") or 0)
    monkeypatch.setattr(manager, "cmd_health", lambda: calls.append("health") or 0)
    monkeypatch.setattr(manager, "cmd_dry_run", lambda: calls.append("dry-run") or 0)
    monkeypatch.setattr(
        manager, "cmd_api_smoke", lambda: calls.append("api-smoke") or 0
    )
    monkeypatch.delenv("HA_TEST_TOKEN", raising=False)

    rc = manager.cmd_quality_gate()

    assert rc == 0
    assert calls == ["status", "health", "dry-run"]


def test_parse_args_supports_new_commands(monkeypatch):
    manager = _load_manager_module()

    monkeypatch.setattr(
        manager.sys, "argv", ["manage_local_ha_test.py", "token-bootstrap"]
    )
    args = manager.parse_args()
    assert args.command == "token-bootstrap"

    monkeypatch.setattr(manager.sys, "argv", ["manage_local_ha_test.py", "health"])
    args = manager.parse_args()
    assert args.command == "health"

    monkeypatch.setattr(manager.sys, "argv", ["manage_local_ha_test.py", "api-smoke"])
    args = manager.parse_args()
    assert args.command == "api-smoke"

    monkeypatch.setattr(manager.sys, "argv", ["manage_local_ha_test.py", "token-prune"])
    args = manager.parse_args()
    assert args.command == "token-prune"

    monkeypatch.setattr(
        manager.sys, "argv", ["manage_local_ha_test.py", "quality-gate"]
    )
    args = manager.parse_args()
    assert args.command == "quality-gate"
