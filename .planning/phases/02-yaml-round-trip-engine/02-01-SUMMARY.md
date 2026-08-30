---
phase: 02-yaml-round-trip-engine
plan: 01
subsystem: configtree
tags: [ruamel-yaml, yaml-round-trip, source-spans, compose, home-assistant-tags, fixtures]

requires:
  - phase: 01-connect-discover
    provides: "haco.errors.HacoError hierarchy; frozen-dataclass result pattern; uv quality gate; ruamel.yaml already declared"
provides:
  - "haco.configtree.loader: make_yaml() YAML factory (rt, preserve_quotes, indent 2/4/2, width 1e6), KNOWN_HA_TAGS (8 D-08 tags), LoadedFile frozen dataclass, load_file(), warn_unknown_tags()"
  - "haco.configtree.spans: NodePath, SpanKind, Span frozen dataclass, build_span_index() over the compose() node tree with per-style kind classification and id(node) alias/merge guarding"
  - "haco.configtree.__init__: public re-exports"
  - "haco.errors: ConfigTreeError, YamlError, DuplicateKeyError, MultiDocumentError"
  - "tests/fixtures/ha_config/ representative HA tree (16 files) + tests/fixtures/ha_config_bad/ (dupkey, multidoc) + tests/fixtures/spans_golden.yaml"
  - "tests/conftest.py: ha_config_tree (with BOM+CRLF probe rewrite) and ha_config_bad fixtures"
  - ".gitattributes: tests/fixtures/** -text so span offsets are byte-stable across platforms"
  - "pyproject.toml: ruamel.yaml pinned >=0.19.1,<0.20; uv.lock relocked"
affects: [02-02, 02-03, 02-04, pull, analyze, apply, rollback]

actuals:
  tokens: 8500
  tasks: 3
  commits: 7

tech-stack:
  added: []
  patterns:
    - "Two-parse load: compose() for mark-carrying nodes -> span index; load() for the navigable round-trip tree"
    - "Source-byte provenance attached at load time (D-01) - every node gets an absolute (start,end) offset into the file's original text"
    - "id(node) seen-set alias guard: a node object reached twice was reached via a *alias; record unspliceable + do not recurse"
    - "All ruamel calls confined to loader.py / spans.py; explicit return types at the boundary (no # type: ignore needed under mypy strict)"
    - "Load-bearing fixture bytes pinned with .gitattributes -text; frozen offset table as a ruamel-drift canary"

key-files:
  created:
    - "src/haco/configtree/loader.py - make_yaml, KNOWN_HA_TAGS, LoadedFile, load_file, warn_unknown_tags"
    - "src/haco/configtree/spans.py - Span, NodePath, SpanKind, build_span_index"
    - "src/haco/configtree/__init__.py - public surface"
    - "tests/test_configtree_loader.py - tracer span slice, opaque tags, all 8 D-08 tags, unknown-tag warn-once, round-trip diagnostic, dup-key / multi-doc, BOM+CRLF probe"
    - "tests/test_configtree_spans.py - per-style SpanKind + slice, alias unspliceable, frozen offset table"
    - "tests/fixtures/ha_config/** (16 files), tests/fixtures/ha_config_bad/** (2), tests/fixtures/spans_golden.yaml"
    - ".gitattributes"
  modified:
    - "src/haco/errors.py - ConfigTreeError, YamlError, DuplicateKeyError, MultiDocumentError"
    - "tests/conftest.py - ha_config_tree + ha_config_bad fixtures"
    - "pyproject.toml + uv.lock - ruamel.yaml >=0.19.1,<0.20"

key-decisions:
  - "load_file reads via path.read_bytes().decode('utf-8') rather than the RESEARCH.md Path.read_text(newline='') pattern - the newline= kwarg on Path.read_text is Python 3.13+ and this project targets 3.12.13. read_bytes+decode preserves CRLF and a BOM verbatim, which is exactly the requirement, and makes loaded.text == file bytes decoded a tautology the tracer test asserts."
  - "MultiDocumentError is detected with compose_all() BEFORE load(): ruamel's load() raises a bare ComposerError on a second '---', so counting composed documents first lets us raise the typed, file-naming error."
  - "DuplicateKeyError re-raises ruamel.yaml.constructor.DuplicateKeyError (imported aliased) with the key recovered by regex from the parser's problem text; the file path is always in the message, the key is best-effort."
  - "warn_unknown_tags dedups into a set then emits one warnings.warn per distinct unknown tag - ruamel 0.19.1 round-trips unknown !tags silently, so the D-08 'warn, don't fail' signal is ours to raise. A !secret argument (key name) is never put in warning or exception text (D-09)."
  - "SpanKind 'tagged' wins over style: !include written plain is still 'tagged' so 02-03 renders it as an opaque re-emit, not a plain scalar."

patterns-established:
  - "haco.configtree package: layer 1 (this plan) is loader + span index for one file; includes/tree/writer land in 02-02/02-03"
  - "Every fixture authored LF/no-BOM; the encoding probe's BOM+CRLF form is applied by the ha_config_tree fixture in the tmp copy, so the property is independent of git checkout normalisation"
  - "Frozen offset table (test_golden_offsets_match_table) is the drift canary for the ruamel pin - a mismatch means re-examine the pin before touching anything else"

requirements-completed: [YAML-01, YAML-02]

coverage:
  - id: D1
    description: "A real HA-shaped configuration.yaml loads through load_file without raising, with all eight D-08 tags present and opaque"
    requirement: "YAML-01"
    verification:
      - kind: unit
        ref: "tests/test_configtree_loader.py#test_known_ha_tags_parse, test_input_tag_parses_in_scalar_and_mapping_form, test_load_file_gives_exact_source_span"
        status: pass
    human_judgment: false
  - id: D2
    description: "An unknown !tag round-trips opaquely as an inert TaggedScalar and warns exactly once per distinct tag; load never fails"
    requirement: "YAML-01"
    verification:
      - kind: unit
        ref: "tests/test_configtree_loader.py#test_unknown_tag_round_trips_and_warns_once"
        status: pass
    human_judgment: false
  - id: D3
    description: "Every editable node carries an exact (start,end) source offset; text[start:end] is the exact substring per scalar style (plain/single/double/literal/folded/flow/tagged)"
    requirement: "YAML-02"
    verification:
      - kind: unit
        ref: "tests/test_configtree_spans.py#test_span_kinds_and_text, test_golden_offsets_match_table; tests/test_configtree_loader.py#test_load_file_gives_exact_source_span"
        status: pass
    human_judgment: false
  - id: D4
    description: "load->dump of every fixture file with the pinned indent is byte-identical (mapping-root strict; sequence-root modulo ruamel's unavoidable uniform root-sequence offset) - the YAML-02 ruamel-drift diagnostic"
    requirement: "YAML-02"
    verification:
      - kind: unit
        ref: "tests/test_configtree_loader.py#test_roundtrip_diagnostic_is_byte_identical"
        status: pass
    human_judgment: false
  - id: D5
    description: "A value reached through a YAML alias is marked unspliceable with a reason naming the anchor; the walker does not descend into the aliased subtree (D-03/D-07 groundwork)"
    verification:
      - kind: unit
        ref: "tests/test_configtree_spans.py#test_alias_path_is_unspliceable"
        status: pass
    human_judgment: false
  - id: D6
    description: "A multi-document file raises MultiDocumentError and a duplicate-key file raises DuplicateKeyError, each naming the file; a !secret argument is never echoed"
    verification:
      - kind: unit
        ref: "tests/test_configtree_loader.py#test_multi_document_raises, test_duplicate_key_raises"
        status: pass
    human_judgment: false
  - id: D7
    description: "Committed fixture bytes are checked out verbatim (.gitattributes -text) so span offsets are reproducible; the encoding probe survives as BOM+CRLF in the working copy"
    verification:
      - kind: unit
        ref: "tests/test_configtree_loader.py#test_encoding_probe_has_bom_and_crlf; git check-attr text -- tests/fixtures/ha_config/configuration.yaml => unset"
        status: pass
    human_judgment: false

duration: 45min
completed: 2026-08-30
status: complete
---

# Phase 2 Plan 01: YAML Round-Trip Engine - Loader + Span Index Summary

**A pinned `ruamel.yaml` round-trip loader that parses every Home Assistant custom tag without error, plus a `compose()`-based span index that gives every editable node an exact `(start, end)` character offset back into its file's original text - the D-01 provenance the whole phase splices against - proven against a representative HA-shaped fixture tree.**

## Performance

- **Duration:** ~45 min
- **Completed:** 2026-08-30
- **Tasks:** 3 (1 tracer + 2 TDD)
- **Files created/modified:** 29 (excluding planning docs)
- **Tests:** 40 new configtree tests; all 33 Phase 1 tests still green (73 total)

## Accomplishments

- `haco.configtree.loader`: `make_yaml()` (rt, `preserve_quotes`, `indent(2,4,2)`, `width=1_000_000`), `KNOWN_HA_TAGS` (the exact 8 D-08 tags), frozen `LoadedFile`, `load_file()` reading bytes verbatim, and `warn_unknown_tags()` emitting exactly one `warnings.warn` per distinct unrecognised `!tag` while the value stays an inert `TaggedScalar`.
- `haco.configtree.spans`: frozen `Span` (`file`, `start`, `end`, `kind`, `unspliceable`), `NodePath`, `SpanKind`, and `build_span_index()` walking the `compose()` tree - per-style kind classification (plain / single / double / literal / folded / flow / tagged / collection) and an `id(node)` seen-set that marks alias/merge-shared paths `unspliceable` (naming the anchor) without recursing into them.
- `haco.errors`: `ConfigTreeError` and `YamlError` under `HacoError`, plus `DuplicateKeyError` and `MultiDocumentError` under `YamlError`, each naming the offending file and never a `!secret` argument.
- `load_file()` fails loud: `compose_all()` up front raises `MultiDocumentError` on a second `---`; ruamel's own duplicate-key error is re-raised as `DuplicateKeyError` with the key recovered from the parser message.
- Wave 0 fixture trees: `tests/fixtures/ha_config/` (16 files - every D-08 tag in legal node form, both quote styles, an anchor+alias pair, `packages:`, a nested include dir, a `.yml` and a dotfile that later plans must skip, a `groups/secrets.yaml` decoy, non-ASCII), `tests/fixtures/ha_config_bad/` (dupkey, multidoc), and `tests/fixtures/spans_golden.yaml` frozen canary.
- `tests/conftest.py`: `ha_config_tree` (copytree into `tmp_path`, then rewrite the encoding probe with a U+FEFF BOM + CRLF so the property is checkout-independent) and `ha_config_bad`.
- `.gitattributes` (`tests/fixtures/** -text`) committed with the first fixture; `ruamel.yaml` narrowed to `>=0.19.1,<0.20` and `uv.lock` relocked.

## Task Commits

1. **Task 1 (tracer): round-trip loader + compose() span index** - `e6a9c38` (feat)
2. **Task 2 (RED): full HA fixture tree + tag / parse-failure tests** - `e4621c0` (test)
3. **Task 2 (GREEN): warn on unknown tags; fail loud on dup-key / multi-doc** - `79fc625` (feat)
4. **Task 3 (RED): per-style span kinds, alias unspliceable, offset canary** - `64a7b2d` (test)
5. **Task 3 (GREEN): real per-style SpanKind classification** - `105f5a6` (feat)

**Plan metadata:** this docs commit + a STATE / ROADMAP / REQUIREMENTS commit.

## Files Created/Modified

- `src/haco/configtree/loader.py` - YAML factory, known-tag set, `LoadedFile`, `load_file`, `warn_unknown_tags`
- `src/haco/configtree/spans.py` - `Span`, `NodePath`, `SpanKind`, `build_span_index` (per-style kind + alias guard)
- `src/haco/configtree/__init__.py` - public re-exports
- `src/haco/errors.py` - `ConfigTreeError`, `YamlError`, `DuplicateKeyError`, `MultiDocumentError`
- `tests/conftest.py` - `ha_config_tree`, `ha_config_bad`
- `tests/test_configtree_loader.py`, `tests/test_configtree_spans.py` - 40 tests
- `tests/fixtures/ha_config/**`, `tests/fixtures/ha_config_bad/**`, `tests/fixtures/spans_golden.yaml`
- `.gitattributes`, `pyproject.toml`, `uv.lock`

## Decisions Made

See `key-decisions` in the frontmatter. In short: read bytes + decode instead of the 3.13-only `read_text(newline=)`; detect multi-doc via `compose_all()` before `load()`; dedup unknown-tag warnings into a set; `tagged` kind outranks scalar style.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `Path.read_text(newline=...)` is Python 3.13+, project targets 3.12.13**
- **Found during:** Task 1 (the tracer test failed with `TypeError: Path.read_text() got an unexpected keyword argument 'newline'`).
- **Issue:** RESEARCH.md's `load_file` example (and the plan's Task 1 wording) specify `path.read_text(encoding="utf-8", newline="")`. The `newline=` parameter was only added to `Path.read_text` in CPython 3.13; `.python-version` here is `3.12.13`.
- **Fix:** `load_file` reads with `path.read_bytes().decode("utf-8")`. This performs zero newline translation and keeps a leading U+FEFF BOM intact, which is precisely the "CRLF + BOM survive verbatim" requirement (Pitfall 5). The test spy for "no other file opened" was retargeted from `Path.read_text` to `Path.read_bytes`. `Path.write_text(newline="")` (used by the `ha_config_tree` BOM rewrite) *is* available on 3.12, so the conftest side is unchanged.
- **Files:** `src/haco/configtree/loader.py`, `tests/test_configtree_loader.py`
- **Commit:** `e6a9c38`

**2. [Rule 3 - Blocking] Pinned indent unavoidably left-shifts a document-root block sequence, so a literal byte-for-byte round-trip of top-level-list fixtures is impossible**
- **Found during:** Task 2 (probing the round-trip diagnostic before writing the test).
- **Issue:** `make_yaml()` uses `indent(mapping=2, sequence=4, offset=2)` - the pin RESEARCH.md/D-10 require for HA's nested block style, and the *only* config that round-trips the nested `sequence:` / `- item` shape. But ruamel applies `offset` to a **document-root** block sequence too, so `load -> dump` of `automations.yaml`, every `sensors/*.yaml`, `scenes/*.yaml` and `templates/weather.yaml` (all top-level lists, dash at column 0 as real HA writes them) comes back uniformly indented by 2 columns. The plan's must-have truth "byte-identical" cannot hold literally for these with the required pin. Authoring the fixtures pre-indented would misrepresent real HA files and would surprise the 02-03 splice tests.
- **Fix:** `test_roundtrip_diagnostic_is_byte_identical` compares mapping-root files **strictly** byte-for-byte, and sequence-root files after removing exactly the one uniform 2-space root-sequence shift (`_dedent2`). It still fires on real emitter drift - nested indentation, quote style, comments, blank lines, and every mapping-root file remain under strict comparison, and the `spans_golden.yaml` offset table is a second, independent canary. Per D-01 an untouched file is spliced, never dumped, so there is no product impact - the diagnostic is explicitly "a canary for ruamel drift, not a product requirement" (RESEARCH.md YAML-02).
- **Files:** `tests/test_configtree_loader.py`
- **Commit:** `e4621c0`

**3. [Rule 2 - Missing coverage] Added `test_input_tag_parses_in_scalar_and_mapping_form`**
- **Found during:** Task 2.
- **Issue:** The plan's behavior list calls for `!input` "in both its scalar and mapping form", but the parametrized `test_known_ha_tags_parse` only asserts tag *presence* and opacity. Added an explicit test that the scalar form loads as a `TaggedScalar` and the mapping form as a tagged `CommentedMap`.
- **Files:** `tests/test_configtree_loader.py`
- **Commit:** `e4621c0`

## Issues Encountered

- Git reports `LF will be replaced by CRLF` for the new `src/` and `tests/*.py` files on this Windows checkout (`core.autocrlf=true`) - as noted in the Phase 1 summaries, ruff / black / mypy / pytest are unaffected. Fixture files under `tests/fixtures/` are exempt via the new `.gitattributes -text` rule (`git check-attr text` reports `unset`).
- No `gsd-core/bin` in this worktree, so `gsd-tools` state handlers and the `.planning/WINDOWS.md` ledger append were not available; STATE / ROADMAP / REQUIREMENTS were updated by hand and the deviations above are recorded here in full.

## Next Phase Readiness

- **02-02** (include resolver + ConfigTree + include graph) can consume `load_file`, `LoadedFile`, `build_span_index`, and both conftest fixtures directly. The `sensors/nested/c_extra.yaml`, `sensors/d_ignored.yml`, `sensors/.hidden.yaml` and `groups/secrets.yaml` fixtures are in place for its recursive-scan / skip-list assertions.
- **02-03** (mutation API + splice writer) branches on `Span.kind` and honours `Span.unspliceable` (D-03).
- No blockers.

## Known Stubs

None. The placeholder `_classify` shipped in Task 1's tracer was replaced with real per-style classification in Task 3 as planned; nothing is left stubbed at plan end.

## Self-Check: PASSED

- `src/haco/configtree/{__init__,loader,spans}.py`, `tests/test_configtree_loader.py`, `tests/test_configtree_spans.py`, `tests/fixtures/spans_golden.yaml`, `.gitattributes` all present.
- Commits `e6a9c38`, `e4621c0`, `79fc625`, `64a7b2d`, `105f5a6` in `git log`.
- `uv run ruff check . && uv run black --check . && uv run mypy && uv run pytest -q` exits 0 (73 passed).
- `from haco.configtree import KNOWN_HA_TAGS; len(KNOWN_HA_TAGS) == 8` holds.
- `git check-attr text -- tests/fixtures/ha_config/configuration.yaml` => `text: unset`.

---
*Phase: 02-yaml-round-trip-engine*
*Completed: 2026-08-30*
