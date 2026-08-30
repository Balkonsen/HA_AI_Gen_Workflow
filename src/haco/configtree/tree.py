"""The whole-tree config engine: walk from ``configuration.yaml`` and load every file.

:func:`load_config_tree` is the single entry point. It runs a depth-first walk
from ``<root>/configuration.yaml``, and for every file it:

1. parses it with :func:`haco.configtree.loader.load_file` (round-trip tree +
   span index + original text);
2. asks :func:`haco.configtree.includes.iter_include_refs` for every
   ``!include`` / ``!include_dir_*`` reference it carries;
3. resolves each reference with
   :func:`haco.configtree.includes.resolve_include_targets` (HA path rules,
   containment check, recursive ``.yaml``-only directory scan);
4. appends one :class:`haco.configtree.graph.IncludeEdge` per resolved target
   and recurses into any target not already loaded.

A target already on the loading stack is a back edge: :class:`IncludeCycleError`
is raised carrying the ordered cycle, so an include loop fails cleanly instead
of dying with ``RecursionError`` the way Home Assistant's own loader does. Every
resolved target becomes its own editable :class:`FileNode` (CONTEXT.md D-04);
``!include*`` tags themselves stay opaque and ``secrets.yaml`` / ``!secret`` are
never opened (D-06, D-09).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from haco.configtree.graph import IncludeEdge, IncludeGraph
from haco.configtree.includes import iter_include_refs, resolve_include_targets
from haco.configtree.loader import load_file
from haco.configtree.spans import NodePath, Span
from haco.configtree.writer import render_scalar
from haco.errors import IncludeCycleError, MissingIncludeError, UnspliceableNodeError

CONFIG_ENTRYPOINT = "configuration.yaml"


def _block_body_indent(source: str) -> int:
    """The column a literal/folded block's body was indented to in ``source``.

    ``source`` is the span slice, e.g. ``"|\\n      body\\n"``; the answer is the
    lead-space count of the first non-blank line after the ``|`` / ``>`` line, so
    the replacement body lands in the same column as the one it replaces.
    """
    newline = source.find("\n")
    if newline == -1:
        return 0
    for line in source[newline + 1 :].split("\n"):
        stripped = line.lstrip(" ")
        if stripped:
            return len(line) - len(stripped)
    return 0


@dataclass
class FileNode:
    """One editable config file: its original text, round-trip tree, and span index.

    ``rel`` is the path relative to the config root (the key used in
    :attr:`ConfigTree.files`); ``path`` is the absolute, resolved path the writer
    works from. ``edits`` accumulates pending ``node_path -> rendered text``
    replacements; :attr:`dirty` is true once any exist.
    """

    rel: Path
    path: Path
    text: str
    data: Any
    spans: Mapping[NodePath, Span]
    edits: dict[NodePath, str] = field(default_factory=dict)

    @property
    def dirty(self) -> bool:
        return bool(self.edits)


@dataclass
class ConfigTree:
    """A loaded Home Assistant config tree: every reachable file plus the include graph.

    ``files`` is keyed by the path **relative to** :attr:`root`;
    :attr:`FileNode.rel` holds the same value. :meth:`node` accepts either an
    absolute path or a root-relative one.
    """

    root: Path
    files: dict[Path, FileNode]
    graph: IncludeGraph

    def node(self, path: Path | str) -> FileNode:
        """The :class:`FileNode` for ``path`` (absolute or root-relative)."""
        return self.files[self._relative(path)]

    def get(self, file: Path | str, node_path: NodePath) -> Any:
        """The live value at ``node_path`` inside ``file``'s round-trip tree."""
        data: Any = self.node(file).data
        for step in node_path:
            data = data[step]
        return data

    def source_text(self, file: Path | str, node_path: NodePath) -> str:
        """The exact source slice backing ``node_path`` inside ``file``."""
        node = self.node(file)
        span = node.spans[node_path]
        return node.text[span.start : span.end]

    def set(self, file: Path | str, node_path: NodePath, value: object) -> None:
        """Record a replacement of ``node_path`` inside ``file`` with ``value``.

        Renders ``value`` in the node's own scalar style and stores the text
        against the file's :class:`FileNode`; the disk is not touched here, so an
        aborted review in a later phase writes nothing. Raises
        :class:`haco.errors.UnspliceableNodeError` - and records nothing - when
        the path has no span, when the span was reached through a YAML alias or
        ``<<`` merge, or when it covers a whole block collection (CONTEXT.md
        D-03). There is no whole-file dump fallback.
        """
        node = self.node(file)
        span = node.spans.get(node_path)
        if span is None:
            raise UnspliceableNodeError(node.rel, node_path, "no source span for this path")
        if span.unspliceable is not None:
            raise UnspliceableNodeError(node.rel, node_path, span.unspliceable)
        if span.kind == "collection":
            raise UnspliceableNodeError(
                node.rel,
                node_path,
                "value is a block collection; only scalar values can be spliced",
            )
        original = node.text[span.start : span.end]
        indent = _block_body_indent(original) if span.kind in ("literal", "folded") else 0
        node.edits[node_path] = render_scalar(value, span.kind, indent, original=original)

    def dirty_files(self) -> tuple[Path, ...]:
        """The root-relative paths of every file carrying at least one edit, sorted."""
        dirty = (node.rel for node in self.files.values() if node.dirty)
        return tuple(sorted(dirty, key=lambda path: path.as_posix()))

    def _relative(self, path: Path | str) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate.resolve().relative_to(self.root)
        return candidate


def load_config_tree(root: Path) -> ConfigTree:
    """Load the whole config tree rooted at ``root / 'configuration.yaml'``.

    Raises :class:`haco.errors.MissingIncludeError` if the entrypoint is absent,
    :class:`haco.errors.IncludeCycleError` on an include loop,
    :class:`haco.errors.IncludeEscapeError` on a target outside ``root``, and
    :class:`haco.errors.MissingIncludeError` on a missing include target.
    """
    resolved_root = root.resolve()
    entrypoint = resolved_root / CONFIG_ENTRYPOINT
    if not entrypoint.is_file():
        raise MissingIncludeError(resolved_root, CONFIG_ENTRYPOINT, entrypoint)

    done: dict[Path, FileNode] = {}
    edges: list[IncludeEdge] = []
    loading: list[Path] = []

    def rel(path: Path) -> Path:
        return path.resolve().relative_to(resolved_root)

    def visit(path: Path) -> None:
        path = path.resolve()
        if path in loading:
            cycle = [*loading[loading.index(path) :], path]
            raise IncludeCycleError([rel(item) for item in cycle])
        if path in done:
            return
        loading.append(path)
        loaded = load_file(path)
        node = FileNode(
            rel=rel(path),
            path=path,
            text=loaded.text,
            data=loaded.data,
            spans=loaded.spans,
        )
        done[path] = node
        for node_path, tag, argument in iter_include_refs(loaded.data):
            for target in resolve_include_targets(path, tag, argument, resolved_root):
                resolved_target = target.resolve()
                edges.append(IncludeEdge(rel(path), node_path, tag, rel(resolved_target)))
                visit(resolved_target)
        loading.pop()

    visit(entrypoint)

    files = {node.rel: node for node in done.values()}
    graph = IncludeGraph(
        root=resolved_root,
        edges=tuple(edges),
        files=tuple(sorted(files, key=lambda p: p.as_posix())),
    )
    return ConfigTree(root=resolved_root, files=files, graph=graph)


__all__ = ["CONFIG_ENTRYPOINT", "ConfigTree", "FileNode", "load_config_tree"]
