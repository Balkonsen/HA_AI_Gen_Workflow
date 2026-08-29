# Research: Features

## Table stakes (a HA config optimizer must do these)

- **Connect + pull** the full config tree over SSH/SFTP into a local working copy.
- **Faithful parse** of HA YAML: `!secret`, `!include`, `!include_dir_list`, `!include_dir_merge_list`, `!include_dir_named`, `!include_dir_merge_named`, `!env_var`, `!input`.
- **Config check** against the live HA before proposing anything (baseline must be green).
- **Deterministic cleanup passes**: trailing-whitespace / indentation normalisation, key ordering within known blocks, removal of entities/automations referencing entity_ids that no longer exist, dedup of identical automations/templates, collapse of empty includes.
- **Diff review**: show every proposed change as a unified diff, hunk by hunk, accept/reject/skip each.
- **Staging validation**: never edit live files first; copy to a scratch dir on the host, apply there, run config check there.
- **Apply + version**: write approved hunks to live config, `git add -A && git commit` in a host-side repo with a message naming the changeset.
- **Restart / reload + smoke check**: restart HA (M1) or reload (M2 via API), confirm it came back, confirm entities/automations/dashboards still parse.
- **Rollback**: `git revert`/`git reset --hard` to the previous commit + restart; HA native backup taken before the first apply of a session as a coarse fallback.

## Differentiators (this project's edge)

- **LLM-proposed structural optimizations** (package splitting, blueprint extraction, modernised automation syntax) presented as reviewable diffs, not free-text advice.
- **Redact-on-send**: secrets never leave the host even though a cloud LLM is used.
- **One tool, three install types** (HA OS / Container / Core) via config-driven paths + per-type check/restart commands.
- **Per-apply git history on the host** — granular, greppable, revertible; independent of HA's own backup blobs.

## Anti-features (deliberately NOT building)

- Multi-server fleet management.
- Config authoring from scratch / "smart home wizard".
- Unattended auto-apply (M1 always human-gated; revisit later, do not design it out).
- Re-implementing HA's schema validation — always call HA's own check.
- Editing the HA database, `.storage/`, or UI-managed (non-YAML) config.

## Sources
- https://www.home-assistant.io/docs/configuration/
- https://www.home-assistant.io/actions/homeassistant.reload_all/
