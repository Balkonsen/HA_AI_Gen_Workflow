---
phase: 01-connect-discover
verified: 2026-08-30T06:04:19Z
status: passed
score: 5/5 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: n/a
---

# Phase 1: Connect & Discover Verification Report

**Phase Goal:** A profile-driven SSH connection that knows what kind of HA it is talking to and where the config lives, and refuses to proceed if the ground is unsafe.
**Verified:** 2026-08-30T06:04:19Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | `haco connect PROFILE` opens an SSH session using a key file or a password | ✓ VERIFIED | `src/haco/ssh.py` `SSHClient.connect()` builds `asyncssh.connect` options — `client_keys=[key_path]` for `auth=key`, `password=resolve_password()` for `auth=password`. Real in-process asyncssh server tests pass: `tests/test_ssh.py::test_key_auth`, `test_password_auth_env`, `test_password_auth_provider`. Live smoke (01-04 checkpoint, user-verified 2026-08-30): `haco connect hass` via `--password-stdin` against HA OS `192.168.178.22:22951` returned exit 0. |
| 2 | The tool prints the detected install type (HA OS/Supervised, Container, or Core venv) | ✓ VERIFIED | `src/haco/discover.py` `detect_type()` — `command -v ha`→haos, `docker` + HA container→container, `command -v hass`→core. `cli.py::_render_report` prints `install_type` row. `tests/test_discover.py` covers all three types + undetectable→`DiscoveryError`. Live smoke printed `install_type=haos` (correct). |
| 3 | The tool prints the resolved config directory, config-check command, and restart command, honoring profile overrides | ✓ VERIFIED | `discover.py::discover()` — `config_dir = profile.config_dir or resolve_config_dir(...)`, `config_check_cmd = profile.config_check_cmd or DEFAULTS[itype].check_cmd(ctx)`, likewise `restart_cmd`; `install_type` override also honored. `cli.py::_render_report` prints all three rows. `tests/test_discover.py::test_discover_profile_overrides_win` asserts overrides used verbatim AND host never touched (`fake.calls == []`). Live smoke: `config_dir=/homeassistant`, `config_check_cmd="ha core check"`, `restart_cmd="ha core restart"`. |
| 4 | The tool runs the live baseline `check_config` and reports pass/fail | ✓ VERIFIED | `src/haco/check.py::run_config_check()` executes `facts.config_check_cmd` once, parses ERROR/WARNING/failure-section lines, `ok = exit==0 and no errors`. `connect.py::connect_and_probe` invokes it inside the live SSH session. `cli.py::_render_report` prints `baseline check  exit N` + error/warning lines. `tests/test_check.py` (4 tests: clean→ok, ERROR line→not ok, non-zero exit→synthesised error, HAOS #156294 path bug→warning not error). Live smoke: `ha core check` ran on the live host, exit 0, reported. |
| 5 | The tool refuses to continue when the baseline fails or the SSH user lacks write/restart permission, with a clear message | ✓ VERIFIED | `src/haco/preflight.py::permission_preflight()` — `test -w` + real `touch`/`rm` of `.haco_wtest`; restart-bin on PATH + passwordless `sudo -n true` when a root-needing bin and user≠root. Findings carry exact remediation strings ("SSH user needs write on <dir>", "passwordless sudo required for '<cmd>'", "<bin> not found on PATH"). `connect.py`: `ready = preflight.ok and check.ok`. `cli.py::connect` prints `NOT READY` (red) + findings/errors then `raise typer.Exit(code=1)`. Tests: `test_preflight.py` (non-writable dir names the dir; missing sudo→not ok), `test_connect.py::test_failing_preflight_is_not_ready`, `test_failing_check_is_not_ready`, `test_connect_exits_one_when_not_ready` (CLI exit 1 + "NOT READY"). Live smoke confirmed exit 2 + message (no traceback) on bad credential / closed port. |

**Score:** 5/5 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `pyproject.toml` | project `haco`, console script `haco = haco.cli:app`, mypy strict | ✓ VERIFIED | `uv run haco profile list` works; `uv run mypy` = strict, 21 files, clean. |
| `src/haco/models.py` | pydantic v2 `HostProfile`, secret-free by design | ✓ VERIFIED | `extra="forbid"`; no `password`/`secret`/`token` field; `Slug` pattern validator; `key_path`/`known_hosts` are path strings only. |
| `src/haco/profile.py` | `save_profile`/`load_profile`/`list_profiles`/`profile_path`, XDG/APPDATA root | ✓ VERIFIED | Atomic write (temp + `os.replace`), `chmod 0o600`/`0o700` on POSIX, `_FORBIDDEN_KEYS` guard before write, `ProfileNotFound` on absent file. |
| `src/haco/ssh.py` | async `SSHClient` (connect/run/sftp/close + `__aenter__/__aexit__`) | ✓ VERIFIED | `CmdResult` frozen dataclass; asyncssh errors mapped to `AuthError`/`HostKeyError`/`ConnectionError`; password never read from profile. |
| `src/haco/hosttypes.py` | per-type default matrix (3 entries) | ✓ VERIFIED | `DEFAULTS` keys exactly `haos`/`container`/`core`; command templates are functions over `CmdContext`. |
| `src/haco/discover.py` | async `discover(client, profile) -> HostFacts` | ✓ VERIFIED | Override precedence implemented per field; container bind-mount resolution via `docker inspect`; `DiscoveryError` with actionable message on every dead end. |
| `src/haco/check.py` | async `run_config_check(client, facts) -> CheckResult` | ✓ VERIFIED | Frozen `CheckResult`; failure-section + ERROR/WARNING parsing; HAOS #156294 path-bug downgraded to warning. |
| `src/haco/preflight.py` | async `permission_preflight(client, facts) -> PreflightResult` | ✓ VERIFIED | Frozen `PreflightResult`; write + restart checks; failure returned as data, never raised. |
| `src/haco/connect.py` | async `connect_and_probe(profile) -> ConnectReport` | ✓ VERIFIED | Composes `SSHClient` → `discover` → `permission_preflight` → `run_config_check` in one session; lets connection/discovery errors propagate. |
| `src/haco/cli.py` | `haco connect` wired, exit codes 0/1/2 | ✓ VERIFIED | 01-01 stub fully replaced; `--password-stdin`; rich table render; `asyncio.run(connect_and_probe(...))`. |
| test suite | round-trip, SSH auth, discovery, check, preflight, connect, CLI | ✓ VERIFIED | `tests/test_profile.py`, `test_ssh.py` (real asyncssh server), `test_discover.py`, `test_check.py`, `test_preflight.py`, `test_connect.py`. `uv run pytest -q` = 33 passed. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `cli.py` | `profile.py` / `connect.py` | Typer commands call library funcs only | ✓ WIRED | `connect` calls `load_profile` then `asyncio.run(connect_and_probe(...))`; `_render_report` sets exit code. |
| `ssh.py` | `asyncssh` | `connect()` builds options from `HostProfile` | ✓ WIRED | host/port/username/client_keys/password/known_hosts. |
| `ssh.py` | env / prompt | `resolve_password()` — provider → `HACO_SSH_PASSWORD` → `getpass` | ✓ WIRED | Never reads the profile file; `AuthError` when no source. |
| `discover.py` | `ssh.py` | probe commands via `client.run` | ✓ WIRED | `detect_type`, `resolve_config_dir`, `_container_config_bind` all use `run`. |
| `discover.py` | `hosttypes.py` | `DEFAULTS[itype].check_cmd(ctx)` / `restart_cmd(ctx)` | ✓ WIRED | Only invoked when the corresponding profile override is absent. |
| `connect.py` | `discover` + `preflight` + `check` | single `async with SSHClient(...)` block | ✓ WIRED | `ready = preflight.ok and check.ok`. |

### Data-Flow Trace (Level 4)

| Rendered value | Source | Produces real data | Status |
| --- | --- | --- | --- |
| `install_type` / `config_dir` / `config_check_cmd` / `restart_cmd` | `discover()` from live probe output or profile overrides | Yes (live SSH probes; verified live smoke on HA OS) | ✓ FLOWING |
| `baseline check exit N` + error/warning lines | `run_config_check()` from live `client.run(config_check_cmd)` | Yes | ✓ FLOWING |
| preflight `write` / `restart` + findings | `permission_preflight()` from live `test -w`, `touch`/`rm`, `command -v`, `sudo -n` | Yes | ✓ FLOWING |
| `READY` / `NOT READY` + exit code | `report.ready` computed from preflight.ok and check.ok | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| CLI help documents NAME + --password-stdin | `uv run haco connect --help` | Usage shows `{name}` required + `--password-stdin` | ✓ PASS |
| profile list works (console script wired) | `uv run haco profile list` | prints `hass` | ✓ PASS |
| missing profile → exit 2, message only | `uv run haco connect __nope__` | "No profile named '__nope__'. Run 'haco profile add ...'" exit 2 | ✓ PASS |
| full test suite | `uv run pytest -q` | 33 passed | ✓ PASS |
| strict type check | `uv run mypy` | Success, 21 source files | ✓ PASS |
| lint / format | `uv run ruff check .` / `black --check .` | all checks pass / 21 files unchanged | ✓ PASS |

### Probe Execution

N/A — no probe scripts declared or implied for this phase.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| CONN-01 | 01-01 | Locally-stored host profile, no secrets committed | ✓ SATISFIED | `models.py` (no secret fields), `profile.py` (`_FORBIDDEN_KEYS` guard, atomic write), `test_profile.py::test_written_file_has_no_secret_text`. |
| CONN-02 | 01-02 | Connect over SSH using a key file | ✓ SATISFIED | `ssh.py` `client_keys=[key_path]`; `test_ssh.py::test_key_auth` against real server; live smoke path exists. |
| CONN-03 | 01-02 | Connect over SSH using a password when no key | ✓ SATISFIED | `resolve_password()` provider/env/prompt; `test_password_auth_env`/`_provider`; live smoke used `--password-stdin`. |
| CONN-04 | 01-03 | Autodetect HA install type | ✓ SATISFIED | `discover.py::detect_type`; `test_discover.py` haos/container/core/undetectable. |
| CONN-05 | 01-03 | Resolve config dir + check + restart cmd, per-field overrides | ✓ SATISFIED | `discover()` override precedence; `test_discover_profile_overrides_win`. |
| CONN-06 | 01-04 | Baseline `check_config` on live host, refuse if already failing | ✓ SATISFIED | `check.py::run_config_check`; `connect.py` gates `ready`; `cli` exit 1 + output on failure; `test_check.py`, `test_connect.py::test_failing_check_is_not_ready`. |
| CONN-07 | 01-04 | Verify write + restart permission, fail early with clear message | ✓ SATISFIED | `preflight.py::permission_preflight` with remediation strings; `test_preflight.py`, `test_connect.py::test_failing_preflight_is_not_ready`. |

All 7 phase requirements are marked Complete in `.planning/REQUIREMENTS.md` (checklist + traceability table). No orphaned requirements.

### Decision Coverage

All CONTEXT.md `<decisions>` are honored in the shipped code: Python 3.12 + `uv` + Ruff/Black(120) + `mypy --strict` scaffold (01-01); `asyncssh` not paramiko (`ssh.py`); TOML profile at XDG/APPDATA with no secrets (`profile.py`); pydantic v2 `HostProfile` (`models.py`); three install types + per-type matrix + detection order (`hosttypes.py` / `discover.py`); baseline gate with HAOS `home-assistant/core#156294` caveat (`check.py`); permission preflight with `test -w` + touch/rm and `sudo -n true` (`preflight.py`). honored 8/8, not_honored: none.

### Security Follow-up Check

The CRITICAL commit-review finding on 01-02 (`known_hosts=None` disabling host-key verification / MITM) is fixed:
- `src/haco/ssh.py` lines 86-87: `known_hosts` is added to the asyncssh options dict **only** when `profile.known_hosts is not None`. When the profile does not name a file, the option is omitted entirely so asyncssh falls back to `~/.ssh/known_hosts` + system files (verification stays ON).
- `src/haco/models.py`: `known_hosts` docstring corrected — "`None` ... does NOT disable host-key checking".
- Regression test present and passing: `tests/test_ssh.py::test_unknown_host_key_rejected` — a profile with `known_hosts=None` against the ephemeral test server (in no known_hosts file) raises `HostKeyError`/`ConnectionError`.
- Fix commit `f3a7287` confirmed in git history.

### Anti-Patterns Found

None. No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER`/`NotImplementedError` markers in `src/haco/` or `tests/`. The 01-01 `haco connect` stub was fully replaced by the wired command in 01-04.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| test_profile.py | CONN-01 | 5 | 0 | No | Value | OK |
| test_ssh.py | CONN-02/03 | 8 | 0 | No (real in-process asyncssh server) | Value / behavioral | OK |
| test_discover.py | CONN-04/05 | 5 | 0 | No | Value | OK |
| test_check.py | CONN-06 | 4 | 0 | No | Value | OK |
| test_preflight.py | CONN-07 | 3 | 0 | No | Value | OK |
| test_connect.py | CONN-06/07 + goal | 8 | 0 | No | Behavioral (CliRunner exit codes) | OK |

Disabled tests on requirements: 0. Circular patterns: 0. Insufficient assertions: 0. The discovery/check/preflight/connect suites drive a scripted stand-in for the SSH *transport* (prefix→`CmdResult` map); the real SSH layer they stub is covered end-to-end in `test_ssh.py` against a genuine asyncssh server, so this is a valid seam, not a mock of the system under test. Expected command strings and parse outcomes are literals / real HA output shapes, not values generated by haco.

### Human Verification

N/A — the phase's blocking `checkpoint:human-verify` (01-04 Task 4a) was already executed and PASSED by the user on 2026-08-30 against a live HA OS host (`192.168.178.22:22951`, root): `install_type=haos`, `config_dir=/homeassistant`, `ha core check` exit 0, preflight `write=True restart=True`, `READY` exit 0; error paths (bad credential, closed port) returned exit 2 with a message and no traceback. The single path not exercised live — a deliberately broken config producing `NOT READY` — is covered at the unit level with behavioral assertions (`test_connect.py::test_failing_check_is_not_ready`, `test_connect_exits_one_when_not_ready`; `test_check.py::test_error_line_makes_not_ok`), and the gating mechanism (`ready = preflight.ok and check.ok` → exit 1) is trivially simple. No further human verification required.

### Gaps Summary

None. All five ROADMAP success criteria are observably achieved in `src/haco/`, all four plans' frontmatter must-haves (truths, artifacts, key links) verify, all seven CONN requirements are implemented and tested, the quality gate is green (ruff / black / mypy --strict 21 files / pytest 33 passed), the CRITICAL host-key-verification finding is fixed with a regression test, and the blocking human checkpoint passed against real hardware.

Informational (not a gap): `.planning/ROADMAP.md` still shows `- [ ] Phase 1` and `- [ ] 01-04: ...` unchecked — roadmap bookkeeping only; `.planning/REQUIREMENTS.md` and the plan checklist already record completion.

---

_Verified: 2026-08-30T06:04:19Z_
_Verifier: Claude (gsd-verifier)_
