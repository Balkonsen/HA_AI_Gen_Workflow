"""The haco config-tree engine: comment- and tag-preserving YAML with source spans."""

from __future__ import annotations

from haco.configtree.graph import IncludeEdge, IncludeGraph
from haco.configtree.includes import (
    INCLUDE_TAGS,
    SECRET_YAML,
    ensure_contained,
    find_dir_yaml,
    iter_include_refs,
    resolve_include_targets,
)
from haco.configtree.loader import (
    KNOWN_HA_TAGS,
    LoadedFile,
    load_file,
    make_yaml,
    warn_unknown_tags,
)
from haco.configtree.spans import NodePath, Span, SpanKind, build_span_index
from haco.configtree.tree import ConfigTree, FileNode, load_config_tree
from haco.configtree.writer import atomic_write, flush, render_scalar, serialize, splice
from haco.errors import (
    DuplicateKeyError,
    IncludeCycleError,
    IncludeError,
    IncludeEscapeError,
    MissingIncludeError,
    MultiDocumentError,
    UnspliceableNodeError,
)

__all__ = [
    "INCLUDE_TAGS",
    "KNOWN_HA_TAGS",
    "SECRET_YAML",
    "ConfigTree",
    "DuplicateKeyError",
    "FileNode",
    "IncludeCycleError",
    "IncludeEdge",
    "IncludeError",
    "IncludeEscapeError",
    "IncludeGraph",
    "LoadedFile",
    "MissingIncludeError",
    "MultiDocumentError",
    "NodePath",
    "Span",
    "SpanKind",
    "UnspliceableNodeError",
    "atomic_write",
    "build_span_index",
    "ensure_contained",
    "find_dir_yaml",
    "flush",
    "iter_include_refs",
    "load_config_tree",
    "load_file",
    "make_yaml",
    "render_scalar",
    "resolve_include_targets",
    "serialize",
    "splice",
    "warn_unknown_tags",
]
