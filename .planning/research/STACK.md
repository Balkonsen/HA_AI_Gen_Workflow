# Research: Stack

**Domain:** Local-network Home Assistant config optimizer (Python CLI)
**Milestone:** Greenfield rewrite (M1)

## Recommended stack (2026)

| Concern | Choice | Rationale | Confidence |
|---|---|---|---|
| Language | Python 3.12+ | HA is Python; tag semantics + entity model map 1:1; LLM SDKs native | High |
| Typing | pydantic v2 + `mypy --strict` | Fixes the loose structure that stalled v1 | High |
| YAML round-trip | `ruamel.yaml` (typ='rt') | Only mature lib preserving comments, key order, anchors through load->mutate->dump. Register `!secret` / `!include` / `!include_dir_*` as custom constructors/representers so they survive rewrite | High |
| SSH + SFTP + exec | `asyncssh` | Modern async, strong SFTP, single dependency. paramiko is sync-only and considered less maintained for this use | High |
| CLI | `Typer` (built on Click) | Type-hint driven, subcommands, good help; pairs with `rich` for diff rendering | High |
| Diff / hunk review | stdlib `difflib` for unified diffs; `rich` for colourised hunks; custom per-hunk accept/reject prompt loop | No good turnkey "interactive hunk picker" lib for Python; build a thin one over `difflib` | Medium |
| LLM | `anthropic` + `openai` SDKs behind a small `LLMBackend` protocol | User chose direct API; keep provider swappable for later local option | High |
| Git on host | invoke `git` over SSH exec (not GitPython on the host) | Host may lack Python git bindings; `git` binary is universal. Local side can use plain subprocess too | High |
| Config check | per-install command (see ARCHITECTURE) | `hass --script check_config` (Core venv), `ha core check` (HA OS/Supervised), `python -m homeassistant --script check_config` (Container) | High |
| Packaging | `uv` project + `pipx`/`uvx` entry point; optional container image | Python packaging is the weak spot; target user runs HA + SSH so pipx is acceptable | Medium |
| Test | `pytest`, `pytest-asyncio`, fixtures with a sample HA config tree; mock SSH with an in-process `asyncssh` server or a fake transport | Matches old repo's CI expectations | High |
| Quality gate | Black (120), Ruff (replaces flake8+isort), mypy strict, bandit | Ruff is the current standard; drop flake8/pylint | High |

## What NOT to use

- **PyYAML / `yaml.safe_load`** — destroys comments and formatting on dump. Disqualified.
- **paramiko** — sync-only; would force threads for concurrent SFTP. Only revisit if asyncssh blocks on a needed feature.
- **GitPython on the HA host** — extra dependency to install on a locked-down appliance; shell out to `git` instead.
- **Go / Rust / TS** — no comment-preserving YAML round-tripper; rejected in PROJECT.md.

## Sources
- https://www.home-assistant.io/docs/tools/check_config/
- https://pypi.org/project/ruamel.yaml/
- https://elegantnetwork.github.io/posts/comparing-ssh/
- https://github.com/ronf/asyncssh
