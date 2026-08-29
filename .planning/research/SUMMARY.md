# Project Research Summary

## Key Findings

**Stack:** Python 3.12+ with pydantic v2 + `mypy --strict`. `ruamel.yaml` (round-trip mode)
is mandatory and is the reason the language is Python — register HA custom-tag
constructors/representers so `!secret`/`!include*` survive rewrite. `asyncssh` for
SSH/SFTP/exec. `Typer` + `rich` for the CLI and diff rendering. `anthropic`/`openai`
SDKs behind a swappable `LLMBackend`. Shell out to the `git` binary on the host rather
than GitPython. Tooling: `uv`, `pytest`+`pytest-asyncio`, Ruff + Black(120) + mypy + bandit.

**Table stakes:** connect+pull over SFTP; faithful HA-tag parse; baseline config check;
deterministic cleanup passes (dead-entity removal, dedup, formatting, include collapse);
per-hunk diff review; host-side staging + validate before live; per-apply git commit;
restart + smoke check; git-based rollback with HA backup as coarse fallback.

**Differentiators:** LLM structural optimizations delivered as reviewable diffs (not prose);
redact-on-send so secrets never leave the host; one tool across HA OS / Container / Core
via config-driven paths and per-type check/restart commands; granular per-apply git history
on the host.

**Watch out for:**
- HA custom tags crash naive YAML loaders; ruamel silently reformats untouched files
  (only rewrite files with an approved hunk; keep `preserve_quotes`, match 2-space indent).
- `hass` CLI is usually absent on HA OS SSH — use `ha core check` (had a path bug in
  2025.11, #156294). Config check is syntax/schema only, not behaviour — smoke tests +
  human confirm still required.
- Redaction must cover inline tokens, lat/long, api_key/password, webhook ids — not just
  `!secret`. Test with a planted-secret fixture asserting nothing leaks to the LLM payload.
- M1 is SSH-only, so reload-without-restart is impossible — full restart (10-60s downtime),
  reload is an explicit M2 feature needing the HA API.
- Git repo in the config dir needs a scoped `.gitignore` (`.storage/`, `*.db*`, logs,
  `backups/`, `deps/`, `tts/`). SSH user needs write + restart permission (sudo?) — detect early.
- Never touch `.storage/`; never re-implement HA schema validation.

## Implications for Roadmap

1. **Foundation / connect+discover** must come first: SSH profile, install-type autodetect,
   path/command matrix, baseline config check. Nothing else works without it.
2. **YAML engine** is a standalone high-risk phase: round-trip loader with all HA tags,
   include-graph builder, "rewrite only touched files" guarantee, idempotency test harness.
3. **Pull + local working copy** with the correct skip list.
4. **Rule-based optimizer + per-hunk review CLI** — deliverable value without any LLM.
5. **Staging + validate + apply + git commit + restart + smoke + rollback** — the safety
   spine; can be built against rule-pass output before the LLM exists.
6. **Redact-on-send + LLM diff proposals** — layered on last; depends on the review loop
   and the redactor test fixture.
7. GUI and HA-API reload are out of scope for M1 (M2).

## Sources
- https://www.home-assistant.io/docs/tools/check_config/
- https://www.home-assistant.io/docs/configuration/
- https://www.home-assistant.io/actions/homeassistant.reload_all/
- https://github.com/home-assistant/core/issues/156294
- https://pypi.org/project/ruamel.yaml/
- https://elegantnetwork.github.io/posts/comparing-ssh/
- https://github.com/ronf/asyncssh
