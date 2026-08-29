"""Baseline live ``check_config`` runner (CONN-06).

:func:`run_config_check` executes the resolved config-check command on the host
*once*, at connect time, and parses its output into a :class:`CheckResult`. A
check that runs and reports problems is data, not an exception - the caller
(:mod:`haco.connect`) decides what to do with a failing baseline.

HAOS caveat: ``ha core check`` shipped a config-path bug in 2025.11
(home-assistant/core#156294) where it can report ``configuration.yaml`` missing
even though the file exists at the resolved config dir. On a ``haos`` host that
single line is downgraded to a warning with a hint to set the
``config_dir`` / ``config_check_cmd`` override, rather than failing the baseline.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from haco.discover import CommandRunner, HostFacts

_HAOS_PATH_BUG_HINT = (
    "possible ha core check path bug (home-assistant/core#156294); verify the config_check_cmd override"
)


@dataclass(frozen=True)
class CheckResult:
    """Outcome of one baseline config check."""

    ok: bool
    exit_status: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    raw: str = ""


def _is_haos_path_bug(low: str) -> bool:
    return "configuration.yaml" in low and ("not found" in low or "no such file" in low or "does not exist" in low)


async def run_config_check(client: CommandRunner, facts: HostFacts) -> CheckResult:
    """Run ``facts.config_check_cmd`` on the host and classify its output.

    ``ok`` is true only when the command exited zero *and* no error lines were
    parsed. A non-zero exit with no recognised error line still yields a
    non-empty ``errors`` list (the last output line, or a synthetic message) so
    the caller always has something to show.
    """
    res = await client.run(facts.config_check_cmd)

    text = res.stdout
    if res.stderr:
        text = f"{text}\n{res.stderr}" if text else res.stderr

    errors: list[str] = []
    warnings: list[str] = []
    haos = facts.install_type == "haos"
    haos_path_bug = False
    in_failure_section = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        low = line.lower()

        if "fail" in low:
            in_failure_section = True
        elif low.rstrip(":").endswith(("warning", "warnings")):
            in_failure_section = False

        if haos and _is_haos_path_bug(low):
            warnings.append(_HAOS_PATH_BUG_HINT)
            haos_path_bug = True
            continue

        if "ERROR" in line:
            errors.append(line)
            continue
        if in_failure_section and line.startswith(("- ", "* ")):
            errors.append(line)
            continue
        if "WARNING" in line:
            warnings.append(line)
            continue

    if res.exit_status != 0 and not errors and not haos_path_bug:
        body = text.strip().splitlines()
        errors.append(body[-1].strip() if body else f"config check failed (exit {res.exit_status})")

    ok = res.exit_status == 0 and not errors
    return CheckResult(
        ok=ok,
        exit_status=res.exit_status,
        errors=errors,
        warnings=warnings,
        raw=text,
    )
