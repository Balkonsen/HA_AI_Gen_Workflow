# Requirements: HA AI Config Optimizer

**Defined:** 2026-08-29
**Core Value:** Safely apply reviewed optimizations to a live Home Assistant config over the local network, with one-command rollback — no import/export cycle.

## v1 Requirements

Milestone 1 = full optimize loop in the CLI, SSH-only.

### Connection & Host (CONN)

- [x] **CONN-01**: User can define a host profile (hostname, port, SSH user) stored locally, no secrets committed
- [x] **CONN-02**: Tool connects over SSH using a key file
- [x] **CONN-03**: Tool connects over SSH using a password when no key is available
- [x] **CONN-04**: Tool autodetects the HA install type (HA OS/Supervised, Container, Core venv)
- [x] **CONN-05**: Tool resolves the config directory, config-check command, and restart command for the detected install type, with per-field profile overrides
- [x] **CONN-06**: Tool runs a baseline `check_config` on the live host and refuses to proceed if the baseline is already failing
- [x] **CONN-07**: Tool verifies the SSH user has write access to the config dir and permission to run the restart command, failing early with a clear message

### Sync (PULL)

- [ ] **PULL-01**: Tool recursively pulls the HA config directory to a local working copy over SFTP
- [ ] **PULL-02**: Pull skips `.storage/`, `*.db*`, `*.log`, `backups/`, `deps/`, `tts/`, `image/`, `.cloud/`
- [ ] **PULL-03**: Each run writes an isolated timestamped working copy under `./.haco/work/`

### YAML Engine (YAML)

- [x] **YAML-01**: Loader parses HA custom tags (`!secret`, `!include`, `!include_dir_list`, `!include_dir_merge_list`, `!include_dir_named`, `!include_dir_merge_named`, `!env_var`, `!input`) without error
- [ ] **YAML-02**: Load -> dump of an untouched file is byte-identical (comments, quote style, key order, indentation preserved) — _diagnostic canary done in 02-01; untouched-file-not-rewritten guarantee lands with the 02-03 writer_
- [ ] **YAML-03**: Tool builds the include graph linking configuration.yaml to every included file
- [ ] **YAML-04**: Only files containing an approved change are rewritten; all others are left untouched on disk
- [ ] **YAML-05**: Re-running analysis on an already-optimized tree produces zero proposed changes (idempotent)

### Rule Optimizer (RULE)

- [ ] **RULE-01**: Pass removes automations/scripts/scenes/customizations referencing entity_ids not present in the live entity list
- [ ] **RULE-02**: Pass detects and offers to merge byte-equivalent duplicate automations/scripts/templates
- [ ] **RULE-03**: Pass normalizes formatting (indentation, trailing whitespace, key ordering within known blocks) without semantic change
- [ ] **RULE-04**: Pass collapses empty or dead `!include` targets
- [ ] **RULE-05**: Each rule emits its changes as discrete, reviewable edits with a rationale string

### Diff Review (REVIEW)

- [ ] **REVIEW-01**: Every proposed change is shown as a unified diff, grouped by file
- [ ] **REVIEW-02**: User accepts, rejects, or skips each hunk individually
- [ ] **REVIEW-03**: Accepted hunks are assembled into a changeset with provenance (rule vs LLM, rationale)
- [ ] **REVIEW-04**: User can abort review with no changes written

### Sandbox & Validate (STAGE)

- [ ] **STAGE-01**: Tool copies the live config dir to a staging dir on the HA host, on the same filesystem
- [ ] **STAGE-02**: Approved changeset is applied to the staging copy only
- [ ] **STAGE-03**: Tool runs the install-type config-check command against the staging dir and parses errors/warnings
- [ ] **STAGE-04**: Live config is never modified while staging validation is pending or failing

### Apply & Version (APPLY)

- [ ] **APPLY-01**: Tool initializes a git repo in the config dir on first apply, with a scoped `.gitignore`
- [ ] **APPLY-02**: Approved changeset is written to live files atomically (temp + rename)
- [ ] **APPLY-03**: Each apply produces one git commit on the host naming the changeset
- [ ] **APPLY-04**: The pre-apply state is tagged/recorded as last-known-good

### Restart, Smoke & Rollback (SAFE)

- [ ] **SAFE-01**: Before the first apply of a session, tool takes an HA backup (supervisor backup on HA OS, config tarball otherwise)
- [ ] **SAFE-02**: After apply, tool restarts HA using the install-type restart command and waits until HA is back
- [ ] **SAFE-03**: Smoke check confirms post-restart config check passes, no new ERROR lines in the log, and automation/scene/dashboard counts match the pre-apply snapshot
- [ ] **SAFE-04**: `haco rollback` reverts the config dir to the last-known-good commit and restarts HA
- [ ] **SAFE-05**: If restart or smoke check fails, tool prompts to roll back automatically
- [ ] **SAFE-06**: HA native backup restore is available as a documented coarse fallback

### AI Proposals (LLM)

- [ ] **LLM-01**: Redactor strips `!secret` values, inline tokens, `latitude`/`longitude`, `api_key`/`password` values, webhook ids, and long-lived tokens from any content sent to the LLM
- [ ] **LLM-02**: A planted-secret test fixture proves no secret-shaped value appears in the LLM payload
- [ ] **LLM-03**: LLM backend is provider-selectable (Anthropic or OpenAI) via config with the API key read from env
- [ ] **LLM-04**: LLM returns proposed YAML; tool diffs it against the original and feeds hunks into the same review loop as rule passes
- [ ] **LLM-05**: Any hunk where a redacted/secret-shaped value changed is auto-rejected

### CLI Surface (CLI)

- [ ] **CLI-01**: `haco run <profile>` executes the full loop: connect -> pull -> analyze -> review -> stage -> validate -> apply -> restart -> smoke
- [ ] **CLI-02**: `haco rollback <profile>` performs SAFE-04
- [ ] **CLI-03**: Rule-only and LLM-included modes are selectable by flag
- [ ] **CLI-04**: Every run writes a session log (connection, proposed/accepted hunks, check results, commit hash) under `./.haco/`

## v2 Requirements

### API & Reload (API)

- **API-01**: Connect to HA via REST/WebSocket API with a long-lived token
- **API-02**: Reload changed domains without a full restart where HA supports it
- **API-03**: Pull live entity/device/area registry via API instead of inferring from YAML

### Interface (GUI)

- **GUI-01**: Web GUI (FastAPI) wrapping the CLI core for connect/review/apply/rollback

### AI (AIX)

- **AIX-01**: Local LLM backend (Ollama) so sensitive setups avoid cloud entirely

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multi-server / fleet management | One HA instance per run by design |
| Config authoring from scratch / smart-home wizard | Tool optimizes existing config only |
| Unattended auto-apply | M1 is always human-gated (not designed out; revisit later) |
| Editing `.storage/`, registries, UI-managed config | YAML-only scope |
| Re-implementing HA schema validation | Always call HA's own `check_config` |
| Encrypted secrets vault + placeholder round-trip (v1 design) | Replaced by redact-on-send |
| Import/export file workflow (v1 design) | Replaced by direct SSH access |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CONN-01 | Phase 1 | Complete |
| CONN-02 | Phase 1 | Complete |
| CONN-03 | Phase 1 | Complete |
| CONN-04 | Phase 1 | Complete |
| CONN-05 | Phase 1 | Complete |
| CONN-06 | Phase 1 | Complete |
| CONN-07 | Phase 1 | Complete |
| YAML-01 | Phase 2 | Complete |
| YAML-02 | Phase 2 | Partial (02-01 diagnostic; writer in 02-03) |
| YAML-03 | Phase 2 | Pending |
| YAML-04 | Phase 2 | Pending |
| YAML-05 | Phase 2 | Pending |
| PULL-01 | Phase 3 | Pending |
| PULL-02 | Phase 3 | Pending |
| PULL-03 | Phase 3 | Pending |
| RULE-01 | Phase 4 | Pending |
| RULE-02 | Phase 4 | Pending |
| RULE-03 | Phase 4 | Pending |
| RULE-04 | Phase 4 | Pending |
| RULE-05 | Phase 4 | Pending |
| REVIEW-01 | Phase 4 | Pending |
| REVIEW-02 | Phase 4 | Pending |
| REVIEW-03 | Phase 4 | Pending |
| REVIEW-04 | Phase 4 | Pending |
| STAGE-01 | Phase 5 | Pending |
| STAGE-02 | Phase 5 | Pending |
| STAGE-03 | Phase 5 | Pending |
| STAGE-04 | Phase 5 | Pending |
| APPLY-01 | Phase 5 | Pending |
| APPLY-02 | Phase 5 | Pending |
| APPLY-03 | Phase 5 | Pending |
| APPLY-04 | Phase 5 | Pending |
| SAFE-01 | Phase 6 | Pending |
| SAFE-02 | Phase 6 | Pending |
| SAFE-03 | Phase 6 | Pending |
| SAFE-04 | Phase 6 | Pending |
| SAFE-05 | Phase 6 | Pending |
| SAFE-06 | Phase 6 | Pending |
| CLI-02 | Phase 6 | Pending |
| LLM-01 | Phase 7 | Pending |
| LLM-02 | Phase 7 | Pending |
| LLM-03 | Phase 7 | Pending |
| LLM-04 | Phase 7 | Pending |
| LLM-05 | Phase 7 | Pending |
| CLI-01 | Phase 7 | Pending |
| CLI-03 | Phase 7 | Pending |
| CLI-04 | Phase 7 | Pending |

**Coverage:**

- v1 requirements: 47 total
- Mapped to phases: 47
- Unmapped: 0

---
*Requirements defined: 2026-08-29*
*Last updated: 2026-08-29 after roadmap creation*
