---
phase: 01-connect-discover
plan: 03
subsystem: infra
tags: [ssh, discovery, home-assistant, install-detect, asyncssh, mypy-strict, pytest]

requires:
  - phase: "01-02"
    provides: "haco.ssh.SSHClient async wrapper + CmdResult frozen dataclass"
  - phase: "01-01"
    provides: "HostProfile pydantic v2 model (install_type / container_name / config_dir / config_check_cmd / restart_cmd override fields), haco.errors hierarchy"
provides:
  - "src/haco/hosttypes.py - per-install-type defaults matrix (InstallType Literal, CmdContext, TypeDefaults, DEFAULTS with config-dir candidates + check/restart command templates for haos/container/core)"
  - "src/haco/discover.py - async discover(client, profile) -> HostFacts; detect_type(); resolve_config_dir(); CommandRunner Protocol"
  - "haco.errors.DiscoveryError for inconclusive autodetect"
  - "tests/test_discover.py - 5 discovery scenarios via a scripted FakeSSH"
affects: [01-04, pull, stage, check, restart, baseline-check, preflight]

actuals:
  tokens: 3800
  tasks: 4
  commits: 4

tech-stack:
  added: []
  patterns:
    - "CommandRunner Protocol (the run()-only slice of SSHClient) so discovery is unit-testable with a structural fake and stays mypy --strict clean"
    - "Command templates as Callable[[CmdContext], str] on a frozen TypeDefaults so a profile override substitutes cleanly without touching the matrix"
    - "Override-first resolution: every HostFacts field yields to the matching HostProfile override verbatim; when install_type + config_dir + config_check_cmd + restart_cmd are all set, discover() makes zero SSH calls"
    - "Remote POSIX path handling via posixpath (not os.path) on the Windows workstation; $HOME expanded in Python before shlex.quote so quoting never blocks expansion"

key-files:
  created:
    - "src/haco/hosttypes.py - InstallType, CmdContext, TypeDefaults, DEFAULTS"
    - "src/haco/discover.py - HostFacts, detect_type, resolve_config_dir, discover, CommandRunner"
    - "tests/test_discover.py - FakeSSH + haos/container/core/undetectable/override scenarios"
  modified:
    - "src/haco/errors.py - added DiscoveryError(HacoError)"

key-decisions:
  - "detect_type returns a private _Detected(install_type, container_name, venv_bin) dataclass rather than a bare InstallType so the container name and venv bin discovered during probing flow into discover() without a second round-trip"
  - "discover() takes a CommandRunner Protocol, not SSHClient concretely - keeps the real type in production (SSHClient satisfies it structurally) while letting tests pass a plain FakeSSH under mypy --strict"
  - "core config-dir candidate stored as the literal \"$HOME/.homeassistant\" in the matrix; discover() resolves $HOME via `printf %s \"$HOME\"` and substitutes before probing, so shlex.quote() on the concrete path is safe"
  - "container config_dir is the host bind-mount path (Source whose Destination is /config, from `docker inspect -f`), while the check command keeps `-c /config` (the in-container path) - the two are deliberately different"
  - "Task 4 (gate) required no code change - the gate was already green after Task 3, so no separate commit (same as plan 01-02 Task 5)"

patterns-established:
  - "Probe commands are read-only (command -v, test -d/-f, docker ps/inspect, printf) - discovery never mutates the host"
  - "HostFacts.notes carries advisory strings (the HAOS 2025.11 `ha core check` path-bug caveat, home-assistant/core#156294) for later phases to surface"

requirements-completed: [CONN-04, CONN-05]

coverage:
  - id: D1
    description: "Per-install-type defaults matrix: DEFAULTS has exactly keys haos/container/core, each yielding a non-empty check_cmd and restart_cmd string from a CmdContext"
    requirement: "CONN-05"
    verification:
      - kind: unit
        ref: "tests/test_discover.py#test_discover_haos, test_discover_container, test_discover_core (assert resolved config_check_cmd / restart_cmd per type)"
        status: pass
      - kind: manual_procedural
        ref: "uv run python -c \"from haco.hosttypes import DEFAULTS, InstallType; print(sorted(DEFAULTS))\" -> ['container', 'core', 'haos']"
        status: pass
    human_judgment: false
  - id: D2
    description: "async discover(client, profile) -> HostFacts autodetects install type from scripted probe output: ha binary -> haos, docker + HA container -> container, hass in a venv -> core"
    requirement: "CONN-04"
    verification:
      - kind: unit
        ref: "tests/test_discover.py#test_discover_haos, test_discover_container, test_discover_core"
        status: pass
    human_judgment: false
  - id: D3
    description: "discover() resolves a concrete config_dir, config_check_cmd, and restart_cmd for each type - haos /homeassistant + `ha core check` + `ha core restart`; container bind-mount path + `docker exec ... check_config` + `docker restart`; core $HOME/.homeassistant + `<venv>/hass --script check_config` + `systemctl restart home-assistant@<user>`"
    requirement: "CONN-05"
    verification:
      - kind: unit
        ref: "tests/test_discover.py#test_discover_haos, test_discover_container, test_discover_core"
        status: pass
    human_judgment: false
  - id: D4
    description: "A profile override for install_type / config_dir / config_check_cmd / restart_cmd wins over autodetect verbatim, and an all-overridden profile makes zero SSH calls"
    requirement: "CONN-05"
    verification:
      - kind: unit
        ref: "tests/test_discover.py#test_discover_profile_overrides_win (asserts config_check_cmd == 'mycheck' and fake.calls == [])"
        status: pass
    human_judgment: false
  - id: D5
    description: "An undetectable host (all probes exit 1) raises DiscoveryError naming the install_type override as the fix"
    requirement: "CONN-04"
    verification:
      - kind: unit
        ref: "tests/test_discover.py#test_discover_undetectable"
        status: pass
    human_judgment: false
  - id: D6
    description: "Full quality gate green: ruff, black --check, mypy --strict, pytest all exit 0"
    requirement: "CONN-04"
    verification:
      - kind: unit
        ref: "uv run ruff check . && uv run black --check . && uv run mypy && uv run pytest -q (18 passed)"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-08-29
status: complete
---

# Phase 1 Plan 03: Install-type discovery Summary

**`haco.discover.discover()` probes an SSH host read-only to classify it as haos / container / core, then resolves a concrete config dir, config-check command, and restart command from a per-type `DEFAULTS` matrix - with every field yielding to a `HostProfile` override verbatim.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-08-29 (approx, right after 01-02 state commit)
- **Completed:** 2026-08-29
- **Tasks:** 4
- **Files modified:** 4 (3 new: hosttypes.py, discover.py, tests/test_discover.py; 1 modified: errors.py)

## Accomplishments

- `src/haco/hosttypes.py`: `InstallType` Literal, frozen `CmdContext` (config_dir, container_name, venv_bin, user) and `TypeDefaults` (config_dir_candidates tuple + `check_cmd` / `restart_cmd` as `Callable[[CmdContext], str]`), and `DEFAULTS` populated for haos / container / core exactly per the phase CONTEXT matrix.
- `src/haco/discover.py`: `async discover(client, profile) -> HostFacts` (frozen `HostFacts`: install_type, config_dir, config_check_cmd, restart_cmd, container_name, notes). Helpers: `detect_type()` (ha -> haos; docker + an HA container in `docker ps` -> container; `hass` on PATH -> core), `resolve_config_dir()` (first candidate that is a dir holding `configuration.yaml`), `_container_config_bind()` (Source bound to `/config` from `docker inspect -f`), `_remote_home()` / `_expand_home()` for the core `$HOME` candidate. A `CommandRunner` Protocol types the client param.
- `haco.errors.DiscoveryError(HacoError)` - raised when install type, HA container, or config dir is undetermined and the profile does not supply it; the message names the unblocking override.
- `tests/test_discover.py`: `FakeSSH` maps command prefixes -> `CmdResult` (unknown -> exit 1); 5 scenarios (haos, container, core, undetectable, override) all green.
- Full gate green: `ruff` / `black --check` / `mypy --strict` (15 files) / `pytest -q` (18 passed, +5 new).

## Task Commits

Each task was committed atomically:

1. **Task 1: host-type matrix** - `dd33d53` (feat) - `src/haco/hosttypes.py`
2. **Task 2: HostFacts + discover()** - `1c07295` (feat) - `src/haco/discover.py`, `src/haco/errors.py`
3. **Task 3: discovery tests with a scripted SSH double** - `1ef209a` (test) - `tests/test_discover.py`
4. **Task 4: gate** - no commit; gate was already green after Task 3 (no code change)

**Plan metadata:** _(this docs commit)_

## Files Created/Modified

- `src/haco/hosttypes.py` - per-install-type defaults matrix (candidates + command templates)
- `src/haco/discover.py` - `HostFacts`, `detect_type`, `resolve_config_dir`, `discover`, `CommandRunner` Protocol
- `src/haco/errors.py` - added `DiscoveryError(HacoError)`
- `tests/test_discover.py` - `FakeSSH` + haos/container/core/undetectable/override scenarios

## Decisions Made

- **`detect_type` returns a private `_Detected` dataclass** (install_type + container_name + venv_bin), not a bare `InstallType` - the container name and venv bin found while probing flow straight into `discover()` with no extra round-trip.
- **`discover()` takes a `CommandRunner` Protocol**, not `SSHClient` concretely - `SSHClient` satisfies it structurally in production; tests pass a plain `FakeSSH` and mypy `--strict` stays clean.
- **Core config-dir candidate is the literal `"$HOME/.homeassistant"` in the matrix**; `discover()` resolves `$HOME` via `printf %s "$HOME"` and substitutes before probing, so `shlex.quote()` on the concrete path never blocks shell expansion (honors the "shlex.quote every remote path interpolation" convention from earlier waves).
- **Container `config_dir` is the host bind-mount path** (the `Source` whose `Destination` is `/config`), while the check command keeps `-c /config` (the in-container path) - deliberately different values.
- **Task 4 (gate) got no commit** - green after Task 3, matching plan 01-02's Task 5 no-op pattern.

## Deviations from Plan

None - plan executed exactly as written. Rules 1-4 not triggered; no bugs, missing critical functionality, blockers, or architectural changes surfaced.

Minor faithful interpretations (not deviations): `detect_type` returns `_Detected | None` rather than a bare `InstallType | None` so discovered container-name / venv-bin propagate; `discover()`'s client parameter is typed as a `CommandRunner` Protocol so the scripted fake type-checks under `mypy --strict`. Both preserve the plan's described behaviour and signatures.

## Issues Encountered

- `uv run mypy tests/test_discover.py` (single-file invocation) reports spurious `import-untyped` errors for `haco.*` because it treats the installed package as stub-less. The real gate runs `uv run mypy` with no args (`files = ["src", "tests"]` in pyproject) and is clean across all 15 source files. No `py.typed` marker added - out of scope for this plan.
- Git reports `LF will be replaced by CRLF` for the new files on this Windows checkout; ruff / black / mypy / pytest are unaffected (same as prior plans).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `01-04` (baseline `check_config` + permission preflight) can consume `HostFacts.config_dir` / `config_check_cmd` / `restart_cmd` directly and surface `HostFacts.notes` (the HAOS 2025.11 `ha core check` caveat) when a baseline check reports a missing `configuration.yaml` that actually exists.
- `discover()` composes with `SSHClient` from 01-02 with no glue needed (structural `CommandRunner` match).
- No blockers.

## Self-Check: PASSED

- `src/haco/hosttypes.py`, `src/haco/discover.py`, `tests/test_discover.py` present on disk; `src/haco/errors.py` carries `DiscoveryError`.
- Commits `dd33d53`, `1c07295`, `1ef209a` in `git log`.
- `uv run ruff check .` / `black --check .` / `mypy` / `pytest -q` all exit 0 (18 passed).

---
*Phase: 01-connect-discover*
*Completed: 2026-08-29*
