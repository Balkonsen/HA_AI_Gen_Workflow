"""The ``haco`` command-line interface.

Only argument parsing lives here; every piece of real behaviour is in the
library modules (:mod:`haco.models`, :mod:`haco.profile`, and later plans).
"""

from __future__ import annotations

from typing import Any

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from haco.errors import HacoError
from haco.models import HostProfile
from haco.profile import list_profiles, load_profile, save_profile

app = typer.Typer(help="Local-network Home Assistant config optimizer.", no_args_is_help=True)
profile_app = typer.Typer(help="Create and inspect stored host profiles.", no_args_is_help=True)
app.add_typer(profile_app, name="profile")

_console = Console()

_CONNECT_STUB = "connect is implemented in plan 01-04"


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


@app.command("connect")
def connect(
    name: str = typer.Argument(..., help="Profile name to connect to."),
) -> None:
    """Open an SSH session to the given profile (implemented in plan 01-04)."""
    typer.echo(_CONNECT_STUB, err=True)
    raise typer.Exit(code=1)
