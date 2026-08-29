# Research: Pitfalls

## YAML round-trip
- **HA custom tags crash a naive loader.** Must register constructors + representers for every `!secret`, `!include*`, `!env_var`, `!input` before parsing. Round-trip them as opaque tagged scalars/sequences so they re-emit byte-identical. Warning sign: `could not determine a constructor for the tag '!include'`.
- **ruamel reformats untouched files subtly** (quote style, flow vs block, indent width) if you load+dump the whole tree. Mitigation: only rewrite files that actually have an approved hunk; for those, diff carefully and keep ruamel's `preserve_quotes=True`, explicit `map_indent`/`sequence_indent`/`offset` matching HA's 2-space style.
- **Anchors/aliases (`&x` / `*x`)** across `!include` boundaries don't resolve — HA merges post-include. Don't try to inline includes.

## Staging validation
- **`hass` is often absent on HA OS SSH.** Use `ha core check`; it had a path bug in 2025.11 (#156294) — pin/verify the command per HA version, and fall back to restarting into the staging dir only as a last resort.
- **Config check validates syntax + schema, not runtime behaviour.** A green check can still break automations logically. That's why smoke tests + human confirm are required before keeping the commit.
- **Staging dir must sit on the same filesystem** as live config for atomic rename on apply, and check must run with the staging path as `-c`.

## Secrets
- **Redaction must cover more than `!secret`.** Inline tokens, `latitude`/`longitude`, `api_key:`, `password:`, MAC/IP, webhook ids, long-lived tokens in `configuration.yaml`. Build an allowlist-of-shapes redactor; test it with a fixture full of planted secrets and assert none appear in the LLM payload.
- **LLM echo-back.** The model may return a secret it inferred or a placeholder mismatch. Re-map placeholders deterministically and reject any hunk whose non-placeholder secret-shaped content changed.

## Apply / restart / rollback
- **Full restart is the only SSH-only option in M1** (reload services need the API). Budget 10-60s downtime; warn the user. Reload-without-restart is an explicit M2 feature.
- **Git repo in the config dir** can collide with HA writing `.storage/` and logs — add a scoped `.gitignore` (`.storage/`, `*.db*`, `*.log`, `backups/`, `deps/`, `tts/`, `image/`, `.cloud/`).
- **Permissions**: files may be owned by root or the HA user; the SSH user needs write + ability to run the restart command (sudo?). Detect and fail early with a clear message.
- **HA native backup** on HA OS is `ha backups new --name ...`; on Container/Core there is no supervisor — fall back to a tarball of the config dir.

## Process
- **Don't re-implement HA schema validation** — always shell out to HA's own checker.
- **Don't touch `.storage/`** (UI-managed config, registries) — YAML-only scope.
- **Idempotency**: re-running analyze on an already-optimised tree must produce zero hunks, or the review loop never converges.

## Sources
- https://github.com/home-assistant/core/issues/156294
- https://www.home-assistant.io/docs/tools/check_config/
- https://www.home-assistant.io/docs/configuration/
