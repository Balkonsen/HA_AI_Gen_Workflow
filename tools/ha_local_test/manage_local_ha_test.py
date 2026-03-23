#!/usr/bin/env python3
"""Manage a local Home Assistant sandbox for dry-run workflow testing."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
TEST_DIR = ROOT / "tools" / "ha_local_test"
COMPOSE_FILE = TEST_DIR / "docker-compose.ha-local.yml"
HA_CONFIG_DIR = TEST_DIR / "ha_config"
EXPORTS_DIR = ROOT / "exports"
DRY_RUN_TARGET = ROOT / "imports" / "dry_run_target"
ORCHESTRATOR = ROOT / "bin" / "workflow_orchestrator.py"
HEALTH_CHECK = TEST_DIR / "health_check.py"
API_TOKEN_SMOKE = TEST_DIR / "api_token_smoke.py"
TOKEN_BOOTSTRAP = TEST_DIR / "token_bootstrap.py"
TOKEN_PRUNE = TEST_DIR / "token_prune.py"


def run_command(command: list[str], *, cwd: Path | None = None) -> int:
    """Run a command and stream output."""
    process = subprocess.run(command, cwd=str(cwd or ROOT), check=False)
    return process.returncode


def compose_command(*extra_args: str) -> list[str]:
    """Build a docker compose command for the local HA sandbox."""
    return [
        "docker",
        "compose",
        "-f",
        str(COMPOSE_FILE),
        *extra_args,
    ]


def ensure_paths() -> None:
    """Ensure basic directories exist before running commands."""
    HA_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DRY_RUN_TARGET.mkdir(parents=True, exist_ok=True)


def get_latest_export() -> Path | None:
    """Return newest export directory matching export_* naming."""
    candidates = [p for p in EXPORTS_DIR.glob("export_*") if p.is_dir()]
    if not candidates:
        return None
    return sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def cmd_up() -> int:
    ensure_paths()
    return run_command(compose_command("up", "-d"))


def cmd_down() -> int:
    return run_command(compose_command("down"))


def cmd_status() -> int:
    return run_command(compose_command("ps"))


def cmd_logs() -> int:
    return run_command(compose_command("logs", "--tail", "150"))


def cmd_reset() -> int:
    rc = run_command(compose_command("down", "--volumes", "--remove-orphans"))
    if rc != 0:
        return rc

    for generated in [
        HA_CONFIG_DIR / ".storage",
        HA_CONFIG_DIR / ".cloud",
        DRY_RUN_TARGET,
    ]:
        if generated.exists():
            shutil.rmtree(generated, ignore_errors=True)

    DRY_RUN_TARGET.mkdir(parents=True, exist_ok=True)
    return 0


def cmd_dry_run() -> int:
    ensure_paths()

    # 1) Full local pipeline against the sandbox config
    rc = run_command(
        [sys.executable, str(ORCHESTRATOR), "full", "--source", str(HA_CONFIG_DIR)]
    )
    if rc != 0:
        return rc

    latest = get_latest_export()
    if latest is None:
        print("No export directory was generated under exports/.")
        return 1

    # 2) Validate produced export
    rc = run_command(
        [sys.executable, str(ORCHESTRATOR), "validate", "--source", str(latest)]
    )
    if rc != 0:
        return rc

    # 3) Execute local import dry-run
    rc = run_command(
        [
            sys.executable,
            str(ORCHESTRATOR),
            "import",
            "--source",
            str(latest),
            "--target",
            str(DRY_RUN_TARGET),
            "--dry-run",
        ]
    )
    if rc != 0:
        return rc

    print(f"Dry-run validation completed successfully. Latest export: {latest}")
    return 0


def cmd_health() -> int:
    return run_command([sys.executable, str(HEALTH_CHECK)])


def cmd_api_smoke() -> int:
    token = os.environ.get("HA_TEST_TOKEN")
    command = [sys.executable, str(API_TOKEN_SMOKE)]
    if token:
        command.extend(["--token", token])
    return run_command(command)


def cmd_token_bootstrap() -> int:
    return run_command([sys.executable, str(TOKEN_BOOTSTRAP), "--export-env"])


def cmd_token_prune() -> int:
    return run_command([sys.executable, str(TOKEN_PRUNE), "--export-env"])


def cmd_quality_gate() -> int:
    """Run a permanent local sandbox validation gate.

    Gate order:
      1) status (container up)
      2) health (HTTP reachability)
      3) dry-run (workflow export/validate/import dry-run)
      4) api-smoke (requires HA_TEST_TOKEN if available)
    """
    for label, command in [
        ("status", "status"),
        ("health", "health"),
        ("dry-run", "dry-run"),
    ]:
        rc = commands_map()[command]()
        if rc != 0:
            print(f"❌ quality-gate failed at step: {label}")
            return rc

    if os.environ.get("HA_TEST_TOKEN"):
        rc = commands_map()["api-smoke"]()
        if rc != 0:
            print("❌ quality-gate failed at step: api-smoke")
            return rc
    else:
        print("ℹ quality-gate skipped api-smoke (HA_TEST_TOKEN not set)")

    print("✅ quality-gate passed")
    return 0


def commands_map() -> dict[str, Callable[[], int]]:
    """Return command dispatch map."""
    return {
        "up": cmd_up,
        "down": cmd_down,
        "status": cmd_status,
        "logs": cmd_logs,
        "reset": cmd_reset,
        "dry-run": cmd_dry_run,
        "health": cmd_health,
        "api-smoke": cmd_api_smoke,
        "token-bootstrap": cmd_token_bootstrap,
        "token-prune": cmd_token_prune,
        "quality-gate": cmd_quality_gate,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Local Home Assistant dry-run test platform manager"
    )
    parser.add_argument(
        "command",
        choices=[
            "up",
            "down",
            "status",
            "logs",
            "reset",
            "dry-run",
            "health",
            "api-smoke",
            "token-bootstrap",
            "token-prune",
            "quality-gate",
        ],
        help="Platform management command",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return commands_map()[args.command]()


if __name__ == "__main__":
    sys.exit(main())
