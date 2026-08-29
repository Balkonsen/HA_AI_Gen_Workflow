# Onboarding Summary

## Project State
- PROJECT.md: present
- REQUIREMENTS.md: present (47 v1 requirements, all mapped)
- ROADMAP.md: present (7 phases)
- STATE.md: present

## Codebase Context
- Brownfield repo: yes (full rewrite - no v1 code carried forward)
- Map readiness: complete
- Codebase map: .planning/codebase/ (7 docs: STACK, ARCHITECTURE, STRUCTURE, CONVENTIONS, TESTING, INTEGRATIONS, CONCERNS)
- Fast map available: yes

## Docs Context
- Existing ADR/PRD/SPEC/RFC candidates: 0

## What Was Decided
- Rebuild the stalled HA tooling project as "HA AI Config Optimizer": a local-network CLI
  that edits a live Home Assistant config directly over SSH - no import/export.
- Stack: typed Python 3.12+ (ruamel.yaml round-trip is the deciding constraint), asyncssh,
  Typer/rich, Anthropic/OpenAI SDKs.
- Safety spine: host-side staging copy validated with the install-type config check,
  per-apply git commit on the host, restart + smoke test, git rollback with HA backup fallback.
- Redact-on-send: secrets never leave the host despite a cloud LLM.
- M1 = full CLI loop, SSH-only. Web GUI and HA REST/WebSocket API + reload-without-restart are M2.

## Recommended Next Step
- /gsd-manager   (or: /gsd-plan-phase 1 to start Phase 1 - Connect & Discover)
