"""End-to-end connect orchestration.

:func:`connect_and_probe` is the spine of ``haco connect``: it opens one SSH
session, discovers the install layout, runs the permission preflight, and runs
the baseline config check - then reports whether the host is ready.

A failing preflight or a failing baseline check is *not* an error here: the
:class:`ConnectReport` is still returned with ``ready=False`` and the CLI turns
that into an exit code. Only genuine connection / discovery failures
(:class:`~haco.errors.ConnectionError`, :class:`~haco.errors.AuthError`,
:class:`~haco.errors.DiscoveryError`) propagate out.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from haco.check import CheckResult, run_config_check
from haco.discover import HostFacts, discover
from haco.models import HostProfile
from haco.preflight import PreflightResult, permission_preflight
from haco.ssh import SSHClient


@dataclass(frozen=True)
class ConnectReport:
    """Everything ``haco connect`` needs to render a verdict."""

    facts: HostFacts
    preflight: PreflightResult
    check: CheckResult
    ready: bool


async def connect_and_probe(
    profile: HostProfile,
    *,
    password_provider: Callable[[], str] | None = None,
) -> ConnectReport:
    """Open SSH, discover the host, preflight permissions, run the baseline check.

    Returns a :class:`ConnectReport`. Does not raise on a failing preflight or
    check; lets connection / discovery errors propagate.
    """
    async with SSHClient(profile, password_provider=password_provider) as client:
        facts = await discover(client, profile)
        preflight = await permission_preflight(client, facts)
        check = await run_config_check(client, facts)

    ready = preflight.ok and check.ok
    return ConnectReport(facts=facts, preflight=preflight, check=check, ready=ready)
