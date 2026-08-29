# Research: Architecture

## Pipeline (M1, CLI, SSH-only)

```
connect -> discover -> pull -> parse -> analyze -> propose -> review -> stage -> validate -> apply -> commit -> restart -> smoke -> [rollback]
```

| Stage | Module | Notes |
|---|---|---|
| connect | `haco.ssh` | asyncssh; key or password; host/port/user from profile |
| discover | `haco.host` | detect install type + config dir + check/restart commands |
| pull | `haco.sync` | SFTP recursive copy of config dir -> local `./.haco/work/<ts>/`; skip `.storage/`, `*.db`, `backups/`, `deps/`, `tts/` |
| parse | `haco.yaml` | ruamel round-trip loader with HA tag constructors; build a file map (path -> CommentedMap/Seq) |
| analyze | `haco.rules` | ordered rule passes, each yields proposed edits as (path, old_node, new_node) |
| propose | `haco.llm` | redact -> send config slices -> parse returned YAML -> diff against original -> proposed edits |
| review | `haco.review` | render unified diff per file, iterate hunks, accept/reject/skip; assemble an approved changeset |
| stage | `haco.stage` | SFTP-copy live config dir -> `<config>/../haco-staging/` on host; apply approved hunks there |
| validate | `haco.check` | run per-type check command against the staging dir; parse pass/fail + messages |
| apply | `haco.apply` | write approved hunks to live files (atomic: temp + rename) |
| commit | `haco.vcs` | `git init` once in config dir if absent; `git commit -am` per apply; tag last-known-good |
| restart | `haco.host` | per-type restart; poll until HA process/container is back |
| smoke | `haco.smoke` | re-run config check on live; grep logs for new ERROR/WARNING; count parsed automations/scenes/dashboards vs pre-apply snapshot |
| rollback | `haco.vcs` + host | `git reset --hard <last-good>` (or `git revert`) + restart; HA native backup restore as fallback |

## Install-type matrix (discover stage)

| Type | Config dir (typical) | Config check | Restart | Detect by |
|---|---|---|---|---|
| HA OS / Supervised | `/homeassistant` or `/config` (via SSH add-on); real path `/mnt/data/supervisor/homeassistant` | `ha core check` | `ha core restart` | `ha` binary present; `/usr/bin/ha` |
| Container (Docker) | bind-mounted volume, e.g. `/opt/homeassistant/config` | `docker exec <ctr> python -m homeassistant --script check_config -c /config` | `docker restart <ctr>` | docker present + HA container found |
| Core (venv) | `~/.homeassistant` or explicit | `<venv>/bin/hass --script check_config -c <dir>` | `systemctl restart home-assistant@<user>` or process supervisor | `hass` on PATH in a venv |

Paths and commands are **config-driven with autodetect fallback** — the profile can override every field.

## Key abstractions

- **HostProfile** — connection + install-type + path/command overrides (pydantic model, persisted to `~/.config/haco/<name>.toml`, no secrets committed).
- **ConfigTree** — in-memory map of file path -> ruamel node, plus the include graph.
- **Edit** — `(file, anchor, before, after, source: rule|llm, rationale)`.
- **Changeset** — ordered list of approved Edits + provenance; serialisable for audit.
- **Validator** — wraps the per-type check command; returns `CheckResult(ok, errors, warnings)`.

## State

Mostly stateless per run. Durable state: local `./.haco/` (work copies, session log, last changeset) and the host-side git repo in the config dir. `~/.config/haco/` holds host profiles.

## Sources
- https://www.home-assistant.io/docs/configuration/
- https://github.com/home-assistant/core/issues/156294
- https://community.home-assistant.io/t/how-do-i-get-to-the-config-folder-via-the-console-of-the-haos-vm/299718
