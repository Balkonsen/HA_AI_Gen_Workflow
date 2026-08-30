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

import re
import warnings
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.constructor import DuplicateKeyError as _RuamelDuplicateKeyError

from haco.configtree.spans import NodePath, Span, build_span_index
from haco.errors import DuplicateKeyError, MultiDocumentError

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


def _tag_value(obj: Any) -> str | None:
    """The string form of a value's YAML tag, or ``None`` if it carries no ``!`` tag."""
    tag = getattr(obj, "tag", None)
    if tag is None:
        return None
    value = getattr(tag, "value", tag)
    return value if isinstance(value, str) else None


def warn_unknown_tags(data: Any, path: Path) -> frozenset[str]:
    """Walk ``data`` for tags outside :data:`KNOWN_HA_TAGS` and warn once per distinct tag.

    ``ruamel.yaml`` round-trips an unrecognised ``!tag`` silently as an inert
    ``TaggedScalar`` / tagged ``Commented*`` - it never constructs a Python
    object and never warns. D-08 requires warn-not-fail, so the warning is ours
    to emit here. A ``!secret`` argument is a key name, never a value, and is
    never included in the warning text.
    """
    unknown: set[str] = set()

    def visit(obj: Any) -> None:
        tag = _tag_value(obj)
        if tag is not None and tag.startswith("!") and tag not in KNOWN_HA_TAGS:
            unknown.add(tag)
        if isinstance(obj, Mapping):
            for value in obj.values():
                visit(value)
        elif isinstance(obj, (list, tuple)):
            for value in obj:
                visit(value)

    visit(data)
    for tag in sorted(unknown):
        warnings.warn(
            f"unknown YAML tag {tag!r} in {path.name}; round-tripped opaquely",
            stacklevel=2,
        )
    return frozenset(unknown)


def _duplicate_key(exc: _RuamelDuplicateKeyError) -> str | None:
    message = getattr(exc, "problem", None) or str(exc)
    match = re.search(r"""duplicate key ["']([^"']+)["']""", message)
    return match.group(1) if match else None


def load_file(path: Path) -> LoadedFile:
    """Parse ``path`` into a :class:`LoadedFile` (single file - includes stay opaque).

    Raises :class:`haco.errors.MultiDocumentError` if the file holds a second
    ``---`` document and :class:`haco.errors.DuplicateKeyError` if a mapping key
    repeats, rather than silently dropping data.
    """
    text = path.read_bytes().decode("utf-8")
    documents = list(make_yaml().compose_all(text))
    if len(documents) > 1:
        raise MultiDocumentError(path)
    root = documents[0] if documents else None
    try:
        data = make_yaml().load(text)
    except _RuamelDuplicateKeyError as exc:
        raise DuplicateKeyError(path, _duplicate_key(exc)) from exc
    spans: dict[NodePath, Span] = build_span_index(root, path) if root is not None else {}
    unknown_tags = warn_unknown_tags(data, path)
    return LoadedFile(path=path, text=text, data=data, spans=spans, unknown_tags=unknown_tags)


__all__ = [
    "KNOWN_HA_TAGS",
    "LoadedFile",
    "load_file",
    "make_yaml",
    "warn_unknown_tags",
]
