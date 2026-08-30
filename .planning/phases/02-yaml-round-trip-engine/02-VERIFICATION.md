---
phase: 02-yaml-round-trip-engine
verified: 2026-08-30T00:00:00Z
status: passed
score: 5/5 roadmap success criteria verified (30/30 plan must-have truths verified)
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: n/a
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 2: YAML Round-Trip Engine Verification Report

**Phase Goal:** Load any HA config tree, mutate part of it, and write it back with every untouched byte preserved.
**Verified:** 2026-08-30
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

Every success criterion was checked by reading the actual code in `src/haco/configtree/`
and by an independent spot-check script (not the committed test suite) that loads the
fixture tree, walks the include graph, mutates one node, flushes, and re-serializes.

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | Loader parses a real config using HA custom tags (`!secret`, `!include`, every `include_dir` variant) without error | ✓ VERIFIED | Spot-check: `load_config_tree(fixture)` returns 12 files, no exception. `KNOWN_HA_TAGS` (loader.py:33) holds all 8 D-08 tags. `test_known_ha_tags_parse` is parametrized over all 8 and asserts each loads as an opaque `TaggedScalar`/`CommentedMap`. `!custom_tag` (unknown) warns once and does not fail (`warn_unknown_tags`, `test_unknown_tag_round_trips_and_warns_once`). |
| 2 | Load then dump of an untouched file is byte-identical (comments, quotes, key order, indentation) | ✓ VERIFIED | Delivered via D-01 mechanism: untouched files are never rewritten. `writer.flush` / `writer.serialize` return `node.text` verbatim for any file with no edit (writer.py:196, 208-210). Spot-check: after editing `configuration.yaml`, the untouched `encoding/crlf_bom.yaml` is byte-identical incl. BOM + CRLF. `test_untouched_identical_after_flush`, `test_empty_changeset_zero_writes` (bytes **and** mtime). See INFO note below on the literal-`ruamel`-dump reinterpretation (documented in REQUIREMENTS.md YAML-02 and 02-01 SUMMARY deviation #2). |
| 3 | Tool reports the include graph from `configuration.yaml` to every included file | ✓ VERIFIED | `graph.py` `IncludeGraph` + `tree.load_config_tree` build one `IncludeEdge` per resolved target. Spot-check: 11 edges from `configuration.yaml`, `graph.reachable() == frozenset(tree.files)` is `True`. `test_include_graph_has_one_edge_per_resolved_target`, `test_graph_queries_agree_with_edges`. `include_dir_*` expands to one edge per matched `.yaml` (`resolve_include_targets` -> `find_dir_yaml`). |
| 4 | After an edit to one file, only that file is rewritten on disk; sibling files are unchanged | ✓ VERIFIED | `writer.flush` iterates `tree.files.values()` and `continue`s past any node with no `edits` (writer.py:207-208). Spot-check: `tree.set("configuration.yaml", ...)` + `flush` -> `written == ('configuration.yaml',)`; every other `*.yaml` on disk unchanged in **bytes and mtime**. `test_dirty_only_one_file_rewritten` asserts sibling bytes + mtime. |
| 5 | Running analysis twice yields zero proposed changes on the second run (Phase 2 = D-10 no-op stability) | ✓ VERIFIED | `load -> serialize -> load -> serialize` is a per-file fixed point. Spot-check: second serialization equals the first across all 12 files incl. the BOM+CRLF probe and every scalar style. `test_serialize_is_fixed_point` + `test_fixed_point_covers_every_fixture_file` (coverage guard, asserts all 11+ reachable files visited). Empty change set writes zero files (`test_empty_changeset_zero_writes`); apply-then-revert is byte-identical over 4 scalar styles (`test_apply_then_revert_is_byte_identical`). |

**Score:** 5/5 roadmap success criteria verified. All 30 plan-frontmatter must-have truths (02-01: 8, 02-02: 9, 02-03: 8, 02-04: 5) also verified — see Required Artifacts and Key Links below.

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/haco/configtree/loader.py` | `make_yaml()`, `KNOWN_HA_TAGS` (8 tags), `LoadedFile`, `load_file()`, `warn_unknown_tags()` | ✓ VERIFIED | 141 lines. Reads `read_bytes().decode("utf-8")` (no newline translation, BOM survives). Double-parse: `compose_all` for spans + multi-doc detection, `load` for the editable tree. `DuplicateKeyError` / `MultiDocumentError` raised, not swallowed. Wired into `tree.py`. |
| `src/haco/configtree/spans.py` | `NodePath`, `SpanKind`, `Span` frozen dataclass, `build_span_index()` | ✓ VERIFIED | 135 lines. Per-style `_classify` (plain/single/double/literal/folded/flow/tagged/collection); `!` tag outranks style. Alias guard: a node reached a second time via `*alias` is recorded `unspliceable` naming the anchor and not descended into. `test_configtree_spans.py` golden offset table + `test_alias_path_is_unspliceable`. |
| `src/haco/configtree/includes.py` | `INCLUDE_TAGS`, `SECRET_YAML`, `find_dir_yaml()`, `iter_include_refs()`, `ensure_contained()`, `resolve_include_targets()` | ✓ VERIFIED | 182 lines. `find_dir_yaml` = recursive `os.walk(topdown=True)`, `*.yaml` only, dot-names dropped, `secrets.yaml` skipped, sorted. `ensure_contained` refuses any target outside the resolved root before `os.walk` runs. Matches HA `annotatedyaml._find_files` (RESEARCH.md). |
| `src/haco/configtree/graph.py` | `IncludeEdge`, `IncludeGraph` frozen dataclasses with `children`/`parents`/`reachable`/`package_files` | ✓ VERIFIED | 85 lines. Frozen, tuple-backed (Phase-1 result style). `package_files()` selects by node path `("homeassistant", "packages")`, not by tag. `reachable()` BFS from `configuration.yaml`. |
| `src/haco/configtree/tree.py` | `FileNode`, `ConfigTree`, `load_config_tree()`, `ConfigTree.set()`, `dirty_files()`, `source_text()` | ✓ VERIFIED | 215 lines. DFS walk with on-stack cycle detection -> `IncludeCycleError` (not `RecursionError`). `set()` refuses missing span / alias-derived span / block-collection span with `UnspliceableNodeError` and records nothing; identity-splice on revert to exact source text (D-10.3). |
| `src/haco/configtree/writer.py` | `splice()`, `render_scalar()`, `serialize()`, `flush()`, `atomic_write()` | ✓ VERIFIED | 223 lines. `splice` applies `(start,end,new)` triples end-first (pure). `render_scalar` wraps the new value in the matching `ruamel` scalar-string class (D-02) and keeps a `!tag` verbatim (D-06). `atomic_write` = `mkstemp` in target dir + `os.replace`, `newline=""`. `flush` skips clean files entirely. |
| `src/haco/errors.py` | `ConfigTreeError`, `YamlError`, `DuplicateKeyError`, `MultiDocumentError`, `UnspliceableNodeError`, `IncludeCycleError`, `IncludeEscapeError`, `MissingIncludeError` | ✓ VERIFIED | All present under `HacoError`. Each carries structured attrs (`.cycle`, `.argument`, `.resolved`, `.node_path`) and a secret-safe message. |
| `src/haco/configtree/__init__.py` | Public re-exports | ✓ VERIFIED | 67-line `__all__` re-exports every symbol the plans name. |
| `tests/conftest.py` `ha_config_tree` / `ha_config_bad` fixtures | Copy fixture trees into `tmp_path`; rewrite encoding probe with BOM+CRLF | ✓ VERIFIED | `shutil.copytree` into `tmp_path`; committed fixture bytes never mutated. Probe rewrite makes the BOM/CRLF property checkout-independent. |
| `tests/fixtures/ha_config/` | Representative HA tree: every D-08 tag, nested includes, anchors, `packages:` | ✓ VERIFIED | 12 reachable files, 11 edges, 2 package files (spot-check confirmed). `configuration.yaml` exercises all 4 `include_dir_*` variants + `!include` + `!secret` + `!env_var` + unknown `!custom_tag` + `&wakeup_script`/`*wakeup_script`. |
| `tests/fixtures/ha_config_bad/` | Negative fixtures: cycle, dupkey, multidoc, missing, escape | ✓ VERIFIED | All five present; each drives a typed-error test. |
| `.gitattributes` | `tests/fixtures/** -text` verbatim checkout | ✓ VERIFIED | `git check-attr text` reports `unset` for fixture files — span offsets are platform-stable. |
| `tests/test_configtree_*.py` (6 files) | Loader, spans, includes, graph, writer, idempotency tests | ✓ VERIFIED | 83 tests collected, all pass. Value-level and byte-level assertions; no `skip`/`xfail`; expected values are literal source slices or hand-authored, not system-generated. |

### Key Link Verification

| From | To | Via | Status |
| ---- | -- | --- | ------ |
| `loader.load_file` | `spans.build_span_index` | called on the `compose()` root, stored on `LoadedFile.spans` | ✓ WIRED (loader.py:130) |
| `loader.load_file` | `errors` | `_RuamelDuplicateKeyError` -> `DuplicateKeyError`; second doc -> `MultiDocumentError` | ✓ WIRED (loader.py:123-129) |
| `tree.load_config_tree` | `loader.load_file` | once per reachable file to build each `FileNode` | ✓ WIRED (tree.py:188) |
| `tree.load_config_tree` | `includes.iter_include_refs` / `resolve_include_targets` | per file in the DFS walk | ✓ WIRED (tree.py:197-198) |
| `tree.load_config_tree` | `graph.IncludeEdge` | one appended per resolved target; tuple becomes `ConfigTree.graph` | ✓ WIRED (tree.py:200, 207-211) |
| `includes.ensure_contained` | `errors.IncludeEscapeError` | raised before `os.walk` on an out-of-root target | ✓ WIRED (includes.py:136) |
| `tree.ConfigTree.set` | `spans` | looks up `FileNode.spans`, refuses missing/`unspliceable`/`collection` | ✓ WIRED (tree.py:125-135) |
| `tree.ConfigTree.set` | `writer.render_scalar` | renders replacement text before recording the edit | ✓ WIRED (tree.py:146) |
| `writer.flush` / `serialize` | `tree` `FileNode.edits` | only dirty nodes spliced; clean nodes emitted as cached text | ✓ WIRED (writer.py:193-197, 207-214) |
| `test_configtree_idempotency` | `writer.serialize` / `flush`, `tree.source_text` | fixed-point round-trip + revert via captured source slice | ✓ WIRED |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `ConfigTree.files` | per-file `FileNode.data` / `.text` / `.spans` | `loader.load_file(path)` reading real bytes off disk | ✓ | ✓ FLOWING |
| `ConfigTree.graph.edges` | `IncludeEdge` tuple | accumulated during the real DFS walk over resolved include targets | ✓ | ✓ FLOWING |
| `writer.serialize(tree)` output | per-file text | `splice(node.text, real span offsets)` for dirty files, `node.text` for clean | ✓ | ✓ FLOWING |
| `flush` return value | written paths | only files with recorded `edits`, root-relative + sorted | ✓ | ✓ FLOWING |

No value traced to a static return, hardcoded literal, or mock.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Loader parses full fixture tree, all 8 HA tags known, unknown tag warns | independent script: `load_config_tree` + `load_file` | 12 files loaded, `KNOWN_HA_TAGS`=8, `unknown_tags={'!custom_tag'}` | ✓ PASS |
| Include graph: edges from `configuration.yaml` to every included file | script: enumerate `tree.graph.edges` | 11 edges, all 4 `include_dir_*` variants + `!include` present, `reachable()==files` | ✓ PASS |
| Edit one node -> only that file rewritten, siblings unchanged (bytes+mtime) | script: `set` + `flush` + disk snapshot diff | `written=['configuration.yaml']`, 0 sibling files changed | ✓ PASS |
| Untouched file byte-identical incl. BOM + CRLF after a sibling edit | script: compare probe bytes before/after | identical, BOM present, CRLF present | ✓ PASS |
| `serialize -> load -> serialize` fixed point over the whole tree | script: two serialization passes | identical across all 12 files | ✓ PASS |
| Full quality gate | `uv run ruff check . && uv run black --check . && uv run mypy && uv run pytest -q` | ruff pass, black 35 files unchanged, mypy Success 35 files, pytest 116 passed | ✓ PASS |

### Probe Execution

N/A — no `scripts/*/tests/probe-*.sh` in this repo and the phase declares none. Phase 2 is a fixture-driven library; verification is the pytest suite + independent spot-check above.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| YAML-01 | 02-01 | Loader parses HA custom tags (`!secret`, `!include`, 4× `!include_dir_*`, `!env_var`, `!input`) without error | ✓ SATISFIED | `KNOWN_HA_TAGS` (8), `test_known_ha_tags_parse` over all 8, `test_input_tag_parses_in_scalar_and_mapping_form`, spot-check. |
| YAML-02 | 02-01, 02-03 | Load -> dump of an untouched file byte-identical (comments, quotes, key order, indentation) | ✓ SATISFIED | Diagnostic canary `test_roundtrip_diagnostic_is_byte_identical` (mapping-root strict, sequence-root minus one uniform indent shift); real guarantee = untouched files never rewritten (`test_untouched_identical_after_flush`, `test_empty_changeset_zero_writes`, spot-check). Reinterpretation documented in REQUIREMENTS.md. |
| YAML-03 | 02-02 | Tool builds the include graph linking `configuration.yaml` to every included file | ✓ SATISFIED | `IncludeGraph`, `test_include_graph_has_one_edge_per_resolved_target`, `test_graph_queries_agree_with_edges`, spot-check (11 edges, `reachable()==files`). |
| YAML-04 | 02-03 | Only files containing an approved change are rewritten; all others untouched on disk | ✓ SATISFIED | `flush` skips clean nodes; `test_dirty_only_one_file_rewritten` (sibling bytes+mtime), `test_untouched_identical_after_flush`, spot-check. |
| YAML-05 | 02-04 | Re-running analysis on an already-optimized tree produces zero proposed changes (idempotent) | ✓ SATISFIED | Asserted at engine level as D-10 no-op stability (ROADMAP SC #5 explicitly scopes it this way for Phase 2). `test_configtree_idempotency.py`: fixed point + coverage guard + empty change set + apply-then-revert over 4 scalar styles. Spot-check confirms fixed point. |

No orphaned requirements: REQUIREMENTS.md maps exactly YAML-01..YAML-05 to Phase 2, and all 5 appear across plan frontmatter `requirements:` fields.

### Decision Coverage (CONTEXT.md D-01..D-10)

| Decision | Honored | Evidence |
| -------- | ------- | -------- |
| D-01 surgical text splice, no full dump of a touched file | ✓ | `writer.splice` uses span offsets; no `yaml.dump` of a whole file anywhere. |
| D-02 `ruamel` parses + renders the replacement scalar only | ✓ | `render_scalar` -> `_value_dump` wraps in matching `ScalarString` subclass. |
| D-03 unresolvable span fails loud, no whole-file fallback | ✓ | `UnspliceableNodeError`; `test_ambiguous_span_fails_loud_{alias,unknown_path,collection}` assert `dirty_files()==()` and `flush()==()`. |
| D-04 all include variants + `packages:`, every target editable | ✓ | `load_config_tree`, `test_every_file_node_is_editable`, `test_packages_are_discovered`. |
| D-05 recursive `os.walk`, `.yaml` only, sorted, dotfiles + `secrets.yaml` skipped (amended) | ✓ | `find_dir_yaml`; `test_dir_scan_is_recursive` (nested `c_extra.yaml`), `_yaml_only`, `_skips_dotfiles`, `_skips_secrets_yaml`, `_sorted_per_directory`. |
| D-06 `!include*` opaque, never inlined | ✓ | `render_scalar` "tagged" keeps tag verbatim; `test_include_tag_stays_opaque` spies `read_bytes` — only the asked-for file is opened. |
| D-07 anchors/aliases preserved in-file, never resolved across includes | ✓ | `spans` alias guard; `iter_include_refs` / walk `seen`-set. |
| D-08 8 custom tags registered; unknown `!` tags warn, don't fail | ✓ | `KNOWN_HA_TAGS`, `warn_unknown_tags`, `test_unknown_tag_round_trips_and_warns_once`. |
| D-09 `!secret` opaque; `secrets.yaml` never loaded | ✓ | `SECRET_YAML` skipped in scan + not a graph node; `test_dir_scan_skips_secrets_yaml`; `test_include_tag_stays_opaque` read-spy. |
| D-10 three no-op stability properties | ✓ | `test_configtree_idempotency.py` (4 tests). |

Status impact: none (informational). All 10 decisions honored.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| --------- | ---------- | ------ | ------- | -------- | --------------- | ------- |
| `test_configtree_loader.py` | YAML-01, YAML-02 | 14+ | 0 | No | Value / byte-identity | ✓ sound |
| `test_configtree_spans.py` | YAML-02 (D-01) | 11 | 0 | No | Value (golden offset table, exact slices) | ✓ sound |
| `test_configtree_includes.py` | YAML-03 | 8 | 0 | No | Set equality, typed-exception attrs | ✓ sound |
| `test_configtree_graph.py` | YAML-03 | 7 | 0 | No | Set equality, per-rule | ✓ sound |
| `test_configtree_writer.py` | YAML-02, YAML-04 | ~20 | 0 | No | Byte-identity + mtime, exact replacement text | ✓ sound |
| `test_configtree_idempotency.py` | YAML-05 | ~9 (incl. params) | 0 | No | Byte-identity fixed point + coverage guard | ✓ sound |

- **Disabled tests on requirements:** 0
- **Circular patterns:** 0 — fixtures are hand-authored HA-shaped configs; expected values are literal source substrings or independently written, never captured from the module under test.
- **Insufficient assertions:** 0 — every requirement-linked test asserts value- or byte-level equality.
- **Coverage quantity:** D-10.1 coverage guard (`test_fixed_point_covers_every_fixture_file`) explicitly asserts all 11+ reachable fixture files were visited, defeating a subset-walk false green.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | none | — | No `TODO`/`FIXME`/`XXX`/`TBD`/`HACK`/`PLACEHOLDER`/`return null` stubs in `src/haco/configtree/`. Comment "rewritten by the ha_config_tree fixture" in `crlf_bom.yaml` is intentional (the conftest rewrites the tmp copy with BOM+CRLF); not a stub. |

### Human Verification

N/A — Infrastructure/foundation phase (core library, `src/haco/configtree/`) with no user-facing elements. Every acceptance criterion is verifiable programmatically and was verified both by the 116-test suite and by an independent spot-check script. No ⚠️ PRESENT_BEHAVIOR_UNVERIFIED truths: the behavior-dependent invariants (single-file rewrite isolation, apply-then-revert byte-identity, fixed-point idempotency, fail-loud-writes-nothing) each have a passing behavioral test and were re-confirmed by the spot-check.

### Deviations Reviewed (from SUMMARYs — none reduce scope)

- 02-01 #1: `read_bytes().decode()` instead of Python-3.13-only `read_text(newline=)` — preserves BOM/CRLF, correct fix.
- 02-01 #2: literal `ruamel` load->dump cannot be byte-identical for document-root block sequences under HA's required indent pin; the round-trip test tolerates exactly one uniform 2-space shift for sequence-root files while keeping mapping-root files strict. **No product impact** — D-01 splices untouched files rather than dumping them; the real "every untouched byte preserved" guarantee is verified independently. Reinterpretation is recorded in REQUIREMENTS.md YAML-02.
- 02-02 #1: removed dead `_child_paths` helper from a resumed-session partial test file — cleanup only.
- 02-03: `render_scalar` gained an `original` kwarg to honour the D-06 tagged contract — in-scope.
- 02-04: one test renamed for alignment; identity-splice guard in `ConfigTree.set()` anticipated by the plan's Task 2 `<behavior>` and `files_modified` — in-scope GREEN work.

The 02-02 rate-limit resume left no incomplete artifacts: `test_every_file_node_is_editable` asserts non-empty `text` + `spans` on every `FileNode`, and the full gate is green.

### Gaps Summary

None. All five ROADMAP success criteria are observably true in the codebase, confirmed by an
independent spot-check that does not rely on the committed test suite. All five requirements
(YAML-01..YAML-05) are delivered by real, wired code. All ten locked decisions (D-01..D-10,
including the D-05 recursive-scan amendment) are honored. The full quality gate is green:
`ruff` clean, `black` 35 files unchanged, `mypy` strict Success (35 files), `pytest` 116 passed
(33 Phase 1 preserved + 83 new configtree tests). Test quality is high — byte-level and
value-level assertions, mtime checks, encoding fidelity, a coverage guard against subset walks,
no skipped or circular tests.

INFO (not a gap): Success criterion #2's literal phrasing ("load then dump ... byte-identical")
is satisfied through the D-01 surgical-splice architecture — untouched files are never
re-emitted — rather than a literal whole-file `ruamel` dump, which is provably impossible for
document-root block sequences under Home Assistant's required 2-space indent pin. This
reinterpretation is documented in `.planning/REQUIREMENTS.md` (YAML-02 line) and
`02-01-SUMMARY.md` deviation #2, and the underlying intent ("every untouched byte preserved")
is fully verified.

---

_Verified: 2026-08-30_
_Verifier: Claude (gsd-verifier)_
