---
phase: 01-connect-discover
plan: 02
subsystem: ssh
tags: [asyncssh, async, ssh, sftp, host-key-verification, pytest-asyncio]

requires:
  - "01-01: HostProfile model, haco.errors hierarchy"
provides:
  - "haco.ssh.SSHClient - async SSH wrapper (connect / run / sftp / close, async context manager)"
  - "Key-file and password auth from a HostProfile; password sourced from provider / $HACO_SSH_PASSWORD / getpass only"
  - "CmdResult frozen dataclass (exit_status, stdout, stderr)"
  - "Enforced host-key verification (known_hosts=None means asyncssh default, never 'trust any')"
  - "In-process asyncssh test server fixture (tests/support/ssh_server.py)"
  - "haco.errors: ConnectionError / AuthError / HostKeyError / RemoteCommandError"
affects: [01-03, 01-04, discover, connect, preflight, baseline-check, pull, apply]

actuals:
  tokens: 33000
  tasks: 5
  commits: 6

tech-stack:
  added: []
  patterns:
    - "One reusable async SSH connection wrapper; all later phases run over it"
    - "asyncssh exceptions translated to the haco.errors family at the boundary"
    - "Secrets never touch HostProfile: password via provider/env/getpass at connect time"
    - "Test SSH server on 127.0.0.1:0 with ephemeral host + client keys; known_hosts file emitted for the run"

key-files:
  created:
    - "src/haco/ssh.py - SSHClient wrapper + CmdResult"
    - "tests/support/ssh_server.py - in-process asyncssh server fixture (SSHServerInfo)"
    - "tests/test_ssh.py - key auth, password (env + provider), bad password, bad key, run nonzero, host-key regression, no-password-field"
  modified:
    - "src/haco/errors.py - added ConnectionError / AuthError / HostKeyError / RemoteCommandError"
    - "src/haco/models.py - corrected known_hosts docstring semantics"
    - "tests/conftest.py - registers the ssh_server fixture"

key-decisions:
  - "Only forward known_hosts to asyncssh when the profile names a file; otherwise omit the kwarg so asyncssh keeps its verifying default. Passing known_hosts=None DISABLES verification (MITM) - this was the CRITICAL security finding on the first pass and is now covered by test_unknown_host_key_rejected."
  - "resolve_password order: explicit provider -> $HACO_SSH_PASSWORD -> getpass (TTY only) -> AuthError. Never the profile file."
  - "run() returns CmdResult and only raises RemoteCommandError when check=True; a nonzero exit is data, not an exception."

patterns-established:
  - "asyncssh.PermissionDenied -> AuthError; asyncssh.HostKeyNotVerifiable -> HostKeyError; OSError/asyncssh.Error -> haco ConnectionError"
  - "Test server exposes known_hosts_path so connection tests verify the real host key rather than disabling the check"

requirements-completed: [CONN-02, CONN-03]

coverage:
  - id: D1
    description: "Key-file auth opens a session from a HostProfile(auth=key, key_path=...)"
    requirement: "CONN-02"
    verification:
      - kind: unit
        ref: "tests/test_ssh.py#test_key_auth"
        status: pass
    human_judgment: false
  - id: D2
    description: "Password auth from $HACO_SSH_PASSWORD and from an explicit provider; never from the profile file"
    requirement: "CONN-03"
    verification:
      - kind: unit
        ref: "tests/test_ssh.py#test_password_auth_env, test_password_auth_provider, test_profile_never_holds_password"
        status: pass
    human_judgment: false
  - id: D3
    description: "Wrong key / wrong password produce AuthError, not a traceback"
    requirement: "CONN-02, CONN-03"
    verification:
      - kind: unit
        ref: "tests/test_ssh.py#test_bad_key, test_bad_password"
        status: pass
    human_judgment: false
  - id: D4
    description: "run(cmd) returns exit status/stdout/stderr; nonzero exit is not an exception unless check=True"
    requirement: "CONN-02"
    verification:
      - kind: unit
        ref: "tests/test_ssh.py#test_run_nonzero"
        status: pass
    human_judgment: false
  - id: D5
    description: "Host-key verification is enforced; known_hosts=None does not trust unknown hosts"
    requirement: "CONN-02"
    verification:
      - kind: unit
        ref: "tests/test_ssh.py#test_unknown_host_key_rejected"
        status: pass
    human_judgment: false

duration: 20min
completed: 2026-08-29
status: complete
---

# Phase 1 Plan 02: Authenticated SSH session Summary

**`haco.ssh.SSHClient` - a reusable async asyncssh wrapper (connect / run / sftp / close, async context manager) with key and password auth from a `HostProfile`, enforced host-key verification, and an in-process test SSH server.**

## Performance

- **Tasks:** 5 (Task 5 = quality gate)
- **Commits:** 6 (4 task commits + 1 CRITICAL security fix + this docs commit)
- **Interrupted once** by a session rate limit after Task 4; resumed to finish the gate, the security fix, and this summary.

## Accomplishments

- `src/haco/ssh.py`: `SSHClient(profile, *, password_provider=None)` with `async connect()`, `async run(cmd, *, check=False) -> CmdResult`, `sftp()` accessor, `async close()`, and `__aenter__` / `__aexit__`.
- Auth: `client_keys=[key_path]` for `auth=key`; for `auth=password` the value comes from `password_provider()` -> `$HACO_SSH_PASSWORD` -> `getpass` (TTY only), never the profile.
- Error translation at the asyncssh boundary: `PermissionDenied -> AuthError`, `HostKeyNotVerifiable -> HostKeyError`, `OSError` / `asyncssh.Error -> haco.errors.ConnectionError`.
- `haco.errors` extended: `ConnectionError`, `AuthError(ConnectionError)`, `HostKeyError(ConnectionError)`, `RemoteCommandError`.
- `tests/support/ssh_server.py`: an `asyncssh` server on `127.0.0.1:0` with generated ed25519 host + client keys, password `test-pw`, a 3-entry command dispatch, and a chrooted SFTP subsystem. Exposes `SSHServerInfo(host, port, client_key_path, good_password, known_hosts_path)`.
- 13 tests green (8 for this plan + 5 carried from 01-01).

## Task Commits

1. **Task 1: extend errors** - `9e36797` (feat)
2. **Task 2: SSHClient wrapper** - `0514c28` (feat)
3. **Task 3: in-process test SSH server** - `869e2b4` (test)
4. **Task 4: connection tests** - `9c018e1` (test)
5. **Security fix (CRITICAL, from commit review): enforce host-key verification** - `f3a7287` (fix)
6. **Task 5: quality gate** - clean at `f3a7287`; no code change needed beyond the security fix. **Plan metadata:** _(this docs commit)_

## Deviations from Plan

### Security fix - CRITICAL (commit review finding)

**Missing host-key verification / MITM via `known_hosts=None`**
- **Found during:** automated commit security review of `0514c28`
- **Issue:** `connect()` built its options dict with `"known_hosts": profile.known_hosts`, and `HostProfile.known_hosts` defaults to `None`. Passing `known_hosts=None` to `asyncssh.connect` **disables** host-key checking entirely - any server on the LAN could impersonate the HA host and receive the SSH session (and, in later phases, config writes).
- **Fix (`f3a7287`):**
  - `ssh.py` - only add `known_hosts` to the options dict when `profile.known_hosts is not None`; otherwise omit it so asyncssh keeps its verifying default (`~/.ssh/known_hosts` + system files).
  - `models.py` - corrected the `known_hosts` field docstring to state that `None` means "use asyncssh's default", not "trust any host key".
  - `tests/support/ssh_server.py` - the fixture now writes a `known_hosts` file for its ephemeral host key and exposes `known_hosts_path`.
  - `tests/test_ssh.py` - the connection-success tests point `known_hosts` at that file; added `test_unknown_host_key_rejected` asserting a profile with `known_hosts=None` still refuses the untrusted test host key.
- **Verification:** `uv run pytest -q` -> 13 passed; full gate green.

### Process

- **Rate-limit interruption after Task 4.** The first executor hit a session limit mid-plan. Tasks 1-4 were already committed; the orchestrator finished Task 5, applied the security fix, and wrote this summary directly. No work lost, no duplicate commits.

## Issues Encountered

- Git reports `LF will be replaced by CRLF` for the new files on this Windows checkout; ruff / black / mypy / pytest are unaffected.

## Next Phase Readiness

- `01-03` (install-type discovery) can drive `SSHClient.run` through a scripted fake and consume `CmdResult`.
- `01-04` composes `SSHClient` with discover / preflight / baseline-check.
- No blockers.

## Self-Check: PASSED

- `src/haco/ssh.py`, `tests/support/ssh_server.py`, `tests/test_ssh.py` present.
- Commits `9e36797`, `0514c28`, `869e2b4`, `9c018e1`, `f3a7287` in `git log`.
- `uv run ruff check .` / `black --check .` / `mypy` / `pytest -q` all exit 0 (13 passed).

---
*Phase: 01-connect-discover*
*Completed: 2026-08-29*
