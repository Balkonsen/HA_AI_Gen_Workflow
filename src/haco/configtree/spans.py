"""Source-byte provenance for a single parsed YAML file.

:func:`build_span_index` walks the ``ruamel.yaml`` ``compose()`` node tree and
records, for every node, an absolute ``(start, end)`` character offset back into
the file's original text. That range is what lets a later mutation splice a new
value in place (``text[:start] + rendered + text[end:]``) without disturbing any
other byte - the ``costly`` provenance requirement in CONTEXT.md D-01.

The walk also guards YAML aliases (D-03, D-07): in ``compose()`` a ``*alias``
resolves to the *same* node object as its ``&anchor``, so the second time a node
object is seen it was reached through an alias. Such a path is recorded as
``unspliceable`` - naming the anchor - and never descended into, so the anchor's
offsets are never mis-attributed to the alias path.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ruamel.yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

NodePath = tuple[str | int, ...]
"""A logical path to a node: mapping keys as strings, sequence indices as ints."""

SpanKind = Literal[
    "plain",
    "single",
    "double",
    "literal",
    "folded",
    "flow",
    "tagged",
    "collection",
]
"""How the source text of a span is delimited - drives replacement rendering."""


@dataclass(frozen=True)
class Span:
    """An absolute character range for one node in its origin file's text."""

    file: Path
    start: int
    end: int
    kind: SpanKind
    unspliceable: str | None = None


def _anchor_name(node: Node) -> str:
    """Best-effort name of the anchor a node was defined with."""
    anchor = getattr(node, "anchor", None)
    value = getattr(anchor, "value", anchor)
    return str(value) if value else "<anonymous>"


def _alias_reason(node: Node) -> str:
    return (
        f"value is shared via a YAML alias/merge to anchor '{_anchor_name(node)}'; "
        f"edit the anchor definition instead"
    )


def _classify(node: Node) -> SpanKind:
    """Map a ``compose()`` node to the :class:`SpanKind` its source text is delimited by.

    A ``!`` tag wins over style: an ``!include`` scalar is ``"tagged"`` no matter
    how it is written. The literal and folded kinds are the ones whose span runs
    through the block's trailing newline - a later splice must re-emit that
    newline or it bleeds into the next line.
    """
    if str(node.tag).startswith("!"):
        return "tagged"
    if isinstance(node, ScalarNode):
        style = node.style
        if style == "'":
            return "single"
        if style == '"':
            return "double"
        if style == "|":
            return "literal"
        if style == ">":
            return "folded"
        return "plain"
    if isinstance(node, (MappingNode, SequenceNode)):
        return "flow" if getattr(node, "flow_style", False) else "collection"
    return "plain"


def _key(key_node: Node) -> str:
    """Canonical string form of a mapping key node.

    ``compose()`` gives ``key_node.value`` as the raw source string; the parallel
    ``load()`` tree may key on a typed value (int/bool/date). Both sides resolve
    to this string form so a caller's path lookups line up with the span index.
    """
    return str(key_node.value)


def build_span_index(root: Node, file: Path) -> dict[NodePath, Span]:
    """Map every node in the ``compose()`` tree rooted at ``root`` to its :class:`Span`."""
    spans: dict[NodePath, Span] = {}
    seen: set[int] = set()

    def walk(node: Node, path: NodePath) -> None:
        if id(node) in seen:
            spans[path] = Span(
                file,
                int(node.start_mark.index),
                int(node.end_mark.index),
                _classify(node),
                _alias_reason(node),
            )
            return
        seen.add(id(node))
        spans[path] = Span(
            file,
            int(node.start_mark.index),
            int(node.end_mark.index),
            _classify(node),
            None,
        )
        if isinstance(node, MappingNode):
            for key_node, value_node in node.value:
                walk(value_node, (*path, _key(key_node)))
        elif isinstance(node, SequenceNode):
            for index, value_node in enumerate(node.value):
                walk(value_node, (*path, index))

    walk(root, ())
    return spans


__all__ = ["NodePath", "Span", "SpanKind", "build_span_index"]
