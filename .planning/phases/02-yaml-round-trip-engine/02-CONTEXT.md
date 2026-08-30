# Phase 2: YAML Round-Trip Engine - Context

**Gathered:** 2026-08-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver the config-tree engine: load a real Home Assistant config starting from
`configuration.yaml`, follow every `!include*` tag transitively, expose the whole
tree as editable in-memory nodes, let a caller mutate individual nodes, and write
back **only** the files that actually changed — with every untouched byte in a
changed file preserved exactly and every untouched file not rewritten at all.

Covers YAML-01..YAML-05. No analysis/optimization logic, no secret resolution or
redaction, no SSH/pull integration (those are later phases). This phase is a
library (`haco.yaml` / config-tree module) plus its tests; it is exercised
against fixture config trees, not a live HA.
</domain>

<decisions>
## Implementation Decisions

### Touched-file rewrite contract
- **D-01:** When a node changes, rewrite the containing file by **surgical text
  splice** — locate the changed node's source byte range and replace only that
  span; every other byte of the file (comments, blank lines, quote style,
  indentation, trailing newline) stays exactly as read from disk. Do **not** do a
  full `ruamel` dump of a touched file. — **Reversibility:** costly — the loader
  must attach source byte-range provenance to every editable node from the start;
  retrofitting span tracking later touches the load path, the mutation API, and
  every write test.
- **D-02:** `ruamel.yaml` (`typ='rt'`, `preserve_quotes=True`) is still the
  parser and the source of line/column data (`.lc`) used to compute spans; it is
  just never used as the *emitter* for a touched file. Serializing a *new* node
  value (the replacement text for the spliced span) uses ruamel with HA's 2-space
  block style so the inserted text matches surrounding conventions.
- **D-03:** If the changed node's byte range cannot be resolved unambiguously
  (e.g. a value produced by an `!include_dir_*` merge that has no single source
  span), the write fails loudly for that node with a clear message rather than
  falling back to a whole-file dump.

### Include handling and tree shape
- **D-04:** Follow every `!include`, `!include_dir_list`, `!include_dir_merge_list`,
  `!include_dir_named`, `!include_dir_merge_named` transitively from
  `configuration.yaml`, and also resolve `packages:` entries. Load every resolved
  target file into the ConfigTree as its own **editable** file node (path -> root
  node + original bytes + span index). — **Reversibility:** costly — later phases
  assume they can edit inside any included file; narrowing this later breaks them.
- **D-05:** The include **graph** (YAML-03) is a byproduct of the load walk: an
  edge `parent file --tag--> child path(s)`, with the `!include_dir_*` variants
  expanding to one edge per matched file. Directory scan matches HA's real loader
  (`annotatedyaml._find_files`, verified in 02-RESEARCH.md): **recursive**
  (`os.walk`), `.yaml` files only, `sorted()` per directory, dotfiles and
  `secrets.yaml` skipped. `secrets.yaml` is **not** a node in the graph in this
  phase. *(Amended 2026-08-30 after research — original D-05 said "non-recursive",
  which contradicts HA source.)*
- **D-06:** `!include*` tag nodes themselves round-trip as **opaque tagged
  scalars** — they re-emit verbatim; includes are never inlined into the parent
  file. The child file's content is edited in the child file.
- **D-07:** Anchors/aliases (`&x` / `*x`) are preserved within a file but never
  resolved across `!include` boundaries (HA merges post-include).

### Custom tags and secrets
- **D-08:** Register constructors + representers for `!secret`, `!include`,
  `!include_dir_list`, `!include_dir_merge_list`, `!include_dir_named`,
  `!include_dir_merge_named`, `!env_var`, `!input` before parsing. Unknown `!`
  tags also round-trip opaquely rather than crashing (warn, don't fail).
- **D-09:** `!secret <key>` stays an opaque tagged scalar. `secrets.yaml` is
  **not** loaded, parsed, or resolved in Phase 2. Secret resolution and redaction
  are a later phase.

### Idempotency (YAML-05) — what Phase 2 asserts
- **D-10:** No analysis engine exists yet, so the idempotency requirement is
  proven at the engine level: **no-op mutation stability**.
  1. `load -> serialize -> load -> serialize` on a real fixture tree is a fixed
     point: the second serialization equals the first, byte-for-byte, per file.
  2. Applying an **empty** change set rewrites **zero** files on disk.
  3. Applying a mutation and then reverting it (setting the node back to its
     original value) leaves every file byte-identical to the pre-mutation state.

### Claude's Discretion
- In-memory API shape (how a caller addresses and mutates a node — path tuples,
  a visitor, dotted keys), the span-index data structure, and how original bytes
  are cached (per-file string vs mmap) are the planner's/executor's call, as long
  as D-01..D-10 hold.
- Fixture design: a representative HA config tree covering every tag in D-08,
  nested includes, `include_dir_*` directories, comments, both quote styles,
  anchors within a file, and a `packages:` block.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` §"Phase 2: YAML Round-Trip Engine" — goal + 5 success criteria
- `.planning/REQUIREMENTS.md` — YAML-01..YAML-05 definitions and traceability
- `.planning/PROJECT.md` — core value, key decisions (ruamel round-trip is the deciding factor for Python)

### Technical research (already in-repo)
- `.planning/research/PITFALLS.md` §"YAML round-trip" — HA tag crashes, ruamel silent reformat, anchors across includes, redaction scope
- `.planning/research/STACK.md` — `ruamel.yaml` (`typ='rt'`) rationale, rejected alternatives
- `.planning/research/ARCHITECTURE.md` — `haco.yaml` parse stage, `ConfigTree` (path -> ruamel node + include graph)
- `.planning/research/FEATURES.md` — faithful-parse tag list
- `.planning/research/SUMMARY.md` — YAML engine flagged as standalone high-risk phase

### External
- https://pypi.org/project/ruamel.yaml/ — round-trip mode, `.lc` line/col data, `preserve_quotes`
- Home Assistant `!include*` / `packages:` semantics (directory scan order, merge behavior) — verify against HA docs during research

### Phase 1 output this phase builds on
- `src/haco/` — existing package (models, errors, ssh, discover, check, preflight, connect). Phase 2 adds the yaml/config-tree module alongside these.
- `.planning/phases/01-connect-discover/01-0*-SUMMARY.md` — established patterns (quality gate, frozen dataclasses, error hierarchy, one-atomic-commit-per-task)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/haco/errors.py` — `HacoError` base hierarchy; add a `YamlError` / `ConfigTreeError` family here rather than inventing a new base.
- Phase 1 quality gate (`uv run ruff check . && black --check . && mypy --strict && pytest -q`) and `pyproject.toml` config are already wired; Phase 2 code must pass the same gate.
- Frozen-dataclass result pattern (`CmdResult`, `HostFacts`, `CheckResult`, `PreflightResult`) — reuse for `ConfigTree` / include-graph result types.

### Established Patterns
- `src/haco/` src-layout package, `mypy --strict`, ruff line-length 120, one atomic commit per task, SUMMARY.md per plan.
- Library modules hold all behavior; any CLI surface is a thin wrapper (Phase 2 likely adds no CLI command yet, or only a hidden debug one).

### Integration Points
- `ruamel.yaml` 0.18+ is already declared as a runtime dep in `pyproject.toml` (added in Phase 1, unused so far).
- Later phases (pull, analyze, apply, rollback) consume the `ConfigTree` + include graph produced here.

</code_context>

<specifics>
## Specific Ideas

- "Untouched byte preserved" is to be taken literally for touched files: the test
  suite should assert a byte-level diff between the original file and the rewritten
  file touches **only** the span of the changed node.
- The idempotency test should run against a real-shaped fixture tree, not a
  single toy file.

</specifics>

<deferred>
## Deferred Ideas

- Secret resolution / `secrets.yaml` parsing / redaction-on-send — later phase (redaction is called out in PITFALLS.md as broader than `!secret`).
- Reload-changed-domains-without-restart — v2 (API-02).
- Any analysis/optimization proposal engine — later phase; YAML-05's "zero proposed changes" against a real analyzer is re-verified then.
- Following anchors/aliases across include boundaries — explicitly rejected (D-07).

None of the above are in Phase 2 scope.

</deferred>

---

*Phase: 02-yaml-round-trip-engine*
*Context gathered: 2026-08-30*
