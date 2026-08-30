# haco - HA AI Config Optimizer

A local-network tool that connects directly to a running Home Assistant server over
SSH, analyzes its full YAML configuration, proposes optimizations from deterministic
rule passes and a cloud LLM, and applies the changes you approve - validated on a
host-side staging copy first, every apply git-committed, with one-command rollback.

This is a ground-up rewrite of an earlier project. Milestone 1 is CLI-only, SSH-only.

## Status

Phase 1 (Connect & Discover) - in progress. Implemented so far:

- `HostProfile` model and local, **secret-free** profile storage (TOML under the user
  config dir: `~/.config/haco/` on POSIX, `%APPDATA%\haco\` on Windows).
- CLI skeleton (`haco profile add/list/show`); `haco connect` is stubbed until plan 01-04.

Profiles never contain a password, private-key bytes, or a token. Passwords are
prompted or read from `HACO_SSH_PASSWORD`; keys are referenced by path.

## Requirements

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/)

## Quickstart

```bash
# install dependencies into an isolated environment
uv sync

# define a host profile (stored locally, no secrets written)
uv run haco profile add hass-lab --host 10.0.0.5 --user root \
    --key-path ~/.ssh/id_ed25519 --install-type haos

uv run haco profile list
uv run haco profile show hass-lab

# connect (implemented in plan 01-04)
uv run haco connect hass-lab
```

## Development

```bash
uv run ruff check .
uv run black --check .
uv run mypy
uv run pytest -q
```
