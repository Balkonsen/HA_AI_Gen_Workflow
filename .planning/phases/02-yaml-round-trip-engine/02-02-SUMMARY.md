---
phase: 02-yaml-round-trip-engine
plan: 02
subsystem: configtree
tags: [home-assistant-includes, include-graph, annotatedyaml, path-containment, cycle-detection, packages, fixtures]

requires:
  - phase: 02-yaml-round-trip-engine
    provides: "02-01: load_file / LoadedFile, build_span_index, ConfigTreeError + YamlError, ha_config_tree / ha_config_bad conftest fixtures, ruamel.yaml pin"
provides:
  - "haco.configtree.includes: SECRET_YAML, INCLUDE_TAGS (5 tags) + INCLUDE_FILE_TAG / INCLUDE_DIR_TAGS, find_dir_yaml() (HA-faithful recursive .yaml-only sorted scan skipping dotfiles + secrets.yaml), iter_include_refs(), ensure_contained() (ASVS V12 containment), resolve_include_targets()"
  - "haco.configtree.graph: frozen IncludeEdge / IncludeGraph with children() / parents() / reachable() / package_files() (package_files selects by node_path homeassistant->packages, not by tag)"
  - "haco.configtree.tree: FileNode (rel/path/text/data/spans/edits/dirty), ConfigTree (files keyed root-relative, node()/get()/source_text()), load_config_tree() - one DFS from configuration.yaml with an ordered loading-stack cycle guard"
  - "haco.errors: IncludeError / IncludeCycleError / IncludeEscapeError / MissingIncludeError under ConfigTreeError"
  - "tests/fixtures/ha_config_bad/{cycle,missing,escape}/ + escape_target.yaml negative fixtures"
affects: [02-03, 02-04, pull, analyze, apply, rollback]

actuals:
  tokens: 8200
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Include graph as a byproduct of the load DFS: one IncludeEdge per resolved target, !include_dir_* expanded to one edge per matched .yaml file"
    - "HA fidelity by re-implementation, not vendoring: find_dir_yaml mirrors annotatedyaml._find_files rule-for-rule (os.walk recursive, per-dir sorted(), *.yaml glob, dotfile + secrets.yaml skip); a total sort on top is stricter than HA, not divergent (RESEARCH A5)"
    - "ensure_contained() on every resolved target - single file AND the directory argument before os.walk - so an untrusted include string can never enumerate or load outside the config root (ASVS V12, RESEARCH Pitfall 9)"
    - "Ordered loading: list[Path] stack turns a back edge into IncludeCycleError naming the cycle in walk order, never RecursionError"
    - "package_files() selects package edges by node_path prefix (homeassistant, packages), so it works whether packages: is written !include_dir_named or as an explicit mapping of !include tags"

key-files:
  created:
    - "tests/test_configtree_graph.py - one focused test per HA _find_files rule + package discovery + graph-query/edge-set agreement"
    - "tests/fixtures/ha_config_bad/cycle/{configuration,ring_a,ring_b}.yaml - ring_a <-> ring_b include loop"
    - "tests/fixtures/ha_config_bad/missing/configuration.yaml - !include nowhere.yaml"
    - "tests/fixtures/ha_config_bad/escape/configuration.yaml + tests/fixtures/ha_config_bad/escape_target.yaml - !include ../escape_target.yaml"
  modified:
    - "tests/test_configtree_includes.py - added cycle / missing-target / containment-escape failure-mode tests (Task 3)"
    - "src/haco/configtree/{includes,graph,tree}.py + src/haco/errors.py + src/haco/configtree/__init__.py - landed whole in the Task 1 tracer commit 93710e8 (prior session)"

key-decisions:
  - "Task 1 (tracer) was committed in a prior session as 93710e8 before a rate limit; it already carried the full includes/graph/tree modules, the IncludeError family, IncludeGraph.package_files(), and the HA-faithful find_dir_yaml. Tasks 2 and 3 in this session were therefore confirm-and-cover: git diff 93710e8 -- src/ is empty, so both remaining commits are test-only."
  - "Task 3's failure paths (ordered loading-stack cycle guard, MissingIncludeError on absent single-file and absent directory targets, ensure_contained containment) were all built into the Task 1 tracer per the plan's <action> wording ('Confirm ... rather than Implement'). The Task 3 tests pass on first run because the implementation genuinely predates them, not because the tests are weak - each fixture exercises a distinct raise site."
  - "test_dir_include_outside_root_refused_before_walk added beyond the three named tests: calls resolve_include_targets directly with a !include_dir_merge_list tag and a '..' argument to prove containment is enforced before os.walk (threat T-02-07, acceptance criterion 'refused before os.walk runs')."
  - "Negative fixtures authored with LF endings via printf; tests/fixtures/** is -text in .gitattributes (from 02-01) so the bytes are checked out verbatim."

patterns-established:
  - "One dedicated passing test per HA directory-scan rule, named so VALIDATION.md's filter selects them (test_dir_scan_is_recursive / _yaml_only / _skips_dotfiles / _skips_secrets_yaml / _sorted_per_directory)"
  - "Include failure modes are typed ConfigTreeError subclasses whose message names the offending file + argument and never a !secret; asserted by is-not-RecursionError and is-not-sibling-error checks"

requirements-completed: [YAML-03]

coverage:
  - id: D1
    description: "load_config_tree(root) walks from configuration.yaml through every !include / !include_dir_* / packages: reference and loads each resolved target as its own editable FileNode with non-empty text and a non-empty span index"
    requirement: "YAML-03"
    verification:
      - kind: unit
        ref: "tests/test_configtree_includes.py#test_load_config_tree_reaches_every_file, test_every_file_node_is_editable"
        status: pass
    human_judgment: false
  - id: D2
    description: "The include graph carries one IncludeEdge per resolved target; !include_dir_* expands to one edge per matched .yaml file; every edge records parent, node_path, tag and child (all paths root-relative)"
    requirement: "YAML-03"
    verification:
      - kind: unit
        ref: "tests/test_configtree_includes.py#test_include_graph_has_one_edge_per_resolved_target"
        status: pass
    human_judgment: false
  - id: D3
    description: "find_dir_yaml matches annotatedyaml._find_files rule-for-rule: recursive (nested file present), .yaml-only (.yml absent), dotfiles skipped, secrets.yaml skipped, sorted per directory"
    requirement: "YAML-03"
    verification:
      - kind: unit
        ref: "tests/test_configtree_graph.py#test_dir_scan_is_recursive, test_dir_scan_yaml_only, test_dir_scan_skips_dotfiles, test_dir_scan_skips_secrets_yaml, test_dir_scan_sorted_per_directory"
        status: pass
    human_judgment: false
  - id: D4
    description: "packages: files are discoverable through the graph - IncludeGraph.package_files() returns exactly the package fixture files, selected by node_path (homeassistant, packages) rather than by tag"
    requirement: "YAML-03"
    verification:
      - kind: unit
        ref: "tests/test_configtree_graph.py#test_packages_are_discovered"
        status: pass
    human_judgment: false
  - id: D5
    description: "children() / parents() / reachable() agree with graph.edges; reachable() equals the ConfigTree.files key set; absolute and root-relative path arguments resolve to the same answer"
    requirement: "YAML-03"
    verification:
      - kind: unit
        ref: "tests/test_configtree_graph.py#test_graph_queries_agree_with_edges"
        status: pass
    human_judgment: false
  - id: D6
    description: "An include cycle raises IncludeCycleError naming the files in walk order (not RecursionError); a missing target raises MissingIncludeError naming parent + argument; a target resolving outside the config root raises IncludeEscapeError and is never loaded, with the directory variant refused before os.walk runs"
    requirement: "YAML-03"
    verification:
      - kind: unit
        ref: "tests/test_configtree_includes.py#test_include_cycle_raises_configtree_error, test_missing_include_target_raises, test_include_outside_root_is_refused, test_dir_include_outside_root_refused_before_walk"
        status: pass
    human_judgment: false
  - id: D7
    description: "secrets.yaml is never a graph node and is never opened (asserted absent from tree.files and from every edge child)"
    requirement: "YAML-03"
    verification:
      - kind: unit
        ref: "tests/test_configtree_graph.py#test_dir_scan_skips_secrets_yaml; tests/test_configtree_includes.py#test_load_config_tree_reaches_every_file"
        status: pass
    human_judgment: false

duration: 20min
completed: 2026-08-30
status: complete
---

# Phase 2 Plan 02: YAML Round-Trip Engine - Whole-Tree Include Engine Summary

**`load_config_tree()` walks from `configuration.yaml` through every `!include` / `!include_dir_*` / `packages:` reference using Home Assistant's own `annotatedyaml._find_files` rules, loads each resolved target as its own editable `FileNode`, emits the include graph as a byproduct of that DFS, and fails by type - `IncludeCycleError` / `MissingIncludeError` / `IncludeEscapeError` - on every way the walk can go wrong.**

## Performance

- **Duration:** ~20 min (this resumed session; Task 1 executed in a prior session before a rate limit)
- **Completed:** 2026-08-30
- **Tasks:** 3 (1 tracer + 2 TDD) - Task 1 committed in a prior session as `93710e8`
- **Files created/modified:** 13 across the plan (7 in this session: 1 test module, 6 negative fixtures, 1 test module extended)
- **Tests:** 87 pass (was 76 at end of 02-01; +7 graph tests, +4 include failure-mode tests)

## Accomplishments

- `haco.configtree.includes`: `SECRET_YAML`, the five include tags, `find_dir_yaml()` re-implementing `annotatedyaml._find_files` (recursive `os.walk`, per-directory `sorted()`, `*.yaml` glob only, dotfile + dot-directory filter, `secrets.yaml` basename skip, plus a whole-list sort that is stricter than HA), `iter_include_refs()` yielding `(node_path, tag, argument)` for every include-tagged scalar, `ensure_contained()` enforcing config-root containment, and `resolve_include_targets()` joining the argument onto the *including file's* directory HA-style.
- `haco.configtree.graph`: frozen `IncludeEdge` and `IncludeGraph` with `children()`, `parents()`, `reachable()` and `package_files()` - the last selecting package edges by `node_path` prefix `(homeassistant, packages)` so it is agnostic to how `packages:` is spelled.
- `haco.configtree.tree`: `FileNode` (root-relative `rel`, absolute `path`, `text`, `data`, `spans`, `edits`, `dirty`), `ConfigTree` (`files` keyed root-relative, `node()` / `get()` / `source_text()`), and `load_config_tree()` - one DFS with an ordered `loading` stack and a `done` map, one `IncludeEdge` appended per resolved target.
- `haco.errors`: `IncludeError` and its three children under `ConfigTreeError`, each message naming the parent file and the include argument and never echoing a `!secret`.
- Negative fixtures under `tests/fixtures/ha_config_bad/`: `cycle/` (a `ring_a` <-> `ring_b` loop), `missing/` (`!include nowhere.yaml`), `escape/` + `escape_target.yaml` (`!include ../escape_target.yaml`, one level above the load root).
- `tests/test_configtree_graph.py`: one focused, filter-selectable test per `_find_files` rule, plus package discovery and graph-query/edge-set agreement.
- `tests/test_configtree_includes.py` extended with the three named failure-mode tests plus `test_dir_include_outside_root_refused_before_walk`.

## Task Commits

1. **Task 1 (tracer): walk configuration.yaml through every include to a loaded tree** - `93710e8` (feat) - *prior session; includes/graph/tree modules, IncludeError family, package_files(), HA-faithful find_dir_yaml, tracer tests*
2. **Task 2 (test): per-rule HA directory-scan tests + graph query surface** - `b687043` (test) - *`git diff 93710e8 -- src/` is empty: `find_dir_yaml` and `package_files()` already satisfied every rule, so this task is its dedicated coverage*
3. **Task 3 (test): typed errors for include cycle, missing target, containment escape** - `5a5d90e` (test) - *six negative fixtures + four failure-mode tests; the raise sites were built into the Task 1 tracer per the plan's confirm-not-implement wording*

**Plan metadata:** this docs commit (SUMMARY + STATE + ROADMAP + REQUIREMENTS).

## Files Created/Modified

- `src/haco/configtree/includes.py` - HA include resolution (landed in `93710e8`)
- `src/haco/configtree/graph.py` - `IncludeEdge` / `IncludeGraph` + queries (landed in `93710e8`)
- `src/haco/configtree/tree.py` - `FileNode` / `ConfigTree` / `load_config_tree` (landed in `93710e8`)
- `src/haco/errors.py` - `IncludeError` family (landed in `93710e8`)
- `src/haco/configtree/__init__.py` - re-exports (landed in `93710e8`)
- `tests/test_configtree_graph.py` - new, 7 tests
- `tests/test_configtree_includes.py` - +4 failure-mode tests (7 tests total)
- `tests/fixtures/ha_config_bad/cycle/{configuration,ring_a,ring_b}.yaml`, `.../missing/configuration.yaml`, `.../escape/configuration.yaml`, `.../escape_target.yaml` - new negative fixtures

## Decisions Made

See `key-decisions` in the frontmatter. In short: Task 1 (committed `93710e8` in a prior session) already carried the full module set and every Task 3 raise site, so Tasks 2 and 3 this session were test-only (`git diff 93710e8 -- src/` is empty); one extra test (`test_dir_include_outside_root_refused_before_walk`) was added to prove the directory-variant containment check fires before `os.walk`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Removed a dead `_child_paths` helper from the partial `tests/test_configtree_graph.py` artifact**
- **Found during:** Task 2 (inspecting the prior session's uncommitted partial test module).
- **Issue:** The partially-written file carried an unused module-level `_child_paths()` helper with a blanket `# type: ignore[attr-defined]`; every test used an inline set-comprehension instead. Dead code carrying a type-ignore is a latent lint/mypy hazard.
- **Fix:** Deleted the helper; all seven tests already used the inline form.
- **Files modified:** `tests/test_configtree_graph.py`
- **Verification:** `uv run ruff check` + `uv run black --check` + `uv run mypy` + the file's 7 tests all pass.
- **Committed in:** `b687043` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking - dead-code cleanup of a partial artifact).
**Impact on plan:** None on scope. The plan's Task 3 `<action>` is written as "Confirm ... rather than implement", and confirmation held: the Task 1 tracer already implemented the ordered loading-stack cycle guard, `MissingIncludeError` on absent single-file *and* directory targets, and `ensure_contained` containment. No source changes were needed in Tasks 2 or 3.

## Issues Encountered

- The prior session's note said "83 tests pass" at `93710e8`; the actual count at that commit is 76 (the 7-test `tests/test_configtree_graph.py` was uncommitted, bringing the working tree to 83). Reconciled by counting with and without the untracked file; no action needed.
- Git reports `LF will be replaced by CRLF` for `tests/*.py` on this Windows checkout (`core.autocrlf=true`) - as in the Phase 1 / 02-01 summaries, the quality gate is unaffected. The six new fixture files under `tests/fixtures/` are exempt via `.gitattributes -text` (authored and committed with LF `0a` bytes, verified with `xxd`).
- `gsd-core/bin` is absent in this worktree, but `gsd-tools.cjs` is reachable at `~/.claude/gsd-core/bin/` (v1.12.0, identity-verified); STATE / ROADMAP / REQUIREMENTS were updated through it.

## Next Phase Readiness

- **02-03** (mutation API + splice writer) can consume `load_config_tree()`, `ConfigTree` (`node()` / `get()` / `source_text()`), `FileNode.edits` / `dirty`, and the `IncludeGraph` to decide which files are in play. `FileNode.spans` (from 02-01) + `Span.kind` / `Span.unspliceable` drive the splice.
- **02-04** consumes the include graph for its dir-based rules.
- No blockers introduced. The pre-existing Phase 01 `01-04` `checkpoint:human-verify` remains outstanding (unrelated to this plan).

## Known Stubs

None. `load_config_tree()` returns fully loaded `FileNode`s (non-empty `text` + `spans`, asserted by `test_every_file_node_is_editable`); nothing is deferred or placeholdered at plan end.

## Self-Check: PASSED

- `tests/test_configtree_graph.py`, `tests/fixtures/ha_config_bad/cycle/{configuration,ring_a,ring_b}.yaml`, `.../missing/configuration.yaml`, `.../escape/configuration.yaml`, `.../escape_target.yaml` all present on disk.
- Commits `93710e8`, `b687043`, `5a5d90e` in `git log`.
- `uv run ruff check . && uv run black --check . && uv run mypy && uv run pytest -q` exits 0 (87 passed, mypy strict clean on 31 files).
- `uv run python -c "from haco.configtree import load_config_tree; import pathlib; t = load_config_tree(pathlib.Path('tests/fixtures/ha_config')); print(len(t.files), len(t.graph.edges), len(t.graph.package_files()))"` prints `12 11 2`.

---
*Phase: 02-yaml-round-trip-engine*
*Completed: 2026-08-30*
