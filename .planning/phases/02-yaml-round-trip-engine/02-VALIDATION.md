---
phase: "02"
slug: "yaml-round-trip-engine"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-08-30"
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `.planning/phases/02-yaml-round-trip-engine/02-RESEARCH.md` §"Validation Architecture" + §"Fixture Design".

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest` 9.x (already present from Phase 1; `pytest-asyncio` installed, unused here) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests"]`, `asyncio_mode = "auto"`) |
| **Quick run command** | `uv run pytest -q tests/test_configtree_<module>.py` |
| **Full suite command** | `uv run ruff check . && uv run black --check . && uv run mypy && uv run pytest -q` |
| **Estimated runtime** | ~5 seconds (Phase 1's 33 tests + new ConfigTree tests) |

---

## Sampling Rate

- **After every task commit:** `uv run pytest -q tests/test_configtree_<module>.py` for the module the task touched, plus `uv run ruff check . && uv run black --check . && uv run mypy`.
- **After every plan wave:** `uv run pytest -q` (full suite).
- **Before `/gsd-verify-work`:** full quality gate green (`ruff && black --check && mypy && pytest -q`).
- **Max feedback latency:** ~10 seconds.

---

## Per-Task Verification Map

Populated by `gsd-planner` per task. Requirement → behavior → command map (from RESEARCH.md §"Phase Requirements → Test Map"):

| Req ID | Behavior | Test Type | Automated Command | File | Status |
|--------|----------|-----------|-------------------|------|--------|
| YAML-01 | every D-08 tag parses without error (scalar + legal collection form) | unit | `uv run pytest -q tests/test_configtree_loader.py -k tags` | ❌ W0 | ⬜ |
| YAML-01 | unknown `!tag` round-trips opaque + exactly one `warnings.warn` per distinct tag | unit | `... -k unknown_tag` | ❌ W0 | ⬜ |
| YAML-02 | loaded-but-unedited file returned byte-identical (no write occurs) | unit | `uv run pytest -q tests/test_configtree_writer.py -k untouched_identical` | ❌ W0 | ⬜ |
| YAML-02 | diagnostic: `load → dump` with pinned indent byte-identical per fixture file | unit | `tests/test_configtree_loader.py -k roundtrip_diagnostic` | ❌ W0 | ⬜ |
| YAML-03 | graph edge from `configuration.yaml` to every reachable file; `!include_dir_*` → one edge per `.yaml`; `secrets.yaml` absent | unit | `uv run pytest -q tests/test_configtree_includes.py tests/test_configtree_graph.py` | ❌ W0 | ⬜ |
| YAML-03 | include cycle → `ConfigTreeError` naming the cycle (not `RecursionError`) | unit | `... -k cycle` | ❌ W0 | ⬜ |
| YAML-03 | dir scan recursive, `.yaml`-only, dotfiles/`secrets.yaml` skipped, per-dir sorted | unit | `... -k dir_scan` | ❌ W0 | ⬜ |
| YAML-04 | edit one value → exactly that file rewritten; siblings' bytes + mtime unchanged | unit | `uv run pytest -q tests/test_configtree_writer.py -k dirty_only` | ❌ W0 | ⬜ |
| YAML-04 | byte-diff of rewritten file vs original touches ONLY the changed node's span (per scalar kind: plain/single/double/literal/folded/flow) | unit (parametrized) | `... -k splice_span` | ❌ W0 | ⬜ |
| YAML-04 | `set()` on alias-derived / merge-derived / spanless path → `ConfigTreeError` (D-03), no file written | unit | `... -k ambiguous_span_fails_loud` | ❌ W0 | ⬜ |
| YAML-05 / D-10.1 | `load → serialize → load → serialize` on whole fixture tree is a per-file fixed point | integration | `uv run pytest -q tests/test_configtree_idempotency.py -k fixed_point` | ❌ W0 | ⬜ |
| YAML-05 / D-10.2 | empty change set → `writer.flush()` writes 0 files (mtime snapshot) | integration | `... -k empty_changeset_zero_writes` | ❌ W0 | ⬜ |
| YAML-05 / D-10.3 | mutate then revert to original value → every file byte-identical to pre-mutation snapshot | integration | `... -k apply_then_revert` | ❌ W0 | ⬜ |
| cross-cutting | CRLF + BOM + non-ASCII fixture survives load+splice, only target span changed | unit | `tests/test_configtree_writer.py -k encoding` | ❌ W0 | ⬜ |
| cross-cutting | ruamel version pin holds; `compose()` end_mark offsets match golden table (drift canary) | unit | `tests/test_configtree_spans.py -k golden_offsets` | ❌ W0 | ⬜ |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/fixtures/ha_config/` — representative HA tree (RESEARCH.md §"Fixture Design"): `configuration.yaml` with comments, both quote styles, an anchor+alias pair, `packages: !include_dir_named packages/`, every `!include_dir_*` variant, a `!secret`, a `!env_var` with default, an unknown `!custom` tag; `automations.yaml` with a block literal + folded scalar + flow seq + numeric mapping key; `sensors/` with a `nested/` subdir (proves recursion); `groups/secrets.yaml` (must be skipped); `blueprints/automation/example.yaml` using `!input`; `.hidden.yaml` (dotfile, must be skipped).
- [ ] `tests/fixtures/ha_config_bad/` — negative tree: include cycle, duplicate mapping key, `!include` outside root, missing include target.
- [ ] `tests/conftest.py` — add `ha_config_tree` fixture: copies `tests/fixtures/ha_config/` into `tmp_path`, returns root `Path` (writer tests mutate a throwaway copy).
- [ ] `tests/test_configtree_loader.py`, `_spans.py`, `_includes.py`, `_graph.py`, `_writer.py`, `_idempotency.py` — all new.
- [ ] Golden-offset table fixture for the `compose()` drift canary.
- [ ] No framework install — `pytest` already present.

Fold Wave 0 (fixtures + conftest fixture) into plan **02-01 Task 1** per research recommendation.

---

## Manual-Only Verifications

None — every phase behavior has an automated `pytest` command. No live HA needed (Phase 2 is a library exercised against fixture trees).

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
