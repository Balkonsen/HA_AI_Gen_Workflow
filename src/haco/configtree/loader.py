"""Round-trip ``ruamel.yaml`` loader for a single Home Assistant config file.

The file is read as raw bytes and decoded as UTF-8 with no newline translation,
so CRLF endings and a leading BOM survive verbatim (they are load-bearing for
"every untouched byte preserved"). ``Path.read_text(newline=...)`` only exists on
Python 3.13+, hence the explicit ``read_bytes().decode()``. The text is then
parsed twice with a fresh :func:`make_yaml` instance:

* ``compose()`` builds the mark-carrying node tree that
  :func:`haco.configtree.spans.build_span_index` turns into source spans;
* ``load()`` builds the navigable ``CommentedMap`` / ``CommentedSeq`` tree the
  caller reads and mutates.

Every ``ruamel`` call is confined to this module and :mod:`haco.configtree.spans`
so the loosely typed parser surface never leaks into ``mypy --strict`` code.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from haco.configtree.spans import NodePath, Span, build_span_index

KNOWN_HA_TAGS: frozenset[str] = frozenset(
    {
        "!secret",
        "!include",
        "!include_dir_list",
        "!include_dir_merge_list",
        "!include_dir_named",
        "!include_dir_merge_named",
        "!env_var",
        "!input",
    }
)
"""The eight custom YAML tags Home Assistant's loader registers (CONTEXT.md D-08)."""


def make_yaml() -> YAML:
    """Build a round-trip ``YAML`` configured for Home Assistant's block style."""
    yaml = YAML()  # typ="rt" by default
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 1_000_000  # never auto-wrap when rendering a replacement scalar
    return yaml


@dataclass(frozen=True)
class LoadedFile:
    """One parsed config file: its original text, editable tree, and span index."""

    path: Path
    text: str
    data: Any
    spans: Mapping[NodePath, Span]
    unknown_tags: frozenset[str]


def load_file(path: Path) -> LoadedFile:
    """Parse ``path`` into a :class:`LoadedFile` (single file - includes are opaque)."""
    text = path.read_bytes().decode("utf-8")
    root = make_yaml().compose(text)
    data = make_yaml().load(text)
    spans: dict[NodePath, Span] = build_span_index(root, path) if root is not None else {}
    return LoadedFile(path=path, text=text, data=data, spans=spans, unknown_tags=frozenset())


__all__ = ["KNOWN_HA_TAGS", "LoadedFile", "load_file", "make_yaml"]
