---
phase: 01-connect-discover
plan: 04
subsystem: infra
tags: [ssh, check-config, permission-preflight, home-assistant, typer, rich, pytest-asyncio, mypy-strict]

requires:
  - phase: "01-02"
    provides: "haco.ssh.SSHClient async wrapper + CmdResult; ConnectionError/AuthError/HostKeyError family"
  - phase: "01-03"
    provides: "haco.discover.discover() -> HostFacts (config_dir / config_check_cmd / restart_cmd, notes), CommandRunner Protocol, DiscoveryError"
provides:
  - "src/haco/check.py - async run_config_check(client, facts) -> CheckResult; parses ERROR/WARNING + a Failed-config section, demotes the HAOS ha-core-check path-bug line (home-assistant/core#156294) to a warning"
  - "src/haco/preflight.py - async permission_preflight(client, facts) -> PreflightResult; test -w + real touch/rm write probe, restart-binary-on-PATH + passwordless-sudo probe with exact remediation findings"
  - "src/haco/connect.py - async connect_and_probe(profile, *, password_provider=None) -> ConnectReport; one SSH session -> discover -> preflight -> baseline check; never raises on pf/chk failure"
  - "haco connect NAME [--password-stdin] wired in cli.py - renders the resolved matrix + preflight + baseline check, exit 0 READY / 1 NOT READY / 2 on ConnectionError|AuthError|DiscoveryError (no traceback)"
  - "haco.errors.CheckError / PreflightError added to the hierarchy (reserved; the connect flow returns data, never raises them)"
affects: [pull, stage, apply, restart, smoke, rollback, cli-run]

actuals:
  tokens: 5600
  tasks: 5
  commits: 4

tech-stack:
  added: []
  patterns:
    - "check_config output is classified into a frozen CheckResult (ok/exit_status/errors/warnings/raw); a check that runs and fails is data, not an exception"
    - "HAOS ha-core-check 2025.11 path bug: a 'configuration.yaml not found' line on a haos host is downgraded to a warning carrying the override hint, never a hard error"
    - "Permission preflight probes are read-only except a single touch/rm of a throwaway .haco_wtest dotfile inside the config dir; every failed check yields an exact remediation string"
    - "connect_and_probe composes SSHClient + discover + preflight + run_config_check over ONE session and returns ConnectReport(facts, preflight, check, ready); ready = preflight.ok and check.ok"
    - "CLI turns the report into an exit code (0/1/2) and renders via rich; ConnectionError/AuthError/DiscoveryError are caught and printed as one line, no traceback"

key-files:
  created:
    - "src/haco/check.py - CheckResult, run_config_check"
    - "src/haco/preflight.py - PreflightResult, permission_preflight, _ROOT_BINS"
    - "src/haco/connect.py - ConnectReport, connect_and_probe"
    - "tests/test_check.py - clean pass, error line, nonzero-exit synth, HAOS path-bug demotion"
    - "tests/test_preflight.py - writable+available ok, non-writable names the dir, missing sudo for a root restart"
    - "tests/test_connect.py - healthy host ready, failing preflight/check not ready, ConnectionError propagates, CLI exit codes 0/1/2 + --help"
  modified:
    - "src/haco/cli.py - replaced the 01-01 connect stub with the real command (_password_provider, _render_report, connect)"
    - "src/haco/errors.py - added CheckError, PreflightError"

key-decisions:
  - "run_config_check NEVER raises. A broken check command (nonzero exit, no recognised ERROR line) still yields a non-empty errors list (last output line, or a synthetic 'config check failed (exit N)') so the CLI always has something to show. CheckError/PreflightError exist in the hierarchy for future callers but are intentionally unused by the connect flow - matching the plan's 'do not raise on pf/chk failure'."
  - "Error detection keys on the uppercase tokens ERROR / WARNING (the plan's literal wording) plus '- '/'* ' bullets under a line containing 'fail'. Lowercase matching was rejected because 'Configuration valid! 0 errors' would false-positive."
  - "HAOS path-bug demotion runs BEFORE the ERROR check and continues, so the bug line (which itself contains 'ERROR' and 'no such file') becomes only a warning and does not trigger the synthetic-error fallback."
  - "preflight learns whether the SSH user is root via `id -u` (HostFacts carries no user). _ROOT_BINS = {systemctl, docker, ha}: for those restart binaries, when not root, `sudo -n true` must succeed."
  - "write probe quotes the config dir with shlex.quote and appends /.haco_wtest outside the quotes ('/dir'/.haco_wtest is valid shell) - honours the 'shlex.quote every remote path interpolation' convention."
  - "CLI exit codes: 0 READY, 1 NOT READY, 2 on ConnectionError/AuthError/DiscoveryError AND on a missing/invalid profile (ProfileError) - all message-only, no traceback."
  - "Task 5 (gate) required no code change beyond black reformatting cli.py before its commit; no separate gate commit (same no-op pattern as 01-02 Task 5 / 01-03 Task 4)."

patterns-established:
  - "Boundary error translation continues: discovery/connection errors propagate out of connect_and_probe; preflight/check failures are surfaced as data on ConnectReport."
  - "rich rendering of a resolved-facts Table + preflight findings + check errors/warnings is the connect command's output contract; HostFacts.notes (the HAOS caveat) is printed as a dim note line."

requirements-completed: [CONN-06, CONN-07]

coverage:
  - id: D1
    description: "run_config_check runs the resolved config check once and classifies output into CheckResult (ok only when exit 0 and no error lines); the HAOS ha-core-check path-bug line is a warning, not an error"
    requirement: "CONN-06"
    verification:
      - kind: unit
        ref: "tests/test_check.py#test_clean_check_is_ok, test_error_line_makes_not_ok, test_nonzero_exit_without_error_token_still_not_ok, test_haos_path_bug_line_is_a_warning_not_an_error"
        status: pass
    human_judgment: false
  - id: D2
    description: "permission_preflight verifies write access to the config dir (test -w + touch/rm) and ability to run the restart command (binary on PATH, passwordless sudo when a root-needing binary and non-root user); each failure names the exact remediation"
    requirement: "CONN-07"
    verification:
      - kind: unit
        ref: "tests/test_preflight.py#test_writable_dir_and_available_restart_bin_is_ok, test_non_writable_dir_names_the_dir, test_missing_sudo_for_root_restart_is_not_ok"
        status: pass
    human_judgment: false
  - id: D3
    description: "connect_and_probe opens one SSH session and runs discover -> preflight -> baseline check, returning ConnectReport(ready = preflight.ok and check.ok); a failing preflight or check returns the report with ready=False rather than raising; connection/discovery errors propagate"
    requirement: "CONN-06"
    verification:
      - kind: unit
        ref: "tests/test_connect.py#test_healthy_host_is_ready, test_failing_preflight_is_not_ready, test_failing_check_is_not_ready, test_connection_error_propagates"
        status: pass
    human_judgment: false
  - id: D4
    description: "haco connect NAME [--password-stdin] renders the matrix + preflight + baseline check and sets the process exit code: 0 READY, 1 NOT READY, 2 on connection/auth/discovery failure with no traceback"
    requirement: "CONN-06"
    verification:
      - kind: unit
        ref: "tests/test_connect.py#test_connect_help_documents_name_and_password_stdin, test_connect_exits_zero_when_ready, test_connect_exits_one_when_not_ready, test_connect_exits_two_on_discovery_error"
        status: pass
    human_judgment: false
  - id: D5
    description: "Manual smoke check of `haco connect` against the user's real Home Assistant over SSH: install type / config dir / baseline check / READY verdict match reality"
    verification:
      - kind: manual
        ref: "uv run haco connect hass against live HA OS 192.168.178.22:22951 (root) on 2026-08-30 -> install_type=haos, config_dir=/homeassistant, baseline `ha core check` exit 0, preflight write+restart True, READY, exit 0. Error paths (bad cred, closed port) -> exit 2, message only."
        status: pass
    human_judgment: true
    rationale: "User-verified end-to-end against a live HA OS host. Deliberate broken-config NOT READY path left to unit coverage (tests/test_connect.py, tests/test_check.py) to avoid disturbing the running system."

duration: 25min
completed: 2026-08-29
status: complete
---

# Phase 1 Plan 04: Baseline check + permission preflight + `haco connect` Summary

**`haco connect NAME` now runs the full path end to end: open SSH, discover the install layout, preflight write + restart permissions, run the live baseline `check_config`, and print READY or the exact blocker with a 0/1/2 exit code. All code is committed and the quality gate is green; the plan's manual smoke check against a real Home Assistant is still PENDING USER VERIFICATION.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-08-29 (right after the 01-03 state commit)
- **Completed:** 2026-08-29
- **Tasks:** 5 (Task 5 = quality gate, no code change beyond a black reformat)
- **Files modified:** 8 (3 new modules, 3 new test files, cli.py + errors.py modified)

## Accomplishments

- `src/haco/check.py`: `run_config_check(client, facts) -> CheckResult` (frozen: `ok`, `exit_status`, `errors`, `warnings`, `raw`). Parses `ERROR` / `WARNING` lines and `- ` / `* ` bullets under a `fail`-marked section; `ok` is true only on exit 0 with no errors; a nonzero exit with no recognised error line still produces a non-empty `errors` list. On a `haos` host a `configuration.yaml not found` line is demoted to a warning carrying the `home-assistant/core#156294` override hint and does **not** count as a failure.
- `src/haco/preflight.py`: `permission_preflight(client, facts) -> PreflightResult` (frozen: `ok`, `can_write_config`, `can_restart`, `findings`). Write probe = `test -w <dir>` then a real `touch <dir>/.haco_wtest && rm ...`. Restart probe = first token of `restart_cmd` on `PATH` via `command -v`, and for `systemctl` / `docker` / `ha` when `id -u` != 0, `sudo -n true` must succeed. Each failed check appends its exact remediation string.
- `src/haco/connect.py`: `connect_and_probe(profile, *, password_provider=None) -> ConnectReport` (frozen: `facts`, `preflight`, `check`, `ready`). One `async with SSHClient(...)` session runs `discover` -> `permission_preflight` -> `run_config_check`; `ready = preflight.ok and check.ok`. Does not raise on preflight/check failure; lets `ConnectionError` / `AuthError` / `DiscoveryError` propagate.
- `src/haco/cli.py`: the 01-01 `connect` stub is replaced. `haco connect NAME [--password-stdin]` loads the profile, runs the probe, renders a rich table of `install_type` / `config_dir` / `config_check_cmd` / `restart_cmd` (+ `container_name`, + dim HAOS note), then the preflight findings and the check errors/warnings, then `READY` (green) or `NOT READY` (red). Exit 0 / 1 / 2. `--password-stdin` reads one stdin line as the password provider.
- `src/haco/errors.py`: `CheckError` and `PreflightError` added to the `HacoError` hierarchy (reserved for callers that want a hard failure; the connect flow never raises them).
- Full gate green: `ruff` / `black --check` / `mypy --strict` (21 files) / `pytest -q` — **33 passed** (18 carried + 15 new).

## Task Commits

Each task was committed atomically:

1. **Task 1: baseline config-check runner** - `a6d6670` (feat) - `check.py`, `errors.py`, `tests/test_check.py`
2. **Task 2: permission preflight** - `4115cf5` (feat) - `preflight.py`, `tests/test_preflight.py`
3. **Task 3: connect orchestration** - `284ce56` (feat) - `connect.py`, `tests/test_connect.py`
4. **Task 4: wire `haco connect`** - `947bf77` (feat) - `cli.py`, `tests/test_connect.py`
5. **Task 5: quality gate** - no commit; gate green after Task 4 (black had already reformatted `cli.py` inside the Task 4 commit)

**Plan metadata:** _(docs commit alongside this summary + STATE / ROADMAP / REQUIREMENTS)_

## Files Created/Modified

- `src/haco/check.py` - `CheckResult`, `run_config_check` (baseline `check_config` classifier, HAOS path-bug demotion)
- `src/haco/preflight.py` - `PreflightResult`, `permission_preflight` (write + restart grants)
- `src/haco/connect.py` - `ConnectReport`, `connect_and_probe` (SSH -> discover -> preflight -> check)
- `src/haco/cli.py` - real `haco connect` command (`_password_provider`, `_render_report`, `connect`)
- `src/haco/errors.py` - added `CheckError`, `PreflightError`
- `tests/test_check.py`, `tests/test_preflight.py`, `tests/test_connect.py` - 15 new tests

## Decisions Made

See `key-decisions` in the frontmatter. Highlights:

- **`run_config_check` never raises** - a failing baseline is data on `CheckResult`, consistent with the plan's "do not raise on pf/chk failure". A nonzero exit with no `ERROR` line synthesises one error line so the CLI always shows something (guarded so the demoted HAOS path-bug line does not trigger it).
- **Uppercase `ERROR` / `WARNING` token matching** (plan's literal wording) to avoid `0 errors` false-positives.
- **`id -u` for root detection** because `HostFacts` carries no user; `_ROOT_BINS = {systemctl, docker, ha}` gate the `sudo -n true` check.
- **CLI exit 2 also covers a missing/invalid profile** (`ProfileError`), message-only.

## Deviations from Plan

**None affecting behaviour** - Rules 1-4 not triggered; no bugs, missing critical functionality, blockers, or architectural changes surfaced.

Faithful interpretations (not deviations):

- Task 1 says "Add `CheckError(HacoError)`"; Task 2 says "Add `PreflightError(HacoError)`". Both were added. Neither is raised by the connect flow (the plan explicitly wants `connect_and_probe` not to raise on check/preflight failure, and the CLI only catches `ConnectionError`/`AuthError`/`DiscoveryError`). They stand as hierarchy entries for future callers.
- `check.py` / `preflight.py` / `connect.py` type their `client` parameter as the `CommandRunner` Protocol from 01-03 (not `SSHClient` concretely) so the scripted fakes type-check under `mypy --strict`; `SSHClient` satisfies it structurally in `connect_and_probe`. Same pattern established in 01-03.
- The nonzero-exit-without-`ERROR` fallback (synthesising an error line) is an addition the plan implies via its acceptance criterion "exit nonzero OR an ERROR line -> ok is False and errors is non-empty" - it guarantees the second half of that clause.
- Added CLI-level tests (`typer.testing.CliRunner`) for the exit codes and `--help` on top of the unit tests the plan named, to lock CONN-06/CONN-07 CLI behaviour.

## Issues Encountered

- Typer's rich-formatted `--help` wraps and injects ANSI, so the help assertion strips ANSI and collapses whitespace before matching `password-stdin` / `name`.
- Git reports `LF will be replaced by CRLF` for the new files on this Windows checkout; ruff / black / mypy / pytest are unaffected (same as prior plans).

## Checkpoint: PASSED (user-verified 2026-08-30)

The plan's `checkpoint:human-verify` (`gate="blocking"`) manual smoke check of
`haco connect` against a **real** Home Assistant was run by the user against a
live HA OS box (host `192.168.178.22`, Advanced SSH & Web Terminal add-on on
port 22951, user `root`, password auth via `--password-stdin`).

**Result — `uv run haco connect hass` → exit 0 / READY:**

```
install_type     haos              (correct — the host runs HA OS)
config_dir       /homeassistant    (real HAOS config path; holds configuration.yaml)
config_check_cmd ha core check
restart_cmd      ha core restart
permission preflight  write=True  restart=True
baseline check  exit 0
READY   (exit 0)
```

- Install type autodetected correctly (`ha` on PATH → `haos`).
- `config_dir` resolved to the actual HAOS path via the probe order.
- Baseline `ha core check` ran on the live host and passed (exit 0); the HAOS
  `home-assistant/core#156294` note was shown as advisory, not an error.
- Preflight confirmed the SSH user can write `/homeassistant` and run `ha core restart`.
- `READY` gated on `preflight.ok and check.ok`.

**Error path also confirmed** during setup: wrong username / password → `authentication failed for … ` exit 2; closed SSH port → `could not connect to …:22: [connection refused]` exit 2. Both messages only, no traceback.

Not exercised: the deliberate broken-config `NOT READY` path (step 4 below) — skipped to avoid disturbing the live system; it is covered by `tests/test_connect.py` and `tests/test_check.py` at the unit level.

### Original steps (for reference / re-verification)

Run these from the repo root (`uv` on PATH; Python 3.12 pinned via `.python-version`):

1. **Create a profile for your HA host:**
   ```
   uv run haco profile add hass --host YOUR_HA_IP --user YOUR_SSH_USER --auth key --key-path ~/.ssh/id_ed25519
   ```
   or, for password auth:
   ```
   uv run haco profile add hass --host YOUR_HA_IP --user YOUR_SSH_USER --auth password
   export HACO_SSH_PASSWORD='...'      # or pass --password-stdin and pipe it in
   ```
   If the host key is not already in `~/.ssh/known_hosts`, add it once (e.g. `ssh-keyscan -H YOUR_HA_IP >> ~/.ssh/known_hosts`) - host-key verification is enforced.

2. **Run connect against the healthy config:**
   ```
   uv run haco connect hass
   # or: printf '%s\n' "$SSH_PASSWORD" | uv run haco connect hass --password-stdin
   ```

3. **Confirm the output matches reality:**
   - `install_type` matches your setup (`haos` / `container` / `core`).
   - `config_dir` points at the directory that actually holds your `configuration.yaml`.
   - `config_check_cmd` is the command you would run by hand (`ha core check`, `docker exec <ctr> python -m homeassistant --script check_config -c /config`, or `<venv>/hass --script check_config -c <dir>`).
   - The baseline check result agrees with running that command yourself.
   - `READY` (exit 0) appears only if your config is valid **and** the SSH user can write the config dir **and** run the restart command. Verify the exit code: `echo $?`.
   - If you are on HAOS 2025.11 and see the `home-assistant/core#156294` warning about a missing `configuration.yaml`, set `--config-check-cmd` / `--config-dir` on the profile and re-run.

4. **Break the config on purpose and re-run:**
   - Add an invalid line to a YAML file HA loads (e.g. `configuration.yaml`), then `uv run haco connect hass`.
   - Confirm it prints `NOT READY`, shows the check error text, and exits `1` (not a traceback). Revert the change afterwards.

5. **(Optional) permission failure path:** run as an SSH user without write on the config dir or without passwordless sudo for the restart command; confirm `NOT READY` with a finding naming the missing grant, exit `1`.

## Requirements

- **CONN-06** (baseline `check_config` gate) - code delivered, unit-verified, and confirmed end-to-end against a live HA OS host (baseline `ha core check` exit 0 → READY).
- **CONN-07** (write + restart permission preflight) - code delivered, unit-verified, and confirmed end-to-end (write=True, restart=True on the live host).

## Next Phase Readiness

- Phase 2 (YAML round-trip engine) does not depend on this plan's runtime behaviour; it can start regardless.
- Phase 3 (pull) and Phase 5 (stage/apply) will reuse `connect_and_probe` / `HostFacts` / `PreflightResult` directly.
- **Blocker for marking Phase 1 fully verified:** the `haco connect` smoke check above must be run by the user.

## Self-Check: PASSED

- `src/haco/check.py`, `src/haco/preflight.py`, `src/haco/connect.py` present on disk; `src/haco/cli.py` carries the real `connect` command; `src/haco/errors.py` carries `CheckError` / `PreflightError`.
- `tests/test_check.py`, `tests/test_preflight.py`, `tests/test_connect.py` present.
- Commits `a6d6670`, `4115cf5`, `284ce56`, `947bf77` in `git log`.
- `uv run ruff check .` / `black --check .` / `mypy` / `pytest -q` all exit 0 (33 passed).

---
*Phase: 01-connect-discover*
*Completed (code): 2026-08-29 — manual smoke check PASSED (user-verified against live HA OS) 2026-08-30*
