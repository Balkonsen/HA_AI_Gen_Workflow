"""Per-install-type defaults for Home Assistant discovery.

Each :data:`DEFAULTS` entry knows, for one install layout, where the config
directory is likely to live and how to build the config-check and restart
commands once the concrete context (config dir, container name, venv bin,
SSH user) is known. Every field here is a *default* - a :class:`~haco.models.HostProfile`
may override the resolved config dir and both commands verbatim.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

InstallType = Literal["haos", "container", "core"]


@dataclass(frozen=True)
class CmdContext:
    """Concrete values discovery resolves before rendering a command template."""

    config_dir: str
    container_name: str | None = None
    venv_bin: str | None = None
    user: str = "root"


@dataclass(frozen=True)
class TypeDefaults:
    """Config-dir candidates plus command templates for one install type."""

    config_dir_candidates: tuple[str, ...]
    check_cmd: Callable[[CmdContext], str]
    restart_cmd: Callable[[CmdContext], str]


def _haos_check(_ctx: CmdContext) -> str:
    return "ha core check"


def _haos_restart(_ctx: CmdContext) -> str:
    return "ha core restart"


def _container_check(ctx: CmdContext) -> str:
    # The config path is always ``/config`` *inside* the container; the host
    # bind-mount path lives in ``ctx.config_dir`` and is used for SFTP only.
    return f"docker exec {ctx.container_name} python -m homeassistant --script check_config -c /config"


def _container_restart(ctx: CmdContext) -> str:
    return f"docker restart {ctx.container_name}"


def _core_check(ctx: CmdContext) -> str:
    return f"{ctx.venv_bin}/hass --script check_config -c {ctx.config_dir}"


def _core_restart(ctx: CmdContext) -> str:
    return f"systemctl restart home-assistant@{ctx.user}"


DEFAULTS: dict[InstallType, TypeDefaults] = {
    "haos": TypeDefaults(
        config_dir_candidates=("/homeassistant", "/config", "/mnt/data/supervisor/homeassistant"),
        check_cmd=_haos_check,
        restart_cmd=_haos_restart,
    ),
    "container": TypeDefaults(
        # Real candidate comes from the discovered bind mount; ``/config`` is the
        # in-container fallback probed on the host when inspect yields nothing.
        config_dir_candidates=("/config",),
        check_cmd=_container_check,
        restart_cmd=_container_restart,
    ),
    "core": TypeDefaults(
        config_dir_candidates=("$HOME/.homeassistant",),
        check_cmd=_core_check,
        restart_cmd=_core_restart,
    ),
}
