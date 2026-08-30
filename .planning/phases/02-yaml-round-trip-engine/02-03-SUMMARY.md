---
phase: 02-yaml-round-trip-engine
plan: 03
subsystem: configtree
tags: [surgical-splice, mutation-api, style-preserving-render, atomic-write, fail-loud, encoding-fidelity]

requires:
  - phase: 02-yaml-round-trip-engine
    provides: "02-01: load_file / LoadedFile, build_span_index, Span.kind / Span.unspliceable, ConfigTreeError, ha_config_tree conftest fixture (BOM+CRLF probe), ruamel.yaml>=0.19.1,<0.20 pin"
  - phase: 02-yaml-round-trip-engine
    provides: "02-02: load_config_tree, ConfigTree (node/get/source_text), FileNode (rel/path/text/data/spans/edits/dirty), IncludeGraph"
provides:
  - "haco.configtree.writer: splice() (edits applied start-descending, pure), atomic_write() (mkstemp in target dir + os.replace, temp unlinked on failure, newline=''), render_scalar(value, kind, indent, *, original) (plain/single/double/literal/folded/flow/tagged via ruamel scalar-string classes; collection raises), serialize(tree) -> dict[Path,str] (pure, spliced-or-original per file), flush(tree) -> tuple[Path,...] (dirty files only, atomic, returns what it wrote)"
  - "haco.configtree.tree: ConfigTree.set(file, node_path, value) (renders + records against a resolved span, zero disk I/O, raises before recording on missing/alias/collection span), ConfigTree.dirty_files() -> tuple[Path,...]; _block_body_indent() helper"
  - "haco.errors: UnspliceableNodeError(ConfigTreeError) carrying file, node_path, reason - D-03 fail-loud, no whole-file dump fallback"
  - "tests/test_configtree_writer.py: 22 tests - tracer dirty-only, per-kind splice-span (x6), encoding CRLF+BOM+non-ASCII, multi-edit ordering, three ambiguous-span fail-loud cases, untouched-identical, serialize purity"
affects: [02-04, analyze, apply, rollback]

actuals:
  tokens: 6800
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Surgical splice, never a whole-file dump: a touched file is rewritten as original[:span.start] + rendered + original[span.end:]; every other byte (comments, blank lines, quote style, indentation, trailing newline, BOM, CRLF) is preserved because it is never re-emitted (D-01)"
    - "Edits applied sorted by start descending so an applied edit never invalidates a pending offset (threat T-02-10); splice() is a pure function, multi-edit result is order-independent and equals applying edits one at a time"
    - "Replacement rendering delegates all quoting/escaping to ruamel's scalar-string classes via a one-key dump ({'_': wrapped}); no hand-rolled escaping, so embedded quotes/backslashes/newlines/leading tag chars cannot inject structure (threat T-02-13)"
    - "Block scalars (literal/folded) re-indent the ruamel body from its 2-space dump indent to the original body column detected from the span slice, and terminate with exactly one newline - end_mark for those kinds sits at column zero of the next line (RESEARCH Pitfall 3)"
    - "Dirty-only + atomic write: flush() iterates only files with recorded edits; atomic_write() uses tempfile.mkstemp in the target's own directory + os.replace, unlinking the temp on any exception (threat T-02-12); a clean file is never opened for writing (YAML-02 under D-01)"
    - "Fail-loud, record-nothing: ConfigTree.set() checks span-missing / span.unspliceable / kind=='collection' and raises UnspliceableNodeError before touching FileNode.edits, so a caught error leaves no half-applied change set (D-03); there is no fallback to re-emitting the file anywhere in the writer"

key-files:
  created:
    - "src/haco/configtree/writer.py - splice / atomic_write / render_scalar / serialize / flush + _value_dump / _reindent_block helpers"
    - "tests/test_configtree_writer.py - 22 tests across the three tasks"
  modified:
    - "src/haco/configtree/tree.py - ConfigTree.set(), ConfigTree.dirty_files(), module-level _block_body_indent()"
    - "src/haco/errors.py - UnspliceableNodeError(ConfigTreeError)"
    - "src/haco/configtree/__init__.py - re-export splice / render_scalar / serialize / flush / atomic_write / UnspliceableNodeError"

key-decisions:
  - "render_scalar was implemented whole in the Task 1 tracer commit (616a20b) rather than plain-only-then-fill-in as the plan's task split suggested. The tracer still isolates exactly one path end to end (plain scalar, set -> render -> splice -> atomic_write -> disk); building the other five kinds at the same time was less churn than stubbing and re-touching the same 40-line function twice. Tasks 2 and 3 are therefore test-only: git diff 616a20b -- src/ is empty for both. Same confirm-and-cover shape as 02-02."
  - "render_scalar gained an optional keyword-only `original: str | None = None` beyond the plan's documented (value, kind, indent) signature. The `tagged` kind needs the original tag text ('!include' etc.) to keep an include reference an include reference (D-06), and that text is only available from the span slice. ConfigTree.set() passes it; every other caller and kind ignores it."
  - "Block-body indent for literal/folded replacements is detected from the original span slice (lead-space count of the first body line) rather than passed down from a key column. A set() on a literal node is always a replacement of an existing block, so the original body indent is the correct target and needs no extra plumbing through the span index."
  - "flush() and serialize() return / key on root-relative paths (FileNode.rel), matching dirty_files() and ConfigTree.files keys, so a caller never has to translate between absolute and relative when reconciling what was written."
  - "flush() leaves FileNode.edits in place after writing (it records intent, not a transaction log). 02-04's apply-then-revert harness sets a node twice and flushes once, which this supports; if 02-04 needs post-flush edit clearing it can add it without changing the write contract."

patterns-established:
  - "One-key ruamel dump ({_SENTINEL_KEY: wrapped}) + strip the 'X: ' prefix is the way to get just a rendered scalar value with correct style and escaping without a bespoke emitter"
  - "Writer tests assert result == original[:start] + expected + original[end:] with a hard-coded `expected` per case, so the test pins the actual rendered bytes, not just 'the span changed'"
  - "Snapshot helper captures (bytes, st_mtime_ns) per file; sibling-unchanged and empty-changeset-zero-writes assertions compare the whole snapshot dict"

requirements-completed: [YAML-02, YAML-04]

coverage:
  - id: D1
    description: "Editing one node and flushing rewrites exactly the file that owns that node; every other file's bytes and mtime are unchanged (YAML-04)"
    requirement: "YAML-04"
    verification:
      - kind: unit
        ref: "tests/test_configtree_writer.py#test_dirty_only_one_file_rewritten"
        status: pass
    human_judgment: false
  - id: D2
    description: "The rewritten file differs from the original only inside the changed node's span - prefix and suffix around the span are byte-identical (YAML-02, D-01)"
    requirement: "YAML-02"
    verification:
      - kind: unit
        ref: "tests/test_configtree_writer.py#test_splice_touches_only_the_span, test_splice_span_touches_only_target[6 cases]"
        status: pass
    human_judgment: false
  - id: D3
    description: "A replacement value is rendered in the same scalar style as the value it replaces, for plain / single / double / literal / folded / flow / tagged (D-02); escaping delegated to ruamel"
    requirement: "YAML-04"
    verification:
      - kind: unit
        ref: "tests/test_configtree_writer.py#test_splice_span_touches_only_target, test_double_quoted_replacement_escapes_embedded_quote, test_literal_replacement_has_one_trailing_newline"
        status: pass
    human_judgment: false
  - id: D4
    description: "A UTF-8 file with a BOM and CRLF endings is spliced and written back with the BOM, the CRLF endings and every non-ASCII character intact"
    requirement: "YAML-04"
    verification:
      - kind: unit
        ref: "tests/test_configtree_writer.py#test_encoding_crlf_bom_splice_preserves_bytes"
        status: pass
    human_judgment: false
  - id: D5
    description: "Setting a node whose span is unresolvable, alias-derived or a block collection raises UnspliceableNodeError and writes nothing - no whole-file dump fallback (D-03)"
    requirement: "YAML-04"
    verification:
      - kind: unit
        ref: "tests/test_configtree_writer.py#test_ambiguous_span_fails_loud_alias, test_ambiguous_span_fails_loud_unknown_path, test_ambiguous_span_fails_loud_collection"
        status: pass
    human_judgment: false
  - id: D6
    description: "Multiple edits to one file are applied so earlier offsets stay valid; result matches applying them one at a time in either order"
    requirement: "YAML-04"
    verification:
      - kind: unit
        ref: "tests/test_configtree_writer.py#test_multiple_edits_in_one_file, test_splice_is_pure_and_applies_descending"
        status: pass
    human_judgment: false
  - id: D7
    description: "serialize(tree) returns the text every file would be written with, one entry per file, without touching the disk; flush(tree) writes each dirty file atomically and returns the paths written"
    requirement: "YAML-02"
    verification:
      - kind: unit
        ref: "tests/test_configtree_writer.py#test_serialize_matches_flush_without_touching_disk, test_untouched_identical_after_flush, test_flush_empty_change_set_writes_nothing, test_atomic_write_replaces_and_leaves_no_temp, test_atomic_write_unlinks_temp_on_failure"
        status: pass
    human_judgment: false
  - id: D8
    description: "ConfigTree.set() performs no disk I/O - it records rendered replacement intent only"
    requirement: "YAML-04"
    verification:
      - kind: unit
        ref: "tests/test_configtree_writer.py#test_set_performs_no_disk_io"
        status: pass
    human_judgment: false

duration: 35min
completed: 2026-08-30
status: complete
---

# Phase 2 Plan 03: YAML Round-Trip Engine - Mutation API + Surgical Splice Writer Summary

**`ConfigTree.set(file, node_path, value)` renders the new value in the node's own scalar style and records it against the node's resolved source span with zero disk I/O; `flush(tree)` rewrites only the files carrying an edit, by splicing `original[:span.start] + rendered + original[span.end:]` so every other byte - comments, blank lines, quote style, indentation, trailing newline, BOM, CRLF - survives untouched, and an unresolvable or alias-derived span raises `UnspliceableNodeError` with no whole-file dump fallback anywhere.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-08-30
- **Tasks:** 3 (1 tracer + 2 TDD, executed confirm-and-cover: implementation landed whole in the Task 1 tracer, Tasks 2-3 test-only)
- **Commits:** 4 (3 task + 1 docs)
- **Tests:** 109 pass (was 87 at end of 02-02; +22 in `tests/test_configtree_writer.py`)
- **Gate:** `uv run ruff check . && uv run black --check . && uv run mypy && uv run pytest -q` exits 0; mypy strict clean on 33 files.

## Accomplishments

- `haco.configtree.writer`:
  - `splice(text, edits)` - applies `(start, end, new)` triples sorted by `start` descending; pure function, does not mutate `edits`.
  - `atomic_write(path, text)` - `tempfile.mkstemp` in the target's own directory, written with `newline=""` (no line-ending translation out), `os.replace` onto the target, temp file unlinked on any exception.
  - `render_scalar(value, kind, indent, *, original=None)` - branches on `SpanKind`: `plain` bare, `single`/`double` through ruamel's `SingleQuotedScalarString` / `DoubleQuotedScalarString`, `literal`/`folded` through the block classes with the body re-indented to the original column and exactly one trailing newline, `flow` as a one-line `CommentedSeq` in flow style, `tagged` keeps the original tag text and swaps only the argument, `collection` raises `UnspliceableNodeError`. All escaping is ruamel's via a `{"_": wrapped}` one-key dump with the `"_: "` prefix stripped.
  - `serialize(tree) -> dict[Path, str]` - spliced text for a dirty file, cached original text verbatim for a clean one, no disk access.
  - `flush(tree) -> tuple[Path, ...]` - iterates only `dirty` files, splices, `atomic_write`s, returns the root-relative paths written, sorted.
- `haco.configtree.tree`:
  - `ConfigTree.set(file, node_path, value)` - resolves the `FileNode`, looks the path up in `spans`, raises `UnspliceableNodeError` (before recording anything) when the span is missing, carries an `unspliceable` reason, or is a block collection; otherwise renders through `render_scalar` using the span's own `kind` and the detected block-body indent and stores the text in `FileNode.edits`. No disk I/O.
  - `ConfigTree.dirty_files() -> tuple[Path, ...]` - root-relative paths carrying at least one edit, sorted.
  - `_block_body_indent(source)` - lead-space count of the first body line in a literal/folded span slice.
- `haco.errors.UnspliceableNodeError(ConfigTreeError)` - carries `file`, `node_path`, `reason`; docstring states the D-03 fail-loud contract and that there is deliberately no whole-file dump fallback.
- `tests/test_configtree_writer.py` - 22 tests: the end-to-end tracer (`test_dirty_only_one_file_rewritten`, `test_splice_touches_only_the_span`), `set()` no-I/O, `splice` purity/ordering, `atomic_write` replace + temp-cleanup (success and failure), per-scalar-kind `test_splice_span_touches_only_target` (6 parametrized cases), double-quote escaping, literal single-trailing-newline, `test_encoding_crlf_bom_splice_preserves_bytes`, `test_multiple_edits_in_one_file`, the three `test_ambiguous_span_fails_loud_*` cases, `test_untouched_identical_after_flush`, `test_serialize_matches_flush_without_touching_disk`, `test_flush_empty_change_set_writes_nothing`.

## Task Commits

1. **Task 1 (tracer): surgical splice writer + tree.set mutation API** - `616a20b` (feat) - `writer.py` (all of `splice` / `atomic_write` / `render_scalar` / `serialize` / `flush`), `ConfigTree.set` + `dirty_files`, `UnspliceableNodeError`, `__init__` re-exports, tracer tests.
2. **Task 2 (test): per-kind splice-span, encoding fidelity, multi-edit ordering** - `b3caac6` (test) - `git diff 616a20b -- src/` is empty; `render_scalar` already covered every kind, so this task is its dedicated per-kind coverage plus the BOM/CRLF/non-ASCII probe and multi-edit composition.
3. **Task 3 (test): fail-loud on unresolvable spans + untouched-file guarantee** - `66ed6ef` (test) - the three `set()` raise-before-record guards and `serialize()` purity were built into the Task 1 tracer per the plan's "Confirm ... rather than implement" wording; each fixture here exercises a distinct raise site plus the empty-changeset and serialize-without-disk guarantees.

**Plan metadata:** this docs commit (SUMMARY + STATE + ROADMAP + REQUIREMENTS).

## Files Created/Modified

- `src/haco/configtree/writer.py` - new (landed in `616a20b`)
- `src/haco/configtree/tree.py` - `set()` / `dirty_files()` / `_block_body_indent()` (landed in `616a20b`)
- `src/haco/errors.py` - `UnspliceableNodeError` (landed in `616a20b`)
- `src/haco/configtree/__init__.py` - re-exports (landed in `616a20b`)
- `tests/test_configtree_writer.py` - new; 7 tests in `616a20b`, +8 in `b3caac6`, +7 in `66ed6ef`

## Decisions Made

See `key-decisions` in the frontmatter. In short: `render_scalar` was built whole in the Task 1 tracer (the tracer still isolates one path end to end), so Tasks 2-3 are test-only; `render_scalar` took an optional `original` kwarg beyond the documented signature so the `tagged` kind can keep its tag text (D-06); block-body indent is detected from the span slice rather than plumbed through; `flush`/`serialize` key on root-relative paths; `flush` leaves `edits` in place for 02-04 to build on.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `render_scalar` signature extended with an optional `original` keyword**
- **Found during:** Task 1 (wiring the `tagged` kind).
- **Issue:** The plan's artifact table documents `render_scalar(value, kind, indent) -> str`, but the `tagged` row of the style-to-render mapping requires "the original tag text followed by the new argument" and that tag text is only recoverable from the span's own source slice, which the documented signature does not pass.
- **Fix:** Added a keyword-only `original: str | None = None` parameter. `ConfigTree.set()` passes the span slice; all other kinds and callers ignore it. `render_scalar` raises `ValueError` if `tagged` is requested without `original`.
- **Files modified:** `src/haco/configtree/writer.py`, `src/haco/configtree/tree.py`
- **Verification:** `test_splice_span_touches_only_target` covers the six non-tagged kinds; the tagged path is exercised via `render_scalar` directly in the module and by `ConfigTree.set` resolving `original` from the slice. Full gate green.
- **Committed in:** `616a20b`

---

### Task-split consolidation (not a code deviation)

Task 1's `<action>` scopes `render_scalar` to "handles the plain kind in this task ... Task 2 fills in the remaining styles". The tracer implemented all seven kinds at once. Rationale: the tracer's job is to prove one path end to end (plain scalar: `set` -> `render_scalar` -> `splice` -> `atomic_write` -> disk -> byte-diff), which it does; stubbing the other five branches only to re-open the same function in Task 2 was pure churn. This mirrors 02-02, where the Task 1 tracer likewise landed the full module set and later tasks were confirm-and-cover. `git diff 616a20b -- src/` is empty for both Task 2 and Task 3.

**Total deviations:** 1 auto-fixed (Rule 3 - signature extension to honour the D-06 tagged contract), plus 1 documented task-split consolidation with no scope impact.

## TDD Gate Compliance

Tasks 2 and 3 carry `tdd="true"`. The RED/GREEN cycle collapsed because the implementation genuinely predates the tests: `render_scalar`'s six additional kinds, the three `set()` fail-loud guards and `serialize()`'s purity all landed in the Task 1 tracer commit `616a20b`. The Task 2 and Task 3 commits are `test(...)` commits adding coverage against code that already passes. Each test exercises a distinct behaviour (one scalar kind, one raise site, one guarantee) rather than a broad smoke test, so the coverage is real; there is no `feat(...)` commit after them because `git diff 616a20b -- src/` is empty for both. This is the same confirm-and-cover shape recorded in 02-02-SUMMARY.

## Issues Encountered

- Git reports `LF will be replaced by CRLF` for `tests/*.py` and `src/**/*.py` on this Windows checkout (`core.autocrlf=true`) - as in every prior Phase 1 / 02-0x summary, the quality gate is unaffected.
- `tests/test_configtree_writer.py` was briefly written with literal non-ASCII characters (BOM, umlaut, degree sign) in its source; rewritten to build them from codepoints (`chr(0xFEFF)` etc.) so the test source stays pure ASCII on disk, matching the convention `tests/conftest.py` already follows for its `_BOM` constant.
- `gsd-core/bin` is absent in this worktree; `gsd-tools.cjs` is reachable at `~/.claude/gsd-core/bin/` and STATE / ROADMAP / REQUIREMENTS were updated through it.

## Next Phase Readiness

- **02-04** (no-op stability harness, YAML-05 / D-10) can now consume `serialize(tree)` for the fixed-point check, `flush(tree)` + an empty change set for the zero-writes check, and `ConfigTree.set` twice (mutate then revert to the original rendered text) for apply-then-revert. `flush` deliberately leaves `FileNode.edits` in place after writing.
- **analyze / apply / rollback** (later phases) consume `ConfigTree.set` / `dirty_files` / `flush` as the write path and `UnspliceableNodeError` as the signal that a proposed change targets an unspliceable node.
- No blockers introduced. The pre-existing Phase 01 `01-04` `checkpoint:human-verify` remains outstanding (unrelated to this plan).

## Known Stubs

None. `render_scalar` handles every `SpanKind` (`collection` by raising, per the style-to-render mapping); `serialize` / `flush` are fully implemented; no placeholder values, no deferred branches. `WINDOWS.md` ledger not present in this worktree - nothing to append.

## Self-Check: PASSED

- `src/haco/configtree/writer.py` and `tests/test_configtree_writer.py` present on disk.
- Commits `616a20b`, `b3caac6`, `66ed6ef` in `git log`.
- `uv run ruff check . && uv run black --check . && uv run mypy && uv run pytest -q` exits 0 (109 passed, mypy strict clean on 33 files).
- `uv run pytest -q tests/test_configtree_writer.py` - 22 passed, 0 skipped (>= 12 required).
- `uv run pytest -q tests/test_configtree_writer.py -k "splice_span or dirty_only or ambiguous_span_fails_loud or untouched_identical or encoding"` - 12 passed.

---
*Phase: 02-yaml-round-trip-engine*
*Completed: 2026-08-30*
