# Phase 1 Context: Connect & Discover

**Source:** inlined (background-session guard blocked the discuss-phase subagent).
Derived from PROJECT.md, REQUIREMENTS.md (CONN-01..07), and .planning/research/.

## Goal restated

A profile-driven SSH connection that knows what kind of Home Assistant it is talking to
and where the config lives, and refuses to proceed if the ground is unsafe.

## Decisions locked for this phase

- **Language/scaffold**: Python 3.12+, `src/haco/` layout, `uv` project, `pyproject.toml`.
  Lint/format/type: Ruff + Black (line length 120) + `mypy --strict`. Tests: `pytest` +
  `pytest-asyncio`. This phase creates the scaffold (plan 01-01).
- **SSH library**: `asyncssh` (async, SFTP + exec in one dep). Not paramiko.
- **Profile storage**: TOML at `~/.config/haco/<name>.toml` (respect `$XDG_CONFIG_HOME`;
  on Windows use `%APPDATA%\haco\`). Contains host, port, user, auth mode, key path,
  and optional path/command overrides. **No password, no key material, no tokens in the
  file** - password is prompted or read from `HACO_SSH_PASSWORD`; key is referenced by path.
- **Config model**: pydantic v2 `HostProfile`.
- **Install types**: `haos` (HA OS / Supervised), `container` (Docker), `core` (venv).
- **Per-type matrix** (defaults; every field overridable in the profile):

  | type | config dir probe order | config check | restart |
  |---|---|---|---|
  | haos | `/homeassistant`, `/config`, `/mnt/data/supervisor/homeassistant` | `ha core check` | `ha core restart` |
  | container | `docker inspect` mount of the HA container -> host path | `docker exec <ctr> python -m homeassistant --script check_config -c /config` | `docker restart <ctr>` |
  | core | `$HOME/.homeassistant`, explicit override | `<venv>/bin/hass --script check_config -c <dir>` | `systemctl restart home-assistant@<user>` (override) |

- **Detection order**: `ha` on PATH -> haos; else `docker` present + an HA container found -> container;
  else `hass` resolvable in a venv -> core; else fail asking for an explicit `install_type` override.
- **Baseline gate (CONN-06)**: run the resolved config-check against LIVE config once at
  connect time. Non-zero exit or parsed errors -> stop with the check output. `check_config`
  had a path bug on HAOS 2025.11 (home-assistant/core#156294) - if `ha core check` reports a
  missing `configuration.yaml` while the file exists at the resolved dir, surface a hint to
  set the `config_dir`/`config_check_cmd` override rather than treating it as a real failure.
- **Permission preflight (CONN-07)**: over SSH, check (a) write access to the config dir
  (`test -w <dir>` + a touch/rm of a temp dotfile), and (b) ability to run the restart
  command (`sudo -n true` if the restart needs sudo, or membership or executability check).
  Fail early with the specific missing grant.

## Assumptions

- One HA host per profile. LAN reachable from the workstation.
- SSH user may be `root` (HAOS add-on) or a normal user (core/container). Handle both.
- Python 3.12 available locally; `uv` installed (plan 01-01 documents the bootstrap).
- No live HA server is available to the planning process; connection code is unit-tested
  against a stub `asyncssh` server / fake transport, and gets a manual smoke check by the
  user against their real HA (checkpoint in 01-04).

## Out of scope for Phase 1

- Pulling the config tree (Phase 3).
- Parsing YAML (Phase 2).
- Any write to HA.
- HA REST/WebSocket API (M2).

## Requirement coverage

| Req | Plan |
|---|---|
| CONN-01 | 01-01 |
| CONN-02, CONN-03 | 01-02 |
| CONN-04, CONN-05 | 01-03 |
| CONN-06, CONN-07 | 01-04 |
