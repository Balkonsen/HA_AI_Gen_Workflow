# Phase 2: YAML Round-Trip Engine - Research

**Researched:** 2026-08-30
**Domain:** Comment/tag-preserving YAML loading, source-span provenance, surgical text splicing, Home Assistant `!include*` / `packages:` semantics
**Confidence:** HIGH for the ruamel mechanics (verified by live probe against the installed `ruamel.yaml 0.19.1`) and HA include semantics (verified against HA's own loader source). MEDIUM for `packages:` merge details and a few HA constants not opened byte-for-byte this session.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** When a node changes, rewrite the containing file by **surgical text splice** — locate the changed node's source byte range and replace only that span; every other byte of the file (comments, blank lines, quote style, indentation, trailing newline) stays exactly as read from disk. Do **not** do a full `ruamel` dump of a touched file.
- **D-02:** `ruamel.yaml` (`typ='rt'`, `preserve_quotes=True`) is still the parser and the source of line/column data (`.lc`) used to compute spans; it is just never used as the *emitter* for a touched file. Serializing a *new* node value (the replacement text for the spliced span) uses ruamel with HA's 2-space block style so the inserted text matches surrounding conventions.
- **D-03:** If the changed node's byte range cannot be resolved unambiguously (e.g. a value produced by an `!include_dir_*` merge that has no single source span), the write fails loudly for that node with a clear message rather than falling back to a whole-file dump.
- **D-04:** Follow every `!include`, `!include_dir_list`, `!include_dir_merge_list`, `!include_dir_named`, `!include_dir_merge_named` transitively from `configuration.yaml`, and also resolve `packages:` entries. Load every resolved target file into the ConfigTree as its own **editable** file node (path -> root node + original bytes + span index).
- **D-05:** The include **graph** (YAML-03) is a byproduct of the load walk: an edge `parent file --tag--> child path(s)`, with the `!include_dir_*` variants expanding to one edge per matched file (directory scan **sorted by filename**, non-recursive — matches HA semantics). `secrets.yaml` is **not** a node in the graph in this phase.
- **D-06:** `!include*` tag nodes themselves round-trip as **opaque tagged scalars** — they re-emit verbatim; includes are never inlined into the parent file. The child file's content is edited in the child file.
- **D-07:** Anchors/aliases (`&x` / `*x`) are preserved within a file but never resolved across `!include` boundaries (HA merges post-include).
- **D-08:** Register constructors + representers for `!secret`, `!include`, `!include_dir_list`, `!include_dir_merge_list`, `!include_dir_named`, `!include_dir_merge_named`, `!env_var`, `!input` before parsing. Unknown `!` tags also round-trip opaquely rather than crashing (warn, don't fail).
- **D-09:** `!secret <key>` stays an opaque tagged scalar. `secrets.yaml` is **not** loaded, parsed, or resolved in Phase 2.
- **D-10:** Idempotency (YAML-05) is proven at engine level: **no-op mutation stability** —
  1. `load -> serialize -> load -> serialize` on a real fixture tree is a fixed point (byte-for-byte per file);
  2. an **empty** change set rewrites **zero** files on disk;
  3. apply-a-mutation-then-revert leaves every file byte-identical to the pre-mutation state.

### Claude's Discretion

- In-memory API shape (path tuples / visitor / dotted keys), the span-index data structure, and how original bytes are cached (per-file string vs mmap) are the planner's/executor's call, as long as D-01..D-10 hold.
- Fixture design: a representative HA config tree covering every tag in D-08, nested includes, `include_dir_*` directories, comments, both quote styles, anchors within a file, and a `packages:` block.

### Deferred Ideas (OUT OF SCOPE)

- Secret resolution / `secrets.yaml` parsing / redaction-on-send — later phase.
- Reload-changed-domains-without-restart — v2 (API-02).
- Any analysis/optimization proposal engine — later phase; YAML-05's "zero proposed changes" against a real analyzer is re-verified then.
- Following anchors/aliases across include boundaries — explicitly rejected (D-07).
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| YAML-01 | Loader parses HA custom tags (`!secret`, `!include`, `!include_dir_list`, `!include_dir_merge_list`, `!include_dir_named`, `!include_dir_merge_named`, `!env_var`, `!input`) without error | `ruamel.yaml 0.19.1` round-trip mode already parses every one of these as a `TaggedScalar` (scalar form) or a tagged `CommentedMap`/`CommentedSeq` (collection form) with **no constructor registration required** and re-emits them byte-identical (verified probe). D-08's explicit registration is still recommended so the *known* set is enumerated and unknown tags get a warning. |
| YAML-02 | Load -> dump of an untouched file is byte-identical | Given D-01, an untouched file is **never dumped** — the engine returns its original bytes verbatim. The requirement is satisfied by "don't rewrite untouched files" (YAML-04), not by fighting ruamel's emitter. A defensive round-trip check (`y.indent(mapping=2, sequence=4, offset=2)` + `preserve_quotes`) is byte-identical for HA-style config in the probe, and is worth keeping as a *diagnostic* only. |
| YAML-03 | Tool builds the include graph linking configuration.yaml to every included file | Include graph = DFS byproduct of the load walk. HA's own resolution algorithm is quoted verbatim below (path join relative to the *including* file's directory; `_find_files` is recursive `os.walk`, `sorted()` per directory, `*.yaml` only, `secrets.yaml` and dotfiles skipped). Cycle detection via a "currently-loading" stack. |
| YAML-04 | Only files containing an approved change are rewritten; all others left untouched on disk | Per-file dirty flag; writer iterates only dirty files; atomic temp+rename. Verified splice technique below changes only the target span. |
| YAML-05 | Re-running analysis on an already-optimized tree yields zero proposed changes (idempotent) | D-10 redefines this for Phase 2 as no-op mutation stability (fixed-point serialize, empty-changeset = 0 writes, apply-then-revert = byte-identical). All three are testable against the fixture tree with the splice engine. |
</phase_requirements>

---

## Summary

The phase hinges on one mechanism: **every editable scalar/collection value must carry an unambiguous `(start, end)` character offset back into its origin file's original text**, so a mutation can be applied as `original[:start] + rendered_new_value + original[end:]` with every other byte untouched (D-01).

The good news from live probing against the **installed `ruamel.yaml 0.19.1`**: `YAML().compose(text)` returns a PyYAML-compatible node tree in which **every node — `ScalarNode`, `MappingNode`, `SequenceNode`, and tagged variants — exposes `start_mark.index` and `end_mark.index` as absolute character offsets into the source string.** These offsets are exact and exclude trailing whitespace and trailing comments for plain/quoted scalars, include the delimiters for flow collections, and span through the terminating newline for block scalars. This is the span-provenance primitive the phase needs, and it is *not* the same thing as `CommentedMap.lc` (which gives only *start* line/col and no end).

The architecture is therefore: parse each file **twice** — once with `compose()` to build a `path -> Span` index with full start/end offsets, once with `load()` (round-trip) to get the `CommentedMap`/`CommentedSeq` tree the caller navigates and reads (values, quote styles, comments). A mutation looks up the span by path, renders the replacement scalar with ruamel (quote-style-aware), splices against the file's cached original text, and marks the file dirty. Only dirty files are written, atomically.

Home Assistant does **not** use ruamel — it uses a PyYAML `SafeLoader` subclass in the `annotatedyaml` package. Phase 2 re-implements HA's `!include*` / `packages:` resolution semantics on top of ruamel. Those semantics are pinned from HA's own source below. **One locked assumption in CONTEXT.md is contradicted by that source: HA's directory includes are recursive (`os.walk`), not "non-recursive" as D-05 states** — see the flag in `## Common Pitfalls` and `## Open Questions`.

**Primary recommendation:** Build a `haco.configtree` package with four layers — (1) a ruamel loader wrapper + `compose()`-based span-index builder for a single file; (2) an include resolver that walks from `configuration.yaml`, loads every target as its own editable file node, and emits the include graph with cycle detection; (3) a mutation API + surgical-splice writer that only rewrites dirty files atomically and fails loudly on ambiguous spans (D-03); (4) a no-op-stability harness proving D-10. Pin `ruamel.yaml>=0.19.1,<0.20` and `y.indent(mapping=2, sequence=4, offset=2)`.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Parse a YAML file preserving comments/quotes/anchors | Library (`haco.configtree.loader`) | — | Pure in-process; ruamel round-trip mode |
| Source-span provenance (`path -> (start,end)`) | Library (`haco.configtree.spans`) | — | `ruamel.yaml.compose()` node marks; no I/O |
| Resolve `!include*` / `packages:` transitively | Library (`haco.configtree.includes`) | Filesystem (read-only, local working copy) | Re-implements HA semantics; operates on the pulled local tree, never the live host |
| Include graph + cycle detection | Library (`haco.configtree.graph`) | — | DFS byproduct of the resolve walk |
| Mutate a node by path | Library (`haco.configtree.tree`) | — | In-memory; records intent, does not touch disk |
| Write back (surgical splice, dirty-only, atomic) | Library (`haco.configtree.writer`) | Filesystem (local working copy) | temp+rename; Phase 5 owns writing to the *live* host |
| Idempotency / no-op stability proof | Test harness | — | Exercises the whole stack against a fixture tree |

Nothing in this phase talks to SSH, the live host, or `secrets.yaml`. It is a library plus tests exercised against fixture trees (per CONTEXT `<domain>`).

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `ruamel.yaml` | `>=0.19.1,<0.20` (installed: **0.19.1**) | Round-trip parse; `compose()` for span marks; render replacement scalars | Only mature comment/anchor/key-order-preserving YAML round-tripper for Python; already the deciding factor for the language choice (PROJECT.md). `[VERIFIED: local probe, ruamel.yaml 0.19.1]` |
| stdlib `pathlib` / `os` | 3.12 | Directory walk for `!include_dir_*`, path resolution | HA uses `os.walk` + `os.path.join`; match it exactly for fidelity |
| stdlib `dataclasses` | 3.12 | Frozen result types (`ConfigTree`, `IncludeGraph`, `Span`, `FileNode`) | Phase 1 established the frozen-dataclass result pattern (`CmdResult`, `HostFacts`, `CheckResult`) |
| stdlib `warnings` | 3.12 | Emit the "unknown `!` tag" warning (D-08) | ruamel does **not** warn on unknown tags (verified); the warning is ours to raise |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | `>=8` (installed 9.x) | Test runner | All phase tests |
| `pytest-asyncio` | present | — | Not needed here; the engine is pure sync file I/O. Do **not** make it async. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `ruamel.yaml.compose()` node marks | `CommentedMap.lc` (`.lc.data`, `.lc.key(k)`, `.lc.value(k)`, `.lc.item(i)`) | `.lc` gives only a **start** `(line, col)` (0-indexed) and **no end** and **no byte index** — verified. You would have to convert `(line,col)->offset` yourself *and* still derive the end. `compose()` gives both ends as absolute indices in one pass. Use `.lc` only as a cross-check. |
| Re-implement HA loader with ruamel | Vendor / import HA's `annotatedyaml` package | `annotatedyaml` is PyYAML-based (`CSafeLoader`), destroys comments/quotes on dump — the whole reason we can't use it. But it is the **authoritative spec** for `!include*` semantics; mine it, don't run it. |
| `compose()` + separate `load()` (two parses) | Single `load()` + walk `CommentedMap` for `.lc` | Two parses is ~2x parse cost per file (negligible for HA configs, typically < 1 MB total) and buys exact spans. Worth it. |
| Pin `ruamel.yaml>=0.18` (current pyproject) | Tighten to `>=0.19.1,<0.20` | 0.19.0 (2025-01-02) reworked the optional C-extension packaging and shipped `YAML().max_depth`; 0.19.1 (late 2025) dropped the `ruamel.yaml.clibz` dependency. Round-trip API is stable across 0.18->0.19 but emitter/indent details are exactly the kind of thing that drifts between minors — pin it for D-10 determinism. `[CITED: libraries.io/pypi/ruamel.yaml]` |

**Installation:** No new dependency. `ruamel.yaml` is already declared (`pyproject.toml` line 9). Recommended change: `"ruamel.yaml>=0.19.1,<0.20"`.

**Version verification:**
```
$ uv pip show ruamel.yaml
Name: ruamel-yaml
Version: 0.19.1
```
`[VERIFIED: local probe]` — 0.19.1 installed in `.venv`, resolved by `uv.lock`. 0.19.1 is the current release line (0.19.0 released 2025-01-02). `[CITED: libraries.io/pypi/ruamel.yaml]`

---

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `ruamel.yaml` | PyPI | ~15 yrs (fork of PyYAML lineage; 0.1 on PyPI 2016, project older) | ~50M+/month | sourceforge.net/projects/ruamel-yaml (canonical); mirror github.com/pycontribs/ruamel-yaml | OK | Approved — already a locked project dependency since Phase 1 |

**Packages removed due to [SLOP] verdict:** none — this phase introduces **no new packages**.
**Packages flagged as suspicious [SUS]:** none.

> Note: the `gsd-tools` legitimacy seam was not reachable in this worktree session (no `gsd-core/bin`). `ruamel.yaml` is the canonical, decade-plus-old Python round-trip YAML library, already vetted and locked in `pyproject.toml` + `uv.lock` during Phase 1; no `checkpoint:human-verify` is needed for it. `[CITED: pypi.org/project/ruamel.yaml, sourceforge.net/p/ruamel-yaml/code]`

---

## HA `!include*` / `packages:` Semantics — Pinned from Source

Authoritative source: **`annotatedyaml`** (Home Assistant's extracted YAML loader; `homeassistant/util/yaml/loader.py` now just wraps it). Fetched from `github.com/home-assistant-libs/annotatedyaml/blob/main/src/annotatedyaml/loader.py`, this session.

### Tag list registered by HA (exact strings) `[CITED: annotatedyaml/loader.py]`

Verbatim from the bottom of `loader.py`:

```python
add_constructor("!include", _include_yaml)
add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _handle_mapping_tag)
add_constructor(yaml.resolver.BaseResolver.DEFAULT_SCALAR_TAG, _handle_scalar_tag)
add_constructor(yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG, _construct_seq)
add_constructor("!env_var", _env_var_yaml)
add_constructor("!secret", secret_yaml)
add_constructor("!include_dir_list", _include_dir_list_yaml)
add_constructor("!include_dir_merge_list", _include_dir_merge_list_yaml)
add_constructor("!include_dir_named", _include_dir_named_yaml)
add_constructor("!include_dir_merge_named", _include_dir_merge_named_yaml)
add_constructor("!input", Input.from_node)
```

This is exactly the D-08 list (8 tags: `!secret !include !include_dir_list !include_dir_merge_list !include_dir_named !include_dir_merge_named !env_var !input`). No others. HA's loader is a **PyYAML** `SafeLoader`/`CSafeLoader` subclass (`FastSafeLoader` / `PythonSafeLoader`), **not** ruamel.

### What each tag carries `[CITED: annotatedyaml/loader.py]`

| Tag | Node form | Argument (`node.value`) | HA behavior (for reference; Phase 2 keeps it **opaque** per D-06/D-09) |
|-----|-----------|--------------------------|----------------------|
| `!include` | scalar | relative path to one `.yaml`/`.yml` file | loads that file; empty file -> `{}` |
| `!include_dir_list` | scalar | relative dir | list of each file's content, `secrets.yaml` + `None` (empty) skipped |
| `!include_dir_merge_list` | scalar | relative dir | flat list; only files whose top level `isinstance(list)` are extended |
| `!include_dir_named` | scalar | relative dir | dict `{file_stem: content}`; empty file -> `{}` entry; `secrets.yaml` skipped |
| `!include_dir_merge_named` | scalar | relative dir | one merged dict via `mapping.update(loaded)`; only `isinstance(dict)` files |
| `!secret` | scalar | secret key name | resolves from nearest `secrets.yaml` walking up to config dir. **Phase 2: opaque, `secrets.yaml` not read (D-09).** |
| `!env_var` | scalar | `VARNAME [default words...]` — `node.value.split()`, first token is the var, the rest joined is the default | `os.getenv`. **Phase 2: opaque.** |
| `!input` | scalar **or mapping** | blueprint input name (or a mapping in some blueprint contexts) | `Input.from_node`; `Input` is a dataclass with `.name`. Round-trips opaque in ruamel as a `TaggedScalar` (scalar form) or tagged `CommentedMap` (verified probe with `!input` on a mapping). |

### `_find_files` — directory scan (the D-05 discrepancy) `[CITED: annotatedyaml/loader.py]`

Verbatim:

```python
def _is_file_valid(name: str) -> bool:
    """Decide if a file is valid."""
    return not name.startswith(".")


def _find_files(directory: str, pattern: str) -> Iterator[str]:
    """Recursively load files in a directory."""
    for root, dirs, files in os.walk(directory, topdown=True):
        dirs[:] = [d for d in dirs if _is_file_valid(d)]
        for basename in sorted(files):
            if _is_file_valid(basename) and fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename
```

And every `_include_dir_*` calls it as `_find_files(loc, "*.yaml")`.

Facts, verbatim-grounded:

1. **RECURSIVE.** `os.walk` descends into every subdirectory. The docstring literally says *"Recursively load files in a directory."* **This contradicts D-05's "non-recursive".** `[CITED: annotatedyaml/loader.py — HIGH confidence]`
2. **Per-directory file order is `sorted()`** (lexicographic on `basename`). But `os.walk`'s *directory* traversal order is **not** sorted (the `dirs[:] = [...]` line filters, does not sort) — so across nested dirs the order is filesystem-dependent. For deterministic reproduction, sort both.
3. **`.yaml` only.** Pattern is hard-coded `"*.yaml"`; `.yml` files are **ignored** by the `_dir_` variants. (Plain `!include foo.yml` still works — it is a bare `os.path.join`.) `[CITED: annotatedyaml/loader.py]`
4. **Dotfiles and dot-directories are skipped** (`_is_file_valid` -> `not name.startswith(".")`).
5. **`secrets.yaml` is skipped** inside every `_include_dir_*` (`if os.path.basename(fname) == SECRET_YAML: continue`). `SECRET_YAML` is the string `"secrets.yaml"` (`annotatedyaml.const`; not opened byte-for-byte this session — `[CITED: HA well-known filename, MEDIUM]`).

### Path resolution `[CITED: annotatedyaml/loader.py]`

Every include function resolves the target as:

```python
fname = os.path.join(os.path.dirname(loader.get_name), node.value)
```

`loader.get_name` is the path of the **file currently being parsed**. So includes are resolved **relative to the directory of the including file**, not relative to the config-dir root. Nested includes compound (a file in `packages/foo/bar.yaml` that does `!include baz.yaml` looks for `packages/foo/baz.yaml`).

### `packages:` semantics `[CITED: github.com/home-assistant/core/blob/dev/homeassistant/config.py — MEDIUM]`

- The key lives at **`homeassistant: -> packages:`** in `configuration.yaml` (`core_config.get(CONF_PACKAGES, {})` where `core_config = config.get(HOMEASSISTANT_DOMAIN, {})`).
- Value is a mapping `{package_name: package_dict}`, typically produced by `packages: !include_dir_named packages/` (so `_include_dir_named` semantics above apply to *finding* the package files).
- Merge algorithm (`merge_packages_config` / `_recursive_merge`):
  - **Lists**: concatenated, falsy removed — `conf[key] = cv.remove_falsy(cv.ensure_list(conf.get(key)) + cv.ensure_list(pack_conf))`.
  - **Dicts**: recursively merged; a duplicate scalar key across a package and the root is an **error** (`_log_pkg_error(... "has duplicate key ...")`).
  - **Scalars**: conflict if the key already exists at root.
- **Phase 2 does NOT perform this merge.** Per D-04 the job is only to (a) discover the package files via the `!include_dir_named` (or explicit) mechanism, (b) load each as its own editable file node, (c) add graph edges `configuration.yaml --packages--> packages/<name>.yaml`. The merge is HA's runtime concern; re-implementing it is out of scope (and RULE-03/RULE-01 in later phases operate per-file).

### Empty / type-mismatch handling `[CITED: annotatedyaml/loader.py]`

| Situation | HA result |
|-----------|-----------|
| `!include` of an empty file | `NodeDictClass()` (empty dict) |
| `!include_dir_named` empty file | empty-dict entry under the stem |
| `!include_dir_merge_named` file whose top level isn't a dict | **silently skipped** (`if isinstance(loaded_yaml, dict)`) |
| `!include_dir_list` empty file | skipped (`is not None`) |
| `!include_dir_merge_list` file whose top level isn't a list | **silently skipped** (`if isinstance(loaded_yaml, list)`) |
| `!include` / `!include_dir_*` with no argument | `YAMLException("... needs an argument.")` |

For Phase 2 these only matter for the **graph** (a matched-but-skipped file: decide whether it is still a graph node — recommend yes, it is still an editable file the pulled tree contains) and for not crashing on odd fixtures.

---

## Architecture Patterns

### System Architecture Diagram

```
                       configuration.yaml (root, path known)
                                  │
                                  ▼
                   ┌──────────────────────────────┐
   raw bytes  ───▶ │  loader.load_file(path)      │
   (utf-8,         │  ├─ open(newline='') → text  │   text kept verbatim
    newline='')    │  ├─ YAML().load(text)        │ ─▶ CommentedMap tree  (navigate / read)
                   │  └─ YAML().compose(text)     │ ─▶ Node tree w/ start_mark.index
                   └──────────────┬───────────────┘         end_mark.index
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │  spans.build_index(node)     │  walk Node tree, assign logical path,
                   │   path → Span(start,end,     │  flag alias-shared / merge-key nodes
                   │        file, kind, unspliceable?)
                   └──────────────┬───────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────────┐        for each !include* / packages:
                   │  includes.resolve(root_dir)  │───────▶ TaggedScalar arg → resolve path(s)
                   │   DFS, "loading" stack for   │         relative to including file's dir
                   │   cycle detection            │◀──────  recurse: load_file + build_index
                   └──────────────┬───────────────┘
                                  │  edges: parent --tag--> child
                                  ▼
        ┌───────────────────────────────────────────────────┐
        │  ConfigTree                                        │
        │   files: dict[Path, FileNode(text, data, spans)]   │
        │   graph: IncludeGraph(edges, roots, cycles=[])     │
        └───────────────────┬───────────────────────────────┘
                            │  caller: tree.set(path_in_file, new_value)
                            ▼
        ┌───────────────────────────────────────────────────┐
        │  Mutation record: (file, span, rendered_text)     │
        │   - span.unspliceable → raise ConfigTreeError (D-03)│
        │   - render new scalar via ruamel, quote-style aware │
        └───────────────────┬───────────────────────────────┘
                            │  writer.flush()
                            ▼
        for file in dirty:  new_text = splice(file.text, edits sorted desc by start)
                            atomic_write(path, new_text)   # temp + os.replace
        untouched files:    never opened for writing        # YAML-04 / YAML-02
```

### Recommended Project Structure

```
src/haco/configtree/
├── __init__.py        # public: load_config_tree(root_dir) -> ConfigTree; re-exports
├── loader.py          # YAML() factory (indent pinned, preserve_quotes), load_file()
├── spans.py           # Span dataclass, build_index(node) walking compose() tree
├── includes.py        # resolve(): HA !include*/packages walk, dir scan, path join
├── graph.py           # IncludeGraph dataclass, cycle detection
├── tree.py            # ConfigTree, FileNode, navigation + set()/get() mutation API
├── writer.py          # surgical splice + atomic dirty-only write
└── errors.py          # (or extend src/haco/errors.py) ConfigTreeError family

tests/
├── fixtures/ha_config/          # the representative tree (see Fixture Design)
├── test_configtree_loader.py
├── test_configtree_spans.py
├── test_configtree_includes.py
├── test_configtree_graph.py
├── test_configtree_writer.py
└── test_configtree_idempotency.py
```

Match Phase 1 conventions: `src/` layout, `mypy --strict`, ruff line-length 120, one atomic commit per task, a `SUMMARY.md` per plan, frozen dataclasses for results, no CLI surface yet (or one hidden `haco _dump-tree` debug command at most).

### Pattern 1: Two-parse load (span index + editable tree)

**What:** Parse each file's text twice — `compose()` for offsets, `load()` for the round-trip object model.
**When to use:** Every file loaded into the ConfigTree.
**Example** (verified against `ruamel.yaml 0.19.1` this session):

```python
# Source: local probe, ruamel.yaml 0.19.1
import io
from ruamel.yaml import YAML

def make_yaml() -> YAML:
    y = YAML()                      # typ='rt' by default
    y.preserve_quotes = True
    y.indent(mapping=2, sequence=4, offset=2)   # HA 2-space block style
    y.width = 1_000_000             # never auto-wrap when rendering a replacement scalar
    return y

text = path.read_text(encoding="utf-8", newline="")   # keep CRLF + BOM verbatim
y = make_yaml()
data = y.load(text)                 # CommentedMap / CommentedSeq / TaggedScalar
node = y.compose(text)              # ScalarNode/MappingNode/SequenceNode w/ marks
# node.start_mark.index / node.end_mark.index are absolute offsets into `text`
```

### Pattern 2: `compose()`-based span index

**What:** Walk the `compose()` node tree, assign each value node a logical path, record `(start_mark.index, end_mark.index)`.
**Verified offset behavior** (probe, ruamel 0.19.1):

| Value kind | Example | Span content (`text[start:end]`) |
|------------|---------|----------------------------------|
| plain scalar | `name: Home` | `Home` — trailing spaces/comments **excluded** |
| int/typed scalar w/ trailing comment | `num: 42   # c` | `42` |
| double-quoted | `x: "Quoted Name"` | `"Quoted Name"` — quotes **included** |
| single-quoted | `v: 'single'` | `'single'` |
| block literal | `state: \|\n  a\n  b\n` | `\|\n  line one\n  line two\n` — starts at `\|`, **ends after the block's final newline** |
| folded | `f: >\n  wrapped\n` | `>\n  wrapped\n text\n` |
| flow seq | `flow: [a, b, c]` | `[a, b, c]` — brackets included |
| flow map | `m: {x: 1, y: 2}` | `{x: 1, y: 2}` |
| tagged scalar | `automation: !include automations.yaml` | `!include automations.yaml` (the `TaggedScalar`'s node span) |
| tagged mapping | `k: !input\n  name: foo` | `!input\n  name: foo\n  default: bar` |

**Path representation:** a tuple mixing dict keys and list indices, e.g. `("homeassistant", "name")`, `("sensor", 0, "sensors", "foo", "value_template")`. Build it during the `compose()` walk. **Canonicalize keys**: `compose()` gives `key_node.value` as the raw string; the `load()` tree may key on a typed value (int/bool/date). Recommend keying paths on the **string form of the scalar** and having `tree.get()/set()` resolve the same way, or run ruamel's scalar resolver on both sides. Flag as a design decision (see Open Questions).

### Pattern 3: Alias / merge-key guarding (D-03, D-07)

**What:** In `compose()`, a `*alias` reference resolves to the **same node object** as its `&anchor` — verified: the aliased subtree's marks point at the *anchor's* original location, and my walker recursed into it and mis-attributed `("script","other","alias")` to `idx 25..34` (the anchor's span). In `load()`, `d['script']['other'] is d['script']['wakeup']` is **True** (shared object).
**Rule:** during the span walk, track `id(node)`; the second+ time a node object is seen, mark that path `unspliceable=True` with reason `"value is a YAML alias (*x); edit the anchor definition instead"`. `tree.set()` on such a path raises `ConfigTreeError` (D-03). Same treatment for `<<` merge-key-derived values.

### Pattern 4: Surgical splice writer

**What:** Collect `(file, span, new_text)` edits; per file, apply edits **sorted by `start` descending** so earlier offsets stay valid; write via temp+`os.replace`.
**Verified** (probe): `text[:s] + "My House" + text[e:]` changed only the `name:` value; `spliced[:s] == text[:s]` and the tail matched exactly. CRLF+BOM source spliced correctly (offsets are indices into whatever string you handed `compose()`).

```python
# Source: local probe pattern, ruamel.yaml 0.19.1
def splice(text: str, edits: list[tuple[int, int, str]]) -> str:
    for start, end, new in sorted(edits, key=lambda e: e[0], reverse=True):
        text = text[:start] + new + text[end:]
    return text
```

### Pattern 5: Rendering the replacement scalar

**What:** Produce the new value's text with a style that matches the surroundings (D-02).
**Verified:** `ruamel.yaml.scalarstring.DoubleQuotedScalarString('a "quote" inside')` dumped as `x: "a \"quote\" inside"`. To render just the value, dump `{"_": value}` and slice after `"_: "`, or keep a tiny renderer. Preserve the original node's style where possible: read it from the `load()` tree (`type(old_value)` is `DoubleQuotedScalarString` / `SingleQuotedScalarString` / `LiteralScalarString` / `FoldedScalarString` / `PlainScalarString`) and re-wrap the new value in the same class. Block scalars: the replacement must re-emit the `|`/`>` indicator, correct indentation, and a trailing `\n` (the span ends after it).

### Anti-Patterns to Avoid

- **Dumping a whole touched file with `yaml.dump()`.** Forbidden by D-01/D-03. Even with `indent(2,4,2)` the probe showed the *default* config re-flows block sequences (`  - x` → `- x`); relying on emitter fidelity is exactly the trap PITFALLS.md calls out.
- **Using `.lc` line/col and converting to an offset by counting characters, then guessing the end.** Works for the start; the *end* is the hard part and `compose()` already has it.
- **Treating `!include*` as something to inline.** D-06: opaque `TaggedScalar`, edit the child file in the child file.
- **Making the engine async.** No I/O concurrency benefit; it complicates `mypy --strict` and testing. Phase 1's async is for SSH only.
- **Reading the file with default `open()` (newline translation on) or `utf-8-sig`.** That silently drops `\r` / BOM and breaks "every untouched byte preserved". Use `open(p, encoding="utf-8", newline="")`.
- **Sorting `os.walk` output only by basename.** Matches HA's per-dir behavior but not cross-dir; sort the full recursive list for determinism (HA itself is non-deterministic across nested dirs — we can be stricter).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML tokenizing / finding where a value ends | A regex or hand-rolled scanner over the YAML text | `ruamel.yaml.YAML().compose(text)` node `start_mark.index` / `end_mark.index` | Handles block scalars, flow collections, quotes, comments, anchors, tags correctly — verified across all of them |
| Line/col → byte offset | Manual line-length table | `compose()` gives `.index` directly (absolute) | `.lc` needs the table; `compose()` doesn't |
| Preserving comments / quote style / key order | Anything | `ruamel.yaml` round-trip mode | The reason Python was chosen |
| Rendering a quoted/block replacement scalar | String concatenation with manual escaping | `ruamel.yaml.scalarstring.*ScalarString` + a 1-line dump | Correct escaping of `"`, `\`, newlines, leading `!`/`&`/`*` |
| HA `!include_dir_*` scan rules | Guessing sort/recursion/extension | The verbatim `_find_files` above | HA's own source is the spec |
| Atomic file replace | `open(w)` truncate-in-place | `tempfile` in same dir + `os.replace` | Phase 1 already uses temp+`os.replace` for profile writes; reuse the pattern |
| Cycle detection in the include graph | Recursion with no guard (HA itself has none → `RecursionError`) | DFS with a "currently-loading" set; back-edge → `ConfigTreeError` | HA crashes on include cycles; we should fail cleanly |

**Key insight:** the only genuinely novel code here is (1) the parallel path-walk that ties `compose()` spans to `load()` navigation, and (2) the HA include-semantics re-implementation. Everything else is ruamel + stdlib.

---

## Runtime State Inventory

Not a rename/refactor/migration phase — greenfield module addition. Section omitted per template guidance.

---

## Common Pitfalls

### Pitfall 1: D-05 says "non-recursive"; HA is recursive

**What goes wrong:** The include graph and any later dir-based rule (RULE-04 "collapse empty includes") will disagree with HA about which files are part of a `!include_dir_*` directory if we implement a flat `os.listdir`.
**Why it happens:** CONTEXT.md D-05 asserts "non-recursive — matches HA semantics" and asked for verification. HA's `_find_files` uses `os.walk` and its docstring says *"Recursively load files in a directory."* `[CITED: annotatedyaml/loader.py]`
**How to avoid:** Implement the scan as **recursive** (`os.walk`, filter dotfiles/dot-dirs, `*.yaml` only, skip `secrets.yaml`), and surface this discrepancy to the user in discuss/plan so D-05 can be corrected. If the user truly wants non-recursive, that is a deliberate divergence from HA and should be logged as such.
**Warning signs:** a fixture with `automations/subdir/foo.yaml` — HA loads it, a flat scan misses it.

### Pitfall 2: ruamel re-flows block sequences unless indent is pinned

**What goes wrong:** `load()` then `dump()` turns
```
light:
  - platform: demo
```
into
```
light:
- platform: demo
```
(verified with default `YAML()`).
**Why it happens:** ruamel's default `sequence`/`offset` differ from HA's 2-space-with-indented-dash style.
**How to avoid:** `y.indent(mapping=2, sequence=4, offset=2)` — the probe confirms this is byte-identical for HA-style input. **But note:** with D-01 you never dump a whole file, so this only bites the *diagnostic* round-trip check and the rendering of a *new* multi-line value. Still pin it.
**Warning signs:** the defensive `load->dump==original` diagnostic fails on files with block sequences.

### Pitfall 3: `end_mark` semantics differ by scalar kind

**What goes wrong:** Splicing a block scalar with a replacement that lacks a trailing newline corrupts the following line; splicing a plain scalar and *adding* a trailing space shifts a trailing comment.
**Why it happens:** For plain/quoted scalars `end_mark.index` sits right after the last value char (no trailing WS/comment). For block scalars it sits at column 0 of the **next** line (the block's final `\n` is inside the span).
**How to avoid:** Branch on the original node's style. For block scalars, the rendered replacement must include indicator + indented body + one trailing `\n`. Add a test per kind (see Validation Architecture).
**Warning signs:** byte-diff test shows changes bleeding past the intended span.

### Pitfall 4: Aliases are shared objects in both `compose()` and `load()`

**What goes wrong:** `tree.set(("script","other"), X)` silently also changes `script.wakeup` (they are the *same* `CommentedMap`), or splices at the anchor's location.
**Why it happens:** verified — `d['script']['other'] is d['script']['wakeup']` is `True`; `compose()` returns the anchor node for the alias.
**How to avoid:** mark alias-target paths `unspliceable` (Pattern 3); `set()` raises `ConfigTreeError` naming the anchor. D-07: never resolve across includes anyway.
**Warning signs:** a mutation test on an aliased key changes two places.

### Pitfall 5: Non-ASCII and line endings

**What goes wrong:** "every untouched byte preserved" fails because `open()` translated `\r\n`→`\n` or `utf-8-sig` ate the BOM, or offsets computed on a normalized string don't match the on-disk bytes.
**Why it happens:** default text-mode `open()` does universal-newline translation.
**How to avoid:** `read_text(encoding="utf-8", newline="")`; splice in that same string; `write_text(..., encoding="utf-8", newline="")`. Offsets from `compose()` are code-point indices into the string you pass it — consistent as long as you pass the untranslated text. Verified with a CRLF+BOM+umlaut sample.
**Warning signs:** diff tools show whole-file "line ending changed" on a one-value edit.

### Pitfall 6: Unknown-tag warning is ours to emit

**What goes wrong:** D-08 wants a warning for unknown `!` tags; a reviewer expects ruamel to produce it.
**Why it happens:** verified — ruamel 0.19.1 round-trips `!lambda`, `!my_custom_tag [1,2,3]`, `!weird {a:1}` **byte-identical with zero warnings**.
**How to avoid:** after `load()`, walk for `TaggedScalar` / tagged `CommentedMap`/`CommentedSeq` whose `.tag` (as a `str`) is not in the known set `{!secret,!include,!include_dir_list,!include_dir_merge_list,!include_dir_named,!include_dir_merge_named,!env_var,!input}` and `warnings.warn(...)` once per distinct tag. Round-tripping still works; the warning is advisory.
**Warning signs:** none at runtime — this is a spec-compliance item.

### Pitfall 7: Duplicate keys

**What goes wrong:** HA (PyYAML) rejects duplicate mapping keys; ruamel round-trip by default raises `DuplicateKeyError` (or warns, version-dependent).
**How to avoid:** let it raise and wrap as `ConfigTreeError` with file + line; do not silently allow. Add a fixture with a *valid* config only — put a dup-key file in a "negative" fixture subset.

### Pitfall 8: `mypy --strict` at the ruamel boundary

**What goes wrong:** `yaml.load()` / `yaml.compose()` are typed to return `Any`; `--strict` (`warn_return_any`, `disallow_any_*`) complains when those flow into typed code.
**Why it happens:** ruamel ships `py.typed` (verified) but its public surface is loosely typed; `CommentedMap` is `dict`-ish.
**How to avoid:** confine ruamel calls to `loader.py` / `spans.py`; give every wrapper function an explicit return type; `cast()` at the boundary; a handful of targeted `# type: ignore[no-any-return]` are acceptable and were anticipated by Phase 1's pattern of Protocol-typed seams. `Node`, `ScalarNode`, `MappingNode`, `SequenceNode` import from `ruamel.yaml.nodes`; `CommentedMap`, `CommentedSeq`, `TaggedScalar` from `ruamel.yaml.comments`; scalar-string classes from `ruamel.yaml.scalarstring`.

### Pitfall 9: `!include` path traversal

**What goes wrong:** `!include ../../../../etc/passwd` or a symlink target outside the pulled tree gets loaded as an editable file node.
**Why it happens:** HA does a bare `os.path.join`; no containment check.
**How to avoid:** resolve each include target, `Path.resolve()`, and assert it stays within the pulled config root; if not, warn and either skip or record it as a read-only external node. Low severity for a local tool on the user's own config, but keeps the file map sane. (See Security Domain.)

---

## Code Examples

### Load one file → editable tree + span index

```python
# Source: local probe, ruamel.yaml 0.19.1 — verified round-trip + marks
import io
from dataclasses import dataclass
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.nodes import Node, ScalarNode, MappingNode, SequenceNode


@dataclass(frozen=True)
class Span:
    file: Path
    start: int          # char offset into file text
    end: int
    kind: str           # "plain" | "single" | "double" | "literal" | "folded" | "flow" | "tagged" | "collection"
    unspliceable: str | None = None   # reason, if the value is an alias / merge-derived


def _make_yaml() -> YAML:
    y = YAML()
    y.preserve_quotes = True
    y.indent(mapping=2, sequence=4, offset=2)
    y.width = 1_000_000
    return y


def load_file(path: Path):
    text = path.read_text(encoding="utf-8", newline="")
    y = _make_yaml()
    data = y.load(text)
    root = y.compose(text)
    spans: dict[tuple, Span] = {}
    seen: set[int] = set()

    def walk(node: Node, p: tuple) -> None:
        alias = id(node) in seen
        seen.add(id(node))
        if isinstance(node, MappingNode):
            if not alias:
                for k, v in node.value:
                    walk(v, p + (k.value,))
            else:
                spans[p] = Span(path, node.start_mark.index, node.end_mark.index,
                                "collection", "value is a YAML alias; edit the anchor")
        elif isinstance(node, SequenceNode):
            if not alias:
                for i, v in enumerate(node.value):
                    walk(v, p + (i,))
            else:
                spans[p] = Span(path, node.start_mark.index, node.end_mark.index,
                                "collection", "value is a YAML alias; edit the anchor")
        else:  # ScalarNode (incl. tagged)
            kind = "tagged" if str(node.tag).startswith("!") else "plain"
            spans[p] = Span(path, node.start_mark.index, node.end_mark.index, kind,
                            "value is a YAML alias; edit the anchor" if alias else None)

    walk(root, ())
    return text, data, spans
```

### HA-faithful directory scan for `!include_dir_*`

```python
# Source: re-implementation of annotatedyaml._find_files  [CITED: annotatedyaml/loader.py]
import fnmatch, os
from pathlib import Path

SECRET_YAML = "secrets.yaml"

def find_dir_yaml(directory: Path) -> list[Path]:
    out: list[Path] = []
    for root, dirs, files in os.walk(directory, topdown=True):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))   # HA filters; we also sort
        for name in sorted(files):
            if name.startswith(".") or not fnmatch.fnmatch(name, "*.yaml"):
                continue
            if name == SECRET_YAML:
                continue
            out.append(Path(root) / name)
    return out
```

### Atomic dirty-only write

```python
# Source: mirrors haco.profile atomic write (Phase 1 pattern)
import os, tempfile
from pathlib import Path

def atomic_write(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `PyYAML` + custom `SafeLoader` with tag constructors (v1 of this project, `bin/ha_ai_context_gen.py`) | `ruamel.yaml` round-trip + `compose()` span index | This rewrite | Comments/quotes/anchors survive; edits are surgical, not full-dump |
| HA loader lived in `homeassistant/util/yaml/loader.py` | Extracted to the standalone **`annotatedyaml`** package; `homeassistant/util/yaml/loader.py` now re-exports it | HA 2025.x | Cite `annotatedyaml` as the spec source, not the old path |
| `ruamel.yaml.clib` / `clibz` hard/soft dependency | 0.19.1 drops both; pure-Python fallback always available | 0.19.1 (late 2025) | No C-extension build headaches on the user's box; pin `>=0.19.1` |
| `.lc` line/col as the only position data people knew about | `compose()` node `start_mark.index` / `end_mark.index` give absolute start **and end** offsets | Long available, under-documented | The enabling primitive for D-01 |

**Deprecated/outdated:**
- Using `yaml.load`/`yaml.safe_load` (PyYAML) anywhere in this engine — disqualified (STACK.md).
- Relying on `ruamel.yaml`'s `RoundTripLoader`/`RoundTripDumper` *class* names — use the `YAML()` instance API (`typ='rt'` default).
- The idea (implied by D-02's phrasing) that `.lc` alone gives spans — it gives starts only.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `SECRET_YAML == "secrets.yaml"` exactly (constant in `annotatedyaml.const`, not opened byte-for-byte this session) | HA semantics | Low — it is HA's documented, decade-stable filename; a wrong guess would only mis-skip one file in dir scans |
| A2 | `packages:` lives under `homeassistant:` and is typically `!include_dir_named packages/`; merge is list-concat / recursive-dict / dup-key-error | `packages:` semantics | Medium — mischaracterizing the merge doesn't break Phase 2 (we don't merge) but could mislead the graph-edge design; the *discovery* mechanism (via `!include_dir_named`) is the only part Phase 2 uses and is well-grounded |
| A3 | `!input` appears in HA config as a `TaggedScalar` or tagged mapping and round-trips opaque | HA semantics / probe | Low — probe confirmed tagged-mapping round-trip; `!input` is blueprint-only and rare in top-level config |
| A4 | ruamel `compose()` `end_mark.index` is stable across 0.19.x patch releases | span index | Medium — pin `<0.20`; a determinism test in the idempotency harness will catch drift |
| A5 | HA's cross-directory `os.walk` order being filesystem-dependent means we are *free* to impose a total sort without diverging from any *guaranteed* HA behavior | dir scan | Low — HA guarantees only per-directory `sorted()`; imposing more order is stricter, not wrong |
| A6 | Two parses per file (`load` + `compose`) is acceptable performance for real HA configs | architecture | Low — typical HA config trees are a few hundred KB total; even 10x is sub-second |

**No `gsd-tools classify-confidence` / `research-plan` seam was available in this worktree**, so confidence tags are assigned directly: HIGH where a live probe or verbatim source backs the claim, MEDIUM for WebFetch-summarized HA source, LOW/ASSUMED as tabled above.

---

## Open Questions (RESOLVED)

1. **D-05 "non-recursive" vs HA's recursive `os.walk`.**
   - What we know: HA's `_find_files` is recursive (verbatim source + docstring).
   - **RESOLVED (2026-08-30):** D-05 amended in CONTEXT.md to **recursive**, `.yaml`-only, per-dir `sorted()`, dotfiles + `secrets.yaml` skipped — matching `annotatedyaml._find_files`. Plan 02-02 Task 1 implements it.

2. **Path canonicalization for the span-index key vs the `load()` navigation key.**
   - What we know: `compose()` keys are raw strings; `load()` keys may be typed (int/bool/date/`null`).
   - **RESOLVED:** Executor discretion per CONTEXT.md "Claude's Discretion"; plans key paths on the scalar's resolved string form and 02-01 fixtures include a numeric mapping key so `tree.get/set` and the span walk are cross-checked.

3. **Does Phase 2 need a public mutation API at all?**
   - **RESOLVED:** Yes — a minimal `tree.set(path, value)` / `tree.get(path)` ships in 02-03 Task 1 so the apply-then-revert idempotency harness (D-10.3) is writable without a fake analyzer.

4. **`!include` targets outside the pulled config root** (symlinks, `../`).
   - **RESOLVED:** 02-02 Task 1 builds `Path.resolve()` + a containment check (`ensure_contained` / equivalent) into the include resolver's tracer — an out-of-root target raises rather than being loaded as an editable node (ASVS V12, RESEARCH Pitfall 9). Not deferred, not a bolt-on.

5. **Multi-document files (`---`).**
   - **RESOLVED:** 02-01 Task 2 raises a clear `YamlError` / `MultiDocumentError` when a second `---` document appears; single-document is assumed for all HA config files.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `ruamel.yaml` | entire engine | ✓ | 0.19.1 (in `.venv`, locked) | none needed |
| Python | engine | ✓ | 3.12.13 (uv-managed, `.python-version`) | none |
| `pytest` | tests | ✓ | 9.x | none |
| Live Home Assistant / SSH | — | n/a | — | Phase 2 runs entirely against fixture trees (CONTEXT `<domain>`) |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none.

---

## Validation Architecture

`workflow.nyquist_validation` is `true` in `.planning/config.json` — this section applies.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `pytest` 9.x (+ `pytest-asyncio`, unused here) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests"]`, `asyncio_mode = "auto"`) |
| Quick run command | `uv run pytest -q tests/test_configtree_*.py` |
| Full suite command | `uv run ruff check . && uv run black --check . && uv run mypy && uv run pytest -q` |
| Phase gate | full suite green before `/gsd-verify-work` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| YAML-01 | every D-08 tag parses without error, on scalar and (where legal) collection form | unit | `uv run pytest -q tests/test_configtree_loader.py -k tags` | ❌ Wave 0 |
| YAML-01 | unknown `!tag` round-trips opaque + emits exactly one `warnings.warn` per distinct tag | unit | `... -k unknown_tag` | ❌ Wave 0 |
| YAML-02 | a loaded-but-unedited file is returned byte-identical (no write occurs) | unit | `uv run pytest -q tests/test_configtree_writer.py -k untouched_identical` | ❌ Wave 0 |
| YAML-02 | defensive: `load -> dump` with pinned indent is byte-identical on each fixture file (diagnostic) | unit | `... tests/test_configtree_loader.py -k roundtrip_diagnostic` | ❌ Wave 0 |
| YAML-03 | include graph has an edge from `configuration.yaml` to every reachable file; `!include_dir_*` expands to one edge per matched `.yaml`; `secrets.yaml` absent | unit | `uv run pytest -q tests/test_configtree_includes.py tests/test_configtree_graph.py` | ❌ Wave 0 |
| YAML-03 | include cycle → `ConfigTreeError` naming the cycle, not `RecursionError` | unit | `... -k cycle` | ❌ Wave 0 |
| YAML-03 | dir scan is recursive, `.yaml`-only, dotfiles/`secrets.yaml` skipped, per-dir sorted | unit | `... -k dir_scan` | ❌ Wave 0 |
| YAML-04 | edit one value in one file → exactly that file rewritten; sibling files' mtime + bytes unchanged | unit | `uv run pytest -q tests/test_configtree_writer.py -k dirty_only` | ❌ Wave 0 |
| YAML-04 | byte-diff of the rewritten file vs original touches **only** the changed node's span (per scalar kind: plain / single / double / literal / folded / flow) | unit (parametrized) | `... -k splice_span` | ❌ Wave 0 |
| YAML-04 | `set()` on an alias-derived / merge-derived / spanless path → `ConfigTreeError` (D-03), no file written | unit | `... -k ambiguous_span_fails_loud` | ❌ Wave 0 |
| YAML-05 / D-10.1 | `load -> serialize -> load -> serialize` on the whole fixture tree is a per-file fixed point | integration | `uv run pytest -q tests/test_configtree_idempotency.py -k fixed_point` | ❌ Wave 0 |
| YAML-05 / D-10.2 | empty change set → `writer.flush()` writes 0 files (assert via mtime snapshot) | integration | `... -k empty_changeset_zero_writes` | ❌ Wave 0 |
| YAML-05 / D-10.3 | apply a mutation, then set the node back to its original value → every file byte-identical to pre-mutation snapshot | integration | `... -k apply_then_revert` | ❌ Wave 0 |
| cross-cutting | CRLF + BOM + non-ASCII fixture file survives load+splice with only the target span changed | unit | `... tests/test_configtree_writer.py -k encoding` | ❌ Wave 0 |
| cross-cutting | ruamel version pin holds; `compose()` end_mark offsets match a golden table (drift canary for A4) | unit | `... tests/test_configtree_spans.py -k golden_offsets` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest -q tests/test_configtree_<module>.py` for the module the task touched, plus `uv run ruff check . && uv run black --check . && uv run mypy`.
- **Per wave / plan merge:** `uv run pytest -q` (full suite — Phase 1's 33 tests + the new ones).
- **Phase gate:** full quality gate green (`ruff && black --check && mypy && pytest -q`).

### Wave 0 Gaps

- [ ] `tests/fixtures/ha_config/` — the representative tree (see Fixture Design below). Shared prerequisite for every test file.
- [ ] `tests/conftest.py` — add a `ha_config_tree` fixture that copies `tests/fixtures/ha_config/` into `tmp_path` (so writer tests mutate a throwaway copy) and returns its root `Path`.
- [ ] `tests/test_configtree_loader.py`, `_spans.py`, `_includes.py`, `_graph.py`, `_writer.py`, `_idempotency.py` — all new.
- [ ] Golden-offset table fixture for the drift canary (A4).
- [ ] No framework install needed — `pytest` already present.

---

## Fixture Design

A single fixture tree at `tests/fixtures/ha_config/` exercising every requirement. Proposed layout:

```
tests/fixtures/ha_config/
├── configuration.yaml         # comments, both quote styles, an anchor+alias pair,
│                              #   homeassistant: with packages: !include_dir_named packages/,
│                              #   automation: !include automations.yaml,
│                              #   sensor: !include_dir_merge_list sensors/,
│                              #   scene: !include_dir_list scenes/,
│                              #   group: !include_dir_merge_named groups/,
│                              #   template: !include_dir_named templates/,
│                              #   a !secret ref, a !env_var with a default, an unknown !custom tag
├── automations.yaml           # a list; a block literal (value_template: |), a folded scalar,
│                              #   a flow seq, a numeric mapping key somewhere
├── sensors/
│   ├── a_power.yaml           # top-level list  (merge_list)
│   ├── b_energy.yaml
│   └── nested/
│       └── c_extra.yaml       # proves RECURSION (Pitfall 1)
├── scenes/
│   ├── 01_evening.yaml        # top-level list (dir_list)
│   └── 02_morning.yaml
├── groups/
│   ├── living.yaml            # top-level dict (merge_named)
│   └── secrets.yaml           # MUST be ignored by the dir scan (assert absent from graph)
├── templates/
│   └── weather.yaml           # dict, keyed by file stem (dir_named)
├── packages/
│   ├── climate.yaml           # a package: dict merged under homeassistant.packages
│   └── lighting.yaml
├── blueprints/
│   └── automation/example.yaml  # uses !input  (scalar and mapping form)
└── .hidden.yaml               # MUST be ignored (dotfile)
```

Plus a **negative** mini-tree `tests/fixtures/ha_config_bad/` for: an include cycle (`a.yaml: !include b.yaml`, `b.yaml: !include a.yaml`), a duplicate mapping key, an `!include` pointing outside the root, and a missing include target.

Do **not** create a real `secrets.yaml` with plausible secrets — an empty/comment-only `groups/secrets.yaml` is enough to prove the skip (D-09: it is never read anyway).

---

## Security Domain

`workflow.security_enforcement` is `true`, `security_asvs_level: 1`.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | no auth surface in this phase |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Validation, Sanitization & Encoding | yes | YAML is parsed with ruamel round-trip (safe by construction — no arbitrary object construction; unknown tags become inert `TaggedScalar`, not Python objects). Reject duplicate keys, multi-doc, and malformed input with a typed `ConfigTreeError` rather than passing through. |
| V6 Cryptography | no | `!secret` stays opaque; `secrets.yaml` not read (D-09). Never log a `!secret`'s *key name* at INFO (it hints at what secrets exist) — keep to DEBUG. |
| V12 Files & Resources | yes | `!include*` path resolution: `Path.resolve()` every target and assert containment within the pulled config root; refuse or quarantine `..`/symlink escapes (Pitfall 9). Atomic temp+rename writes stay within the target file's own directory. Never follow an include to an absolute path outside the tree. |
| V5.5 Deserialization | yes | ruamel round-trip does not deserialize to arbitrary types; do **not** switch to `typ='unsafe'` / `typ='safe'` with custom multi-constructors that instantiate objects. Keep everything as `Commented*` / `TaggedScalar`. |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| YAML "billion laughs" / deeply nested anchors → memory blow-up | Denial of Service | ruamel round-trip does not expand aliases into copies (they are shared refs — verified); optionally set `YAML().max_depth` (added in 0.19) as a guard on pathological nesting |
| Include cycle → `RecursionError` / hang | Denial of Service | DFS "currently-loading" stack → `ConfigTreeError` (HA itself has no guard) |
| `!include ../../../etc/anything` or symlinked include escaping the tree | Information Disclosure / Tampering | `Path.resolve()` + containment check; warn + read-only quarantine or hard error |
| Path traversal in `!include_dir_*` argument (`../..`) | Information Disclosure | same containment check on the resolved directory before `os.walk` |
| Splice math error rewrites bytes outside the intended span | Tampering (silent config corruption) | parametrized byte-diff tests per scalar kind (Validation Architecture); D-03 fail-loud on ambiguous spans; atomic write so a crash never leaves a half-file |
| `!secret` key names leaked into logs / session log | Information Disclosure | log secret *keys* only at DEBUG; the Phase 7 redactor is the real control, but don't create the leak here |
| Symlink in the config tree followed during `os.walk` | Tampering | `os.walk(..., followlinks=False)` (the default) — do not enable `followlinks` |

No `security_block_on: high` items are expected from this phase; the file-handling controls (V12) are the ones to make sure land in the plans.

---

## Project Constraints (from CLAUDE.md / .claude/CLAUDE.md)

- **GSD workflow enforcement:** no direct repo edits outside a GSD workflow. (This phase runs under `/gsd-execute-phase`.)
- **Full rewrite, no old code:** the v1 `bin/*.py` (PyYAML-based) is excluded from the gate and must not be imported or revived. The new engine lives under `src/haco/`.
- **Quality gate is mandatory and unchanged:** `uv run ruff check . && uv run black --check . && uv run black --check . && uv run mypy && uv run pytest -q`, with `mypy` in `strict = true` mode over `files = ["src", "tests"]`. ruff selects `E,F,I,UP,B`, line length 120.
- **Conventions:** src-layout package, one atomic commit per task, `SUMMARY.md` per plan, frozen dataclasses for result types, library holds all behavior (thin/absent CLI), `shlex.quote` any shell interpolation (n/a here — no shell), remote paths via `posixpath` (n/a — local `pathlib` here).
- **Security:** no secret material in exceptions or logs (established in `errors.py` docstring); extends to `!secret` key names.
- **Error hierarchy:** add `ConfigTreeError` (and any sub-errors) under the existing `HacoError` base in `src/haco/errors.py` — do not invent a new base.

---

## Recommendations per Requirement

### YAML-01 — parse HA custom tags without error
- Build `haco.configtree.loader` with a `YAML()` factory: `preserve_quotes=True`, `indent(mapping=2, sequence=4, offset=2)`, `width` huge.
- ruamel 0.19.1 already round-trips all 8 D-08 tags + unknown tags as `TaggedScalar` / tagged `Commented*` with **no constructor needed** (verified). Still: define `KNOWN_HA_TAGS: frozenset[str]` = the D-08 set; after `load()`, walk for tagged nodes and `warnings.warn(f"unknown YAML tag {tag!r} in {path}; round-tripped opaquely")` once per distinct unknown tag (D-08's "warn, don't fail").
- Optionally register no-op round-trip constructors/representers for the known tags for explicitness and to lock behavior against a future ruamel that changes unknown-tag handling — but treat this as belt-and-braces, not load-bearing.
- Tests: one parametrized test feeding each tag in scalar form; `!input` and (a contrived) tag on a mapping; a `!custom` unknown tag asserting round-trip + exactly one warning.

### YAML-02 — untouched file load→dump byte-identical
- **Reframe:** with D-01, untouched files are never emitted. The writer must guarantee it opens **only** dirty files. Test: load the whole tree, `flush()` with no edits, assert every file's bytes and mtime are unchanged.
- Keep a *diagnostic* test that `load()`→`dump()` each fixture file with the pinned indent equals the original (it does, per probe) — a canary for ruamel drift, not a product requirement.

### YAML-03 — include graph
- `haco.configtree.includes.resolve(root_dir)`: start at `configuration.yaml`, DFS. For each `TaggedScalar` whose tag is `!include` / `!include_dir_*`, resolve the path(s) with `os.path.join(os.path.dirname(current_file), arg)` (HA-faithful), recurse. For `homeassistant.packages` whose value is `!include_dir_named` (or an explicit mapping of includes), add the package files.
- Directory scan: the recursive, sorted, `.yaml`-only, dotfile/`secrets.yaml`-skipping `find_dir_yaml` above.
- `haco.configtree.graph.IncludeGraph`: frozen dataclass — `edges: tuple[IncludeEdge, ...]` where `IncludeEdge(parent: Path, tag: str, child: Path)`, `roots: tuple[Path, ...]`, `cycles: tuple[tuple[Path, ...], ...]`. Cycle detection via a `loading: set[Path]` on the DFS stack; on a back-edge, record the cycle and raise `ConfigTreeError` (or record and continue — planner's call; recommend raise, matching "fail loudly").
- `secrets.yaml` never added (D-05) — it is skipped by the dir scan and `!secret` is opaque so it is never followed.
- Tests: graph edges match the fixture tree exactly; `groups/secrets.yaml` and `.hidden.yaml` absent; `sensors/nested/c_extra.yaml` **present** (recursion); the bad-tree cycle raises.

### YAML-04 — only changed files rewritten
- `haco.configtree.tree.ConfigTree` holds `files: dict[Path, FileNode]`; `FileNode(path, text, data, spans, dirty: bool)`.
- `tree.set(path_tuple, value)`: look up `Span`; if `span is None` or `span.unspliceable`, raise `ConfigTreeError` (D-03) — no file touched. Else render replacement, record `(span, rendered)` on the FileNode, set `dirty=True`.
- `writer.flush(tree)`: for each `dirty` file only, `splice(text, edits desc)`, `atomic_write`. Return the list of written paths (for the session log later).
- Tests: `dirty_only` (edit one file, snapshot all others' mtime+bytes, flush, assert unchanged); `splice_span` parametrized over the six scalar kinds asserting `difflib`/byte-diff touches only `[start,end)`; `ambiguous_span_fails_loud`.

### YAML-05 — idempotency (D-10 no-op stability)
- `haco.configtree` gets a `serialize(tree) -> dict[Path, str]`: for each file, `splice` if it has edits else return `text` verbatim.
- Harness `tests/test_configtree_idempotency.py`:
  1. `fixed_point`: `t1 = load(root); s1 = serialize(t1)` → write `s1` to a temp tree → `t2 = load(temp); s2 = serialize(t2)` → assert `s1 == s2` per file.
  2. `empty_changeset_zero_writes`: `load`, `flush` with zero edits, assert 0 paths returned and 0 mtimes changed.
  3. `apply_then_revert`: snapshot bytes; `tree.set(P, new)`; `tree.set(P, original_value_text)`; `flush`; assert every file byte-identical to snapshot. (Requires `get()` to return the original rendered text, or the writer to detect a no-op edit and skip.)
- Add the `golden_offsets` drift canary here or in `_spans.py`.

---

## Proposed Plan Breakdown

Four plans, aligned with ROADMAP.md's existing 02-01..02-04 slots. **Wave 0** (fixtures + conftest) is a shared prerequisite — fold it into 02-01 Task 1 or make it a tiny standalone plan.

| Plan | Title | Delivers | Requirements | Key risks / notes |
|------|-------|----------|--------------|-------------------|
| **02-01** | Round-trip loader + span index (single file) | `configtree/loader.py` (YAML factory, `load_file`), `configtree/spans.py` (`Span`, `build_index` via `compose()`), `errors.py` += `ConfigTreeError`; the `tests/fixtures/ha_config/` tree + `ha_config_tree` conftest fixture; unknown-tag warning | YAML-01 | **The central technical risk lives here.** Nail the `compose()`↔`load()` parallel walk, alias detection (Pattern 3), per-kind `end_mark` semantics (Pitfall 3), CRLF/BOM (Pitfall 5), `mypy --strict` boundary (Pitfall 8). Include the golden-offset canary. |
| **02-02** | Include resolver + ConfigTree + include graph | `configtree/includes.py` (HA-faithful `!include*` / `packages:` walk, recursive dir scan), `configtree/graph.py` (`IncludeGraph`, cycle detection), `configtree/tree.py` (`ConfigTree`, `FileNode`, `get()`), assembly `load_config_tree(root)` | YAML-03 | Resolve **D-05 recursion discrepancy** first (Open Q1). Path containment check (Pitfall 9 / V12). `secrets.yaml` + dotfile skip. Negative fixture tree (cycle, missing target). |
| **02-03** | Mutation API + surgical splice writer | `configtree/tree.py` `set()`, `configtree/writer.py` (`splice`, `flush`, `atomic_write`), `serialize()` | YAML-02, YAML-04 | Replacement rendering per style (Pattern 5), block-scalar trailing `\n`, edits-sorted-desc, D-03 fail-loud, dirty-only + atomic. Byte-diff tests per scalar kind. |
| **02-04** | No-op stability harness | `tests/test_configtree_idempotency.py` — D-10's three properties against the full fixture tree; ruamel version pin bump in `pyproject.toml` | YAML-05 | `apply_then_revert` needs `get()` to yield the original value text (or writer no-op detection). Drift canary. |

Dependencies: 02-01 → 02-02 → 02-03 → 02-04 (strict chain; each builds on the prior module). 02-01 and the fixture tree gate everything.

---

## Sources

### Primary (HIGH confidence)
- **Local probe, `ruamel.yaml 0.19.1`** (installed in `.venv`, run this session): round-trip fidelity, `compose()` node `start_mark.index` / `end_mark.index` for every scalar kind + flow + block + tagged nodes, `.lc.data` / `.lc.value` / `.lc.key` / `.lc.item` shape (start-only, no end, no index), alias node sharing in both `compose()` and `load()`, `y.indent(mapping=2, sequence=4, offset=2)` byte-identical for HA-style config, CRLF+BOM+non-ASCII splice, unknown-tag silent round-trip (no warning), `py.typed` present.
- **`github.com/home-assistant-libs/annotatedyaml/blob/main/src/annotatedyaml/loader.py`** (fetched verbatim this session): `_find_files` (recursive `os.walk`, `sorted()` per dir, `*.yaml`, dotfile filter), every `_include_dir_*` body, `_include_yaml` path join, `secret_yaml`, `_env_var_yaml`, `Input.from_node`, the exact `add_constructor(...)` tag list, `FastSafeLoader`/`PythonSafeLoader` (PyYAML) classes.

### Secondary (MEDIUM confidence)
- **`github.com/home-assistant/core/blob/dev/homeassistant/config.py`** (WebFetch summary): `merge_packages_config` / `_recursive_merge` — `packages:` under `homeassistant:`, list-concat / recursive-dict / duplicate-key-error semantics.
- **`github.com/home-assistant/core/blob/dev/homeassistant/util/yaml/loader.py`** (WebFetch): confirms HA's loader now delegates to `annotatedyaml`.
- **ruyaml / yaml.dev ruamel docs** (`ruyaml.readthedocs.io/en/latest/detail.html`): `.lc` line/col API, `sequence >= offset + 2` indent guidance.
- **libraries.io / PyPI** (`libraries.io/pypi/ruamel.yaml`): 0.19.0 (2025-01-02) and 0.19.1 changelog — C-extension packaging changes, `YAML().max_depth` added.
- **Context7 `/pycontribs/ruamel-yaml`**: round-trip mode overview, `CommentedMap.ca` / `.lc` existence, `CommentMark`.

### Tertiary (LOW confidence / community)
- home-assistant.io/docs/configuration/splitting_configuration/ and /packages/ — user-facing description of `!include_dir_*` ("ordered alphanumerically", ".yaml only", "work recursively"); consistent with the source above.
- Home Assistant community threads on `!include_dir_merge_*` ordering — anecdotal, superseded by source.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — single dependency, already locked, version verified in-venv.
- ruamel span/round-trip mechanics: HIGH — every load-bearing claim was executed against `ruamel.yaml 0.19.1` this session.
- HA `!include*` semantics: HIGH — verbatim from HA's own loader source (the `annotatedyaml` extraction).
- `packages:` merge details: MEDIUM — WebFetch summary of `config.py`, not opened line-by-line; but Phase 2 does not implement the merge.
- Architecture / plan breakdown: MEDIUM-HIGH — follows Phase 1's established patterns; the `compose()`↔`load()` parallel walk is the one genuinely new mechanism and is prototyped above.
- Pitfalls: HIGH — all but Pitfall 8 were reproduced in-probe.

**Research date:** 2026-08-30
**Valid until:** ~2026-09-29 for the ruamel mechanics (pin `<0.20` and the golden-offset canary makes drift loud); HA include semantics are stable but re-check `annotatedyaml` if HA majorly bumps it.
