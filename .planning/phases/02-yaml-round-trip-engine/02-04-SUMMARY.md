---
phase: 02-yaml-round-trip-engine
plan: 04
subsystem: configtree
tags: [idempotency, fixed-point, no-op-stability, identity-splice, apply-then-revert, integration-test]

requires:
  - phase: 02-yaml-round-trip-engine
    provides: "02-01: load_file, build_span_index, Span.kind, ha_config_tree conftest fixture (BOM+CRLF probe), ruamel.yaml>=0.19.1,<0.20 pin"
  - phase: 02-yaml-round-trip-engine
    provides: "02-02: load_config_tree, ConfigTree (node/get/source_text), FileNode, IncludeGraph"
  - phase: 02-yaml-round-trip-engine
    provides: "02-03: writer.serialize(tree) -> dict[Path,str], writer.flush(tree) -> tuple[Path,...] (dirty-only atomic), ConfigTree.set / dirty_files, UnspliceableNodeError"
provides:
  - "tests/test_configtree_idempotency.py: the three D-10 no-op stability properties as integration tests over the whole fixture tree - test_serialize_is_fixed_point, test_fixed_point_covers_every_fixture_file, test_empty_changeset_zero_writes, test_apply_then_revert_is_byte_identical (x4 scalar kinds)"
  - "tests/support/snapshots.py: snapshot_tree(root) -> dict[Path, (bytes, mtime_ns)] - the single shared filesystem-snapshot helper for the whole test suite"
  - "haco.configtree.tree: ConfigTree.set() identity-splice guard - value equal to the node's exact source slice is recorded verbatim, so reverting a node to its original text is byte-for-byte (D-10.3)"
affects: [analyze, apply, rollback, diff-review]

actuals:
  tokens: 3600
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Engine idempotency proven at the engine level (D-10): no analysis engine exists yet, so YAML-05's 'zero proposed changes' is asserted as three no-op stability properties - fixed-point serialize, empty-change-set zero writes, apply-then-revert byte-identical - against the whole representative fixture tree, never a single toy file"
    - "Fixed point via a real second on-disk tree: serialize -> write every file to a fresh tmp dir with newline='' (line endings and BOM not laundered) -> load that dir as its own ConfigTree -> serialize again; equality asserted per file with the drifted file named in the message"
    - "Coverage guard against a false green: test_fixed_point_covers_every_fixture_file asserts the serialization key set equals the loaded file set AND equals the known 12-file reachable set, so a harness that silently walked a subset cannot report a green fixed point"
    - "Identity splice on revert: ConfigTree.set() short-circuits when value is a str equal to text[span.start:span.end] and records that slice verbatim; re-rendering through render_scalar would re-quote a quoted scalar or re-wrap a literal block and defeat byte-for-byte revert"
    - "One snapshot helper, one place: the (bytes, mtime_ns) per-file snapshot moved out of test_configtree_writer.py into tests/support/snapshots.py; mtime is compared as well as bytes so a writer that rewrote identical content is caught as churn"

key-files:
  created:
    - "tests/test_configtree_idempotency.py - the D-10 integration harness (7 test cases)"
    - "tests/support/snapshots.py - snapshot_tree shared helper"
  modified:
    - "src/haco/configtree/tree.py - ConfigTree.set() identity-splice guard + docstring"
    - "tests/test_configtree_writer.py - imports snapshot_tree from tests.support.snapshots; local _snapshot removed"

key-decisions:
  - "ConfigTree.source_text() was NOT added in this plan - it already landed in 02-02 (tree.py) with the exact text[span.start:span.end] semantics the plan's Task 1 asked for. Task 1's <action> says 'if 02-02 did not already land it'; it did, so Task 1 is test-only."
  - "Task 2 needed one real source change: an identity-splice guard in ConfigTree.set(). The plan's Task 2 <behavior> explicitly anticipates it ('whether the writer skips the write or performs an identity splice') and the frontmatter files_modified lists tree.py, so this is in-scope GREEN work, not a deviation. RED committed first (d81e7cc), GREEN after (679e1ae)."
  - "The empty-change-set test is named test_empty_changeset_zero_writes (not the plan prose table's test_empty_changeset_writes_zero_files) so it matches both the plan's own <verify> command (-k empty_changeset_zero_writes) and the VALIDATION.md idempotency test map. The prose table name would have made the verify command report 'no tests ran'."
  - "test_apply_then_revert_is_byte_identical is parametrized over FOUR scalar kinds (plain, single-quoted, double-quoted, literal-block) rather than the plan's minimum three - the extra single-quoted case (external_url) costs nothing and both quote styles now have an explicit revert proof. Verify requires >= 3; 4 reported."
  - "Fixed-point and apply-then-revert compare bytes only (mtime excluded) because flush() legitimately rewrites the touched file with identical content on a revert (identity splice moves mtime). The dedicated empty-change-set test is where mtime is asserted unmoved."

patterns-established:
  - "A whole-tree round-trip integration test writes the serialized mapping back to a second tmp directory and re-loads it, rather than trusting serialize() to be its own oracle"
  - "Shared test helpers live in tests/support/*.py (importable module), matching the existing tests/support/ssh_server.py convention, not duplicated per test module"

requirements-completed: [YAML-05]

coverage:
  - id: D1
    description: "load -> serialize -> write to a second on-disk tree -> load -> serialize is a per-file fixed point: the second serialization equals the first byte-for-byte for every file, including the BOM + CRLF probe (D-10.1)"
    requirement: "YAML-05"
    verification:
      - kind: integration
        ref: "tests/test_configtree_idempotency.py#test_serialize_is_fixed_point"
        status: pass
    human_judgment: false
  - id: D2
    description: "The fixed-point harness provably visited every reachable file - the serialization key set equals the loaded file set and equals the known 12-file fixture reachable set (D-10.1 coverage guard against a false green)"
    requirement: "YAML-05"
    verification:
      - kind: integration
        ref: "tests/test_configtree_idempotency.py#test_fixed_point_covers_every_fixture_file"
        status: pass
    human_judgment: false
  - id: D3
    description: "Loading the tree and flushing with no set() call returns an empty tuple and leaves every file's bytes AND mtime unchanged (D-10.2)"
    requirement: "YAML-05"
    verification:
      - kind: integration
        ref: "tests/test_configtree_idempotency.py#test_empty_changeset_zero_writes"
        status: pass
    human_judgment: false
  - id: D4
    description: "Setting a node to a distinct value then setting it back to its captured source text then flushing leaves every file byte-identical to the pre-mutation snapshot, across a plain, a single-quoted, a double-quoted and a literal-block scalar (D-10.3)"
    requirement: "YAML-05"
    verification:
      - kind: integration
        ref: "tests/test_configtree_idempotency.py#test_apply_then_revert_is_byte_identical[4 params]"
        status: pass
    human_judgment: false
  - id: D5
    description: "ConfigTree.set() records the node's exact source slice verbatim (identity splice) when value equals that slice, so a revert never re-quotes or re-wraps the restored text"
    requirement: "YAML-05"
    verification:
      - kind: unit
        ref: "tests/test_configtree_idempotency.py#test_apply_then_revert_is_byte_identical[configuration.yaml-node_path2-Antarctica/Troll]"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-08-30
status: complete
---

# Phase 2 Plan 04: YAML Round-Trip Engine - No-Op Stability Harness Summary

**The engine is proven a fixed point over the whole representative fixture tree: `load -> serialize -> reload -> serialize` is byte-identical per file, an empty change set flushes zero files and moves no mtime, and mutating a node then reverting it to its captured source text leaves every file byte-for-byte identical across four scalar kinds - the assumption every later phase makes about running the engine over an unchanged tree, turned into a test that fails loudly.**

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-08-30
- **Tasks:** 2 (1 tracer + 1 TDD)
- **Commits:** 4 (1 tracer + RED + GREEN + this docs commit)
- **Tests:** 116 pass (was 109 at end of 02-03; +7 in `tests/test_configtree_idempotency.py`)
- **Gate:** `uv run ruff check . && uv run black --check . && uv run mypy && uv run pytest -q` exits 0; mypy strict clean on 35 files.

## Accomplishments

- `tests/test_configtree_idempotency.py` - the D-10 integration harness, all against the `ha_config_tree` throwaway copy:
  - `test_serialize_is_fixed_point` - serializes the loaded tree, writes every file into a second `tmp_path` directory with `newline=""` and `encoding="utf-8"` (so neither line endings nor the leading BOM are laundered), loads that directory as its own `ConfigTree`, serializes again, and asserts the two mappings are equal key-for-key and byte-for-byte, naming any drifted file.
  - `test_fixed_point_covers_every_fixture_file` - asserts the serialization key set equals the loaded file set and equals the known 12-file reachable fixture set (`configuration.yaml`, `automations.yaml`, `encoding/crlf_bom.yaml`, the `packages/`, `scenes/`, `sensors/`, `sensors/nested/`, `groups/`, `templates/` files), so a harness that walked a subset cannot report a green fixed point.
  - `test_empty_changeset_zero_writes` - snapshots every file's `(bytes, mtime_ns)`, loads the tree, calls `flush` with no `set`, asserts the returned tuple is `()` and that both bytes and mtime are unchanged for every file.
  - `test_apply_then_revert_is_byte_identical` - parametrized over a plain (`homeassistant.name`), a single-quoted (`homeassistant.external_url`), a double-quoted (`homeassistant.time_zone`) and a literal-block (`automations[1].variables.template_body`) scalar; captures the node's exact source slice via `ConfigTree.source_text`, sets a distinct intermediate value, sets it back to the captured slice, flushes, and asserts every file is byte-identical to the pre-mutation snapshot.
- `tests/support/snapshots.py` - `snapshot_tree(root)` promoted out of `test_configtree_writer.py` so the `(bytes, mtime_ns)` per-file snapshot helper exists in exactly one place; `test_configtree_writer.py` now imports it.
- `haco.configtree.tree.ConfigTree.set()` - identity-splice guard: when `value` is a `str` equal to `text[span.start:span.end]`, the slice is recorded verbatim instead of being re-rendered through `render_scalar` (which would re-quote a quoted scalar or re-wrap a literal block). Non-revert edits are unaffected - they never equal the original slice.

## Task Commits

1. **Task 1 (tracer): fixed-point serialize over the whole fixture tree** - `ea9629a` (test) - `test_serialize_is_fixed_point` + `test_fixed_point_covers_every_fixture_file`. No source change: `ConfigTree.source_text()` already landed in 02-02.
2. **Task 2 (RED): empty change set + apply-then-revert** - `d81e7cc` (test) - `tests/support/snapshots.py`, the writer-test import swap, and both remaining D-10 tests. The three quoted/literal revert cases fail RED because re-rendering the captured source text re-quotes / re-wraps it.
3. **Task 2 (GREEN): identity splice on revert** - `679e1ae` (feat) - the `ConfigTree.set()` guard; all four revert cases pass.

**Plan metadata:** this docs commit (SUMMARY + STATE + ROADMAP + REQUIREMENTS).

## Files Created/Modified

- `tests/test_configtree_idempotency.py` - new; 2 tests in `ea9629a`, +5 (1 + 4 params) in `d81e7cc`
- `tests/support/snapshots.py` - new (landed in `d81e7cc`)
- `tests/test_configtree_writer.py` - `_snapshot` removed, `snapshot_tree` imported (`d81e7cc`)
- `src/haco/configtree/tree.py` - `ConfigTree.set()` identity-splice guard + docstring (`679e1ae`)

## Decisions Made

See `key-decisions` in the frontmatter. In short: `source_text()` was already present from 02-02 so Task 1 is test-only; Task 2's one source change (the identity-splice guard) is in-scope GREEN work the plan's `<behavior>` explicitly anticipates; the empty-change-set test is named to match the plan's own `<verify>` command and VALIDATION.md rather than the plan's prose table; four scalar kinds instead of the minimum three; bytes-only comparison for fixed-point / apply-then-revert with mtime asserted only in the dedicated empty-change-set test.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Test name aligned to the `<verify>` command, not the plan's prose table**
- **Found during:** Task 2.
- **Issue:** The plan's artifact/test table names the empty-change-set test `test_empty_changeset_writes_zero_files`, but Task 2's own `<verify>` runs `uv run pytest -q tests/test_configtree_idempotency.py -k empty_changeset_zero_writes` (matching VALIDATION.md's idempotency test map). With the table's name, `-k empty_changeset_zero_writes` matches nothing and the `<fails_when>` ("no tests ran") trips.
- **Fix:** Named the test `test_empty_changeset_zero_writes`. Matches the `<verify>` filter and the canonical VALIDATION.md D-10.2 row.
- **Files modified:** `tests/test_configtree_idempotency.py`
- **Verification:** `uv run pytest -q tests/test_configtree_idempotency.py -k empty_changeset_zero_writes` -> 1 passed.
- **Committed in:** `d81e7cc`

---

**Total deviations:** 1 auto-fixed (1 blocking - test-name alignment).
**Impact on plan:** None on scope. The identity-splice guard in `ConfigTree.set()` is not counted as a deviation - the plan's Task 2 `<behavior>` explicitly contemplates it ("whether the writer skips the write or performs an identity splice") and the plan frontmatter's `files_modified` lists `src/haco/configtree/tree.py`.

## TDD Gate Compliance

Task 2 carries `tdd="true"`. RED/GREEN sequence is present in git log:
- RED: `d81e7cc` `test(02-04): RED - empty change set + apply-then-revert` - three parametrized cases fail as recorded.
- GREEN: `679e1ae` `feat(02-04): identity splice on revert` after it - all cases pass.
`test_empty_changeset_zero_writes` and the plain-scalar revert case passed at RED (the engine already satisfied those); only the quoted/literal revert cases drove new code, and each exercises a distinct scalar-delimiting style.

## Issues Encountered

- Git reports `LF will be replaced by CRLF` for the new/changed `tests/*.py` and `src/**/*.py` on this Windows checkout (`core.autocrlf=true`) - as in every prior Phase 1 / 02-0x summary, the quality gate is unaffected.
- `.planning/state.json` is an untracked GSD 1.12 auto-snapshot; left untracked, never staged into a code commit.
- `gsd-core/bin` is absent in this worktree; `gsd-tools.cjs` is reachable at `~/.claude/gsd-core/bin/` (v1.12.0, identity-verified) and STATE / ROADMAP / REQUIREMENTS were updated through it. `.planning/WINDOWS.md` is not present in this worktree - nothing to append.

## Next Phase Readiness

- **analyze / diff-review / apply / rollback** can now rely on the proven invariant: running the engine over an unedited tree changes nothing on disk. Any diff those phases produce carries no engine noise, and the apply stage commits no churn on a no-op.
- `serialize(tree)` is confirmed a pure fixed-point function of the loaded tree; `flush(tree)` on a clean tree is a guaranteed no-op (zero writes, zero mtime movement); `ConfigTree.set(path, original_source_text)` is a guaranteed byte-for-byte revert.
- No blockers introduced. The pre-existing Phase 01 `01-04` `checkpoint:human-verify` remains outstanding (unrelated to this plan).
- Phase-level verification (marking the phase verified/complete) is the orchestrator's verifier step, not done here.

## Known Stubs

None. All four D-10 test functions are real integration assertions against the fixture tree; the identity-splice guard is fully implemented with no placeholder branch.

## Self-Check: PASSED

- `tests/test_configtree_idempotency.py`, `tests/support/snapshots.py` present on disk.
- Commits `ea9629a`, `d81e7cc`, `679e1ae` in `git log`.
- `uv run ruff check . && uv run black --check . && uv run mypy && uv run pytest -q` exits 0 (116 passed, mypy strict clean on 35 files).
- `uv run pytest -q tests/test_configtree_idempotency.py` - 7 passed, 0 skipped.
- `uv run pytest -q tests/test_configtree_idempotency.py -k fixed_point` - 2 passed.
- `uv run pytest -q tests/test_configtree_idempotency.py -k apply_then_revert` - 4 passed.
- `git status --porcelain tests/fixtures` - prints nothing after the full test run.

---
*Phase: 02-yaml-round-trip-engine*
*Completed: 2026-08-30*
