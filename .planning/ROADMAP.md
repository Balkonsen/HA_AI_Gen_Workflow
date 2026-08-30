# Roadmap: HA AI Config Optimizer

## Overview

The rebuild delivers one milestone: a CLI that connects to a live Home Assistant server
over SSH, proposes reviewed optimizations to its YAML config, validates them on a host-side
staging copy, applies and git-commits the approved changes, restarts HA, smoke-checks the
result, and can roll back with one command. Phases build bottom-up: connection and
install-type discovery, then the comment-preserving YAML engine, then the local working copy,
then the rule-based optimizer with per-hunk review, then the staging/apply/version spine,
then the restart/smoke/rollback safety net, and finally the redact-on-send guard with
LLM-proposed diffs. GUI and HA-API reload are explicitly M2.

## Phases

- [x] **Phase 1: Connect & Discover** - SSH connection, auth, HA install-type autodetect, path/command matrix, baseline check (completed 2026-08-30)
- [ ] **Phase 2: YAML Round-Trip Engine** - comment/tag-preserving loader, include graph, touched-only rewrite, idempotency
- [ ] **Phase 3: Pull & Working Copy** - recursive SFTP pull with skip list into isolated local working copies
- [ ] **Phase 4: Rule Optimizer & Diff Review** - deterministic optimization passes and per-hunk accept/reject review loop
- [ ] **Phase 5: Sandbox, Apply & Version** - host staging copy, config check on staging, atomic live apply, host-side git history
- [ ] **Phase 6: Restart, Smoke & Rollback** - pre-apply backup, restart+wait, smoke checks, one-command and automatic rollback
- [ ] **Phase 7: Redact-on-Send & LLM Proposals** - secret redactor with planted-secret test, LLM diff proposals into review loop, full CLI wiring

## Phase Details

### Phase 1: Connect & Discover

**Goal**: A profile-driven SSH connection that knows what kind of HA it is talking to and where the config lives.
**Depends on**: Nothing (first phase)
**Requirements**: CONN-01, CONN-02, CONN-03, CONN-04, CONN-05, CONN-06, CONN-07
**Success Criteria** (what must be TRUE):

  1. haco connect PROFILE opens an SSH session using a key file or a password
  2. The tool prints the detected install type (HA OS/Supervised, Container, or Core venv)
  3. The tool prints the resolved config directory, config-check command, and restart command, honoring profile overrides
  4. The tool runs the live baseline check_config and reports pass/fail
  5. The tool refuses to continue when the baseline fails or the SSH user lacks write/restart permission, with a clear message

**Plans**: 4/4 plans executed (planned 2026-08-29)

Plans:

- [x] 01-01-PLAN.md
- [x] 01-02-PLAN.md
- [x] 01-03-PLAN.md
- [x] 01-04-PLAN.md
- [x] 01-01: Host profile model + local persistence (no secrets committed)
- [x] 01-02: asyncssh connection with key and password auth
- [x] 01-03: Install-type autodetect + path/command matrix with overrides
- [x] 01-04: Baseline check_config runner + permission preflight

### Phase 2: YAML Round-Trip Engine

**Goal**: Load any HA config tree, mutate part of it, and write it back with every untouched byte preserved.
**Depends on**: Phase 1
**Requirements**: YAML-01, YAML-02, YAML-03, YAML-04, YAML-05
**Success Criteria** (what must be TRUE):

  1. The loader parses a real config using HA custom tags (secret, include, and every include_dir variant) without error
  2. Load then dump of an untouched file is byte-identical (comments, quotes, key order, indentation)
  3. The tool reports the include graph from configuration.yaml to every included file
  4. After an edit to one file, only that file is rewritten on disk; sibling files are unchanged
  5. Running analysis twice on the same tree yields zero proposed changes on the second run

**Plans**: 3/4 plans executed (planned 2026-08-30)

Plans:

- [x] 02-01-PLAN.md — Round-trip loader + compose() span index + Wave 0 fixture trees (YAML-01, YAML-02)
- [x] 02-02-PLAN.md — HA-faithful include resolver, ConfigTree, and include graph (YAML-03)
- [x] 02-03-PLAN.md — Mutation API + surgical splice writer, dirty-only atomic writes (YAML-02, YAML-04)
- [ ] 02-04-PLAN.md — No-op stability harness proving D-10's three properties (YAML-05)

### Phase 3: Pull & Working Copy

**Goal**: A faithful local copy of the live config that the engine can parse.
**Depends on**: Phase 1, Phase 2
**Requirements**: PULL-01, PULL-02, PULL-03
**Success Criteria** (what must be TRUE):

  1. haco pull PROFILE recursively copies the HA config directory over SFTP
  2. storage, databases, logs, backups, deps, tts, image, cloud dirs are excluded from the copy
  3. Each run creates an isolated timestamped working copy under ./.haco/work/
  4. The pulled tree loads cleanly through the Phase 2 engine

**Plans**: TBD

Plans:

- [ ] 03-01: Recursive SFTP pull
- [ ] 03-02: Skip-list filtering + timestamped work dirs

### Phase 4: Rule Optimizer & Diff Review

**Goal**: Deterministic optimizations the user can review and approve hunk by hunk - value with no LLM.
**Depends on**: Phase 2, Phase 3
**Requirements**: RULE-01, RULE-02, RULE-03, RULE-04, RULE-05, REVIEW-01, REVIEW-02, REVIEW-03, REVIEW-04
**Success Criteria** (what must be TRUE):

  1. The optimizer flags automations/scripts/scenes referencing entity_ids absent from the live entity list
  2. The optimizer detects byte-equivalent duplicate automations/scripts/templates and offers a merge
  3. Formatting normalization and empty-include collapse are proposed as changes with no semantic effect
  4. Every proposed change is shown as a unified diff grouped by file, and the user can accept, reject, or skip each hunk
  5. Accepted hunks form a changeset with provenance; aborting review writes nothing

**Plans**: TBD

Plans:

- [ ] 04-01: Rule pass framework + edit/rationale model
- [ ] 04-02: Dead-entity, dedup, formatting, empty-include passes
- [ ] 04-03: Unified-diff renderer + per-hunk review loop
- [ ] 04-04: Changeset assembly with provenance

### Phase 5: Sandbox, Apply & Version

**Goal**: Get an approved changeset validated on the host and safely written to live config with git history.
**Depends on**: Phase 4
**Requirements**: STAGE-01, STAGE-02, STAGE-03, STAGE-04, APPLY-01, APPLY-02, APPLY-03, APPLY-04
**Success Criteria** (what must be TRUE):

  1. The tool copies live config to a same-filesystem staging dir on the host and applies the changeset there only
  2. The install-type config-check runs against the staging dir and its errors/warnings are reported
  3. Live config is untouched while staging validation is pending or failing
  4. On staging pass, approved hunks are written to live files atomically
  5. The config dir is a git repo with a scoped ignore file; each apply is one commit and the pre-apply state is recorded as last-known-good

**Plans**: TBD

Plans:

- [ ] 05-01: Host staging copy + changeset apply-to-staging
- [ ] 05-02: Staging config-check runner + result parsing
- [ ] 05-03: Atomic live write
- [ ] 05-04: Host-side git init, scoped ignore, per-apply commit, last-known-good marker

### Phase 6: Restart, Smoke & Rollback

**Goal**: A bad change is caught and undone; a good change is confirmed live.
**Depends on**: Phase 5
**Requirements**: SAFE-01, SAFE-02, SAFE-03, SAFE-04, SAFE-05, SAFE-06, CLI-02
**Success Criteria** (what must be TRUE):

  1. Before the first apply of a session the tool takes an HA backup (supervisor backup on HA OS, config tarball otherwise)
  2. After apply the tool restarts HA with the install-type command and waits until HA is back
  3. The smoke check confirms post-restart config check passes, no new ERROR log lines, and automation/scene/dashboard counts match the pre-apply snapshot
  4. haco rollback PROFILE reverts the config dir to the last-known-good commit and restarts HA
  5. A failed restart or smoke check prompts an automatic rollback; HA native backup restore is documented as the coarse fallback

**Plans**: TBD

Plans:

- [ ] 06-01: Pre-apply backup (supervisor + tarball paths)
- [ ] 06-02: Restart + wait-for-healthy
- [ ] 06-03: Smoke checks + pre/post snapshot diff
- [ ] 06-04: rollback command + auto-rollback on failure

### Phase 7: Redact-on-Send & LLM Proposals

**Goal**: Add LLM-proposed optimizations without ever sending a secret off the host, wired into the same review loop.
**Depends on**: Phase 4, Phase 6
**Requirements**: LLM-01, LLM-02, LLM-03, LLM-04, LLM-05, CLI-01, CLI-03, CLI-04
**Success Criteria** (what must be TRUE):

  1. The redactor strips secret values, inline tokens, latitude/longitude, api_key/password values, webhook ids, and long-lived tokens from LLM-bound content
  2. A planted-secret fixture test proves no secret-shaped value appears in the LLM payload
  3. The LLM backend is provider-selectable (Anthropic or OpenAI) with the API key from env
  4. LLM-returned YAML is diffed against the original and its hunks flow through the Phase 4 review loop; any hunk changing a redacted or secret-shaped value is auto-rejected
  5. haco run PROFILE executes the full loop end to end with rule-only and LLM-included modes selectable by flag, and writes a session log under ./.haco/

**Plans**: TBD

Plans:

- [ ] 07-01: Secret-shape redactor + planted-secret test fixture
- [ ] 07-02: Provider-selectable LLM backend
- [ ] 07-03: LLM YAML-diff proposals into the review loop + secret-change auto-reject
- [ ] 07-04: Full haco run wiring, mode flags, session log

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Connect & Discover | 4/4 | Complete    | 2026-08-30 |
| 2. YAML Round-Trip Engine | 3/4 | In Progress|  |
| 3. Pull & Working Copy | 0/2 | Not started | - |
| 4. Rule Optimizer & Diff Review | 0/4 | Not started | - |
| 5. Sandbox, Apply & Version | 0/4 | Not started | - |
| 6. Restart, Smoke & Rollback | 0/4 | Not started | - |
| 7. Redact-on-Send & LLM Proposals | 0/4 | Not started | - |

---
*Roadmap created: 2026-08-29*
