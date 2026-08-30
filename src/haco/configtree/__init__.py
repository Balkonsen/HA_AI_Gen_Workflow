"""The haco config-tree engine: comment- and tag-preserving YAML with source spans."""

from __future__ import annotations

from haco.configtree.loader import (
    KNOWN_HA_TAGS,
    LoadedFile,
    load_file,
    make_yaml,
    warn_unknown_tags,
)
from haco.configtree.spans import NodePath, Span, SpanKind, build_span_index
from haco.errors import DuplicateKeyError, MultiDocumentError

__all__ = [
    "KNOWN_HA_TAGS",
    "DuplicateKeyError",
    "LoadedFile",
    "MultiDocumentError",
    "NodePath",
    "Span",
    "SpanKind",
    "build_span_index",
    "load_file",
    "make_yaml",
    "warn_unknown_tags",
]
