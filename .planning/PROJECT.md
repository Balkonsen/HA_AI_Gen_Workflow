# HA AI Config Optimizer

## What This Is

A rebuild of a prior Home Assistant tooling project that never reached a functional
state. The rewrite is a local-network tool that connects directly to a running Home
Assistant server over SSH, analyzes its full YAML configuration (including dashboards),
proposes optimizations from both deterministic rule passes and a cloud LLM, and applies
the changes the user approves — validated on a host-side staging copy first, every apply
git-committed, with one-command rollback. It replaces the old export -> sanitize ->
generate -> validate -> import file-shuffling workflow with direct access.

## Core Value

Safely apply reviewed optimizations to a live Home Assistant config over the local
network, with one-command rollback — no import/export cycle.

## Requirements

### Validated

<!-- v1 never reached a functional state; nothing is proven. -->

(None yet — ship to validate)

### Active

- [ ] Connect to a local-network HA server over SSH (key or password auth)
- [ ] Support HA OS / Supervised, HA Container, and HA Core layouts via config-driven paths
- [ ] Pull the live config tree into a local working copy (configuration.yaml, packages, includes, helpers, scripts, scenes, automations, Lovelace/dashboard YAML)
- [ ] Round-trip YAML edits that preserve comments, anchors, and HA custom tags (!secret, !include, !include_dir_*)
- [ ] Rule-based optimization passes: dedup, dead-entity removal, formatting normalization, structural split
- [ ] LLM-proposed optimization diffs via direct Anthropic / OpenAI API
- [ ] Redact-on-send guard: strip !secret values, tokens, latitude/longitude, API keys from every LLM payload; real files never leave the host
- [ ] Interactive per-hunk diff review in the CLI
- [ ] Sandbox: apply the approved changeset to a staging copy on the HA host, validate with `hass --script check_config`
- [ ] Apply to live config only after staging passes and the user approves
- [ ] Git-commit every apply in a host-side config repo (per-apply granular history)
- [ ] Post-apply smoke tests: entities resolve, automations parse, dashboards render; HA restarts clean
- [ ] Rollback: git revert to last-known-good + reload; HA native backup as the coarse safety net
- [ ] CLI covers the full loop end to end (connect -> optimize -> review -> apply -> rollback)

### Out of Scope

- Multi-server / fleet management — one HA instance per run; not orchestrating many homes
- HA REST / WebSocket API integration — deferred to M2; M1 is SSH-only
- Web GUI — deferred to M2; M1 is CLI-only
- v1 import/export file workflow — replaced by direct SSH access
- v1 encrypted secrets vault + placeholder round-trip — replaced by redact-on-send
- Config authoring from scratch — optimizes existing config, not a "build my smart home" wizard

## Context

- Full rewrite of an existing Python project (bin/ services: export, secret-sanitize,
  AI-context-gen, validate, import) that stalled before working. Only domain knowledge and
  patterns carry forward — no old code. Prior codebase map preserved in .planning/codebase/.
- Runs on the user's Windows workstation; targets a Linux Home Assistant host on the LAN.
- HA config YAML uses custom tags (!secret, !include, !include_dir_merge_list, etc.) that
  standard YAML parsers mishandle. Faithful round-trip on rewrite is a hard requirement —
  this is the single biggest constraint on stack choice.
- The old repo has CI on GitHub Actions (pytest matrix, Black 120-col, flake8, mypy, bandit);
  the rewrite keeps an equivalent quality gate.

## Constraints

- **Tech stack**: Python 3.12+, strict typing (pydantic v2, mypy --strict) — chosen because
  ruamel.yaml is the only mature comment/anchor-preserving YAML round-tripper, HA itself is
  Python (tag semantics, `hass --script check_config`, entity model map 1:1), and the LLM SDKs
  are Python-native. Go / Rust / TypeScript were rejected specifically on YAML round-trip fidelity.
- **YAML handling**: must preserve comments, anchors, and tag structure across read -> edit -> write.
- **Security**: no real secret material in any outbound LLM request (redact-on-send is mandatory).
- **Access**: SSH only for M1 (asyncssh, SFTP + exec); HA REST/WebSocket API is M2+.
- **Safety**: no change reaches live config without passing host-side staging validation AND
  explicit per-hunk user approval.
- **Compatibility**: HA OS / Supervised, HA Container, HA Core — path-layout differences
  abstracted behind config.
- **Distribution**: packaged via uv / pipx or a container image.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Full rewrite in typed Python 3.12+ | v1 stalled; ruamel.yaml round-trip has no peer in Go/Rust/TS; HA ecosystem alignment | — Pending |
| Direct SSH access replaces import/export | Removes the manual file-shuffle that made v1 unusable | — Pending |
| Redact-on-send instead of a secrets vault | Keeps secrets on the host while still enabling a cloud LLM; far less machinery | — Pending |
| Git-on-host + HA native backup for rollback | Granular per-apply revert, with a coarse safety net | — Pending |
| Staging copy on the HA host as the sandbox | Validates with the real `hass --script check_config` before live is touched | — Pending |
| M1 = CLI full loop, SSH only; GUI + HA API = M2 | Narrowest path to a first functional state | — Pending |
| Rule passes + LLM diffs, user approves each hunk | Determinism where possible, AI where it adds value, human gate always | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-08-29 after initialization*
