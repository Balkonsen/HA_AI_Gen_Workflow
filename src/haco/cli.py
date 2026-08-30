"""The ``haco`` command-line interface.

Only argument parsing lives here; every piece of real behaviour is in the
library modules (:mod:`haco.models`, :mod:`haco.profile`, and later plans).
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Callable
from typing import Any

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from haco.connect import ConnectReport, connect_and_probe
from haco.errors import ConnectionError as HacoConnectionError
from haco.errors import DiscoveryError, HacoError
from haco.models import HostProfile
from haco.profile import list_profiles, load_profile, save_profile

app = typer.Typer(help="Local-network Home Assistant config optimizer.", no_args_is_help=True)
profile_app = typer.Typer(help="Create and inspect stored host profiles.", no_args_is_help=True)
app.add_typer(profile_app, name="profile")

_console = Console()


@profile_app.command("add")
def profile_add(
    name: str = typer.Argument(..., help="Profile name (slug: lowercase, digits, '-', '_')."),
    host: str = typer.Option(..., "--host", help="Hostname or IP of the Home Assistant server."),
    user: str = typer.Option(..., "--user", help="SSH user."),
    port: int = typer.Option(22, "--port", help="SSH port."),
    auth: str = typer.Option("key", "--auth", help="Auth mode: 'key' or 'password'."),
    key_path: str | None = typer.Option(None, "--key-path", help="Path to the SSH private key."),
    install_type: str | None = typer.Option(None, "--install-type", help="'haos', 'container', or 'core'."),
    container_name: str | None = typer.Option(None, "--container-name", help="HA container name (container installs)."),
    config_dir: str | None = typer.Option(None, "--config-dir", help="Override the discovered config directory."),
    config_check_cmd: str | None = typer.Option(None, "--config-check-cmd", help="Override the config-check command."),
    restart_cmd: str | None = typer.Option(None, "--restart-cmd", help="Override the restart command."),
) -> None:
    """Build a :class:`HostProfile` from the options and save it locally."""
    raw: dict[str, Any] = {
        "name": name,
        "host": host,
        "user": user,
        "port": port,
        "auth": auth,
        "key_path": key_path,
        "install_type": install_type,
        "container_name": container_name,
        "config_dir": config_dir,
        "config_check_cmd": config_check_cmd,
        "restart_cmd": restart_cmd,
    }
    try:
        profile = HostProfile.model_validate(raw)
    except ValidationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    try:
        path = save_profile(profile)
    except HacoError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(str(path))


@profile_app.command("list")
def profile_list() -> None:
    """Print the names of every stored profile."""
    names = list_profiles()
    if not names:
        typer.echo("no profiles")
        return
    for name in names:
        typer.echo(name)


@profile_app.command("show")
def profile_show(
    name: str = typer.Argument(..., help="Profile name to display."),
) -> None:
    """Pretty-print a stored profile."""
    try:
        profile = load_profile(name)
    except HacoError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    table = Table(title=f"profile: {name}")
    table.add_column("field", style="cyan")
    table.add_column("value")
    for field, value in profile.model_dump(exclude_none=True).items():
        table.add_row(field, str(value))
    _console.print(table)


def _password_provider(password_stdin: bool) -> Callable[[], str] | None:
    """Return a provider that yields the first stdin line, or ``None``."""
    if not password_stdin:
        return None
    password = sys.stdin.readline().rstrip("\n")
    return lambda: password


def _render_report(name: str, report: ConnectReport) -> None:
    facts = report.facts
    table = Table(title=f"connect: {name}")
    table.add_column("field", style="cyan")
    table.add_column("value")
    table.add_row("install_type", facts.install_type)
    table.add_row("config_dir", facts.config_dir)
    table.add_row("config_check_cmd", facts.config_check_cmd)
    table.add_row("restart_cmd", facts.restart_cmd)
    if facts.container_name:
        table.add_row("container_name", facts.container_name)
    _console.print(table)

    for note in facts.notes:
        _console.print(f"[dim]note: {note}[/dim]")

    pf = report.preflight
    _console.print(f"[bold]permission preflight[/bold]  write={pf.can_write_config}  restart={pf.can_restart}")
    for finding in pf.findings:
        _console.print(f"  [red]- {finding}[/red]")

    chk = report.check
    _console.print(f"[bold]baseline check[/bold]  exit {chk.exit_status}")
    for err in chk.errors:
        _console.print(f"  [red]ERROR {err}[/red]")
    for warn in chk.warnings:
        _console.print(f"  [yellow]WARNING {warn}[/yellow]")


@app.command("connect")
def connect(
    name: str = typer.Argument(..., help="Profile name to connect to."),
    password_stdin: bool = typer.Option(
        False,
        "--password-stdin",
        help="Read the SSH password from the first line of stdin.",
    ),
) -> None:
    """Connect to a profile: SSH in, discover the host, preflight permissions, run the baseline check.

    Exit code: 0 when the host is READY, 1 when it is NOT READY, and 2 on a
    connection, auth, or discovery failure (message only, no traceback).
    """
    try:
        profile = load_profile(name)
    except HacoError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc

    try:
        report = asyncio.run(connect_and_probe(profile, password_provider=_password_provider(password_stdin)))
    except (HacoConnectionError, DiscoveryError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc

    _render_report(name, report)

    if report.ready:
        _console.print("[green]READY[/green]")
        return
    _console.print("[red]NOT READY[/red]")
    raise typer.Exit(code=1)
