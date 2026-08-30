"""Surgical splice writer: rewrite only the files carrying an edit, byte for byte.

CONTEXT.md D-01 is the decision this module exists to honour. A touched file is
rewritten as ``original[:span.start] + rendered_new_value + original[span.end:]``
- every comment, blank line, quote style, indentation character and the trailing
newline outside the changed node's span survives exactly as read from disk. A
``ruamel`` dump of a whole file would silently reflow block sequences and
normalise style; there is deliberately no such fallback anywhere here (D-03).

Files with no edit are never opened for writing at all, which is how YAML-02's
"load then dump is byte-identical" is actually satisfied - see :func:`flush` and
:meth:`haco.configtree.tree.ConfigTree.dirty_files`.

The replacement text for a span is produced by :func:`render_scalar`, which wraps
the new value in ``ruamel``'s matching scalar-string class and lets ``ruamel``
render it (correct escaping of quotes, backslashes and newlines) rather than
hand-rolling any quoting (D-02, threat T-02-13).
"""

from __future__ import annotations

import contextlib
import io
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from ruamel.yaml.comments import CommentedSeq
from ruamel.yaml.scalarstring import (
    DoubleQuotedScalarString,
    FoldedScalarString,
    LiteralScalarString,
    PlainScalarString,
    ScalarString,
    SingleQuotedScalarString,
)

from haco.configtree.loader import make_yaml
from haco.configtree.spans import NodePath, Span, SpanKind
from haco.errors import UnspliceableNodeError

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from haco.configtree.tree import ConfigTree

_SENTINEL_KEY = "_"

_WRAP: dict[str, type[ScalarString]] = {
    "plain": PlainScalarString,
    "single": SingleQuotedScalarString,
    "double": DoubleQuotedScalarString,
    "literal": LiteralScalarString,
    "folded": FoldedScalarString,
}


def splice(text: str, edits: Iterable[tuple[int, int, str]]) -> str:
    """Apply ``(start, end, new)`` triples to ``text``, sorted by ``start`` descending.

    Applying an edit shifts every offset after it, so the edits are applied from
    the end of the file backwards: an edit that has not been applied yet keeps
    the offsets it was recorded with. Pure function of its inputs - no I/O, no
    mutation of ``edits``.
    """
    for start, end, new in sorted(edits, key=lambda edit: edit[0], reverse=True):
        text = text[:start] + new + text[end:]
    return text


def atomic_write(path: Path, text: str) -> None:
    """Write ``text`` to ``path`` atomically via a temp file in ``path``'s own directory.

    ``tempfile.mkstemp`` creates the temp file owner-only inside the target's
    directory (not a world-readable temp location) and on the same filesystem, so
    the final ``os.replace`` is atomic and an interrupted run can never leave
    Home Assistant a half-written config (threat T-02-12). ``newline=""`` means
    no line-ending translation on the way out - CRLF stays CRLF.
    """
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    tmp_path = Path(tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(tmp_path, path)
    except BaseException:
        with contextlib.suppress(OSError):
            tmp_path.unlink()
        raise


def _value_dump(value: object) -> str:
    """Render ``value`` as ``ruamel`` would emit it for a mapping value, prefix stripped.

    Dumps ``{"_": value}`` with the Home Assistant block-style ``YAML`` factory
    and returns everything after the ``"_: "`` key prefix. For a block scalar the
    result keeps its trailing newline; the caller strips it for inline kinds.
    """
    yaml = make_yaml()
    buffer = io.StringIO()
    yaml.dump({_SENTINEL_KEY: value}, buffer)
    return buffer.getvalue()[len(_SENTINEL_KEY) + 2 :]


def _reindent_block(rendered: str, indent: int) -> str:
    """Shift a ``ruamel``-rendered block body from its 2-space indent to ``indent`` spaces.

    ``rendered`` is ``"|\\n  body...\\n"`` (or ``">\\n  ..."``); the indicator line
    is kept as-is and every body line's two-space lead is replaced with ``indent``
    spaces. Blank fold-separator lines are left blank. Exactly one trailing
    newline is guaranteed, because for the literal/folded kinds ``end_mark`` sits
    at column zero of the following line and a missing newline would run that
    line into the block (RESEARCH.md Pitfall 3).
    """
    lines = rendered.split("\n")
    out = [lines[0]]
    for line in lines[1:]:
        if line.startswith("  "):
            out.append(" " * indent + line[2:])
        else:
            out.append(line)
    result = "\n".join(out)
    if not result.endswith("\n"):
        result += "\n"
    return result


def render_scalar(
    value: object,
    kind: SpanKind,
    indent: int = 0,
    *,
    original: str | None = None,
) -> str:
    """Render ``value`` as replacement text in the scalar style named by ``kind`` (D-02).

    ``indent`` is the column the original block body was indented to and is used
    only for the ``literal`` / ``folded`` kinds. ``original`` is the source slice
    of the span being replaced and is required for the ``tagged`` kind, whose tag
    text is kept verbatim so an ``!include`` stays an ``!include`` (D-06).

    Raises :class:`haco.errors.UnspliceableNodeError` for the ``collection`` kind -
    a block mapping or sequence has no single-scalar replacement form.
    """
    if kind == "collection":
        raise UnspliceableNodeError(
            Path("<render_scalar>"),
            (),
            "value is a block collection; only scalar values can be spliced",
        )
    if kind == "tagged":
        if original is None:
            raise ValueError("rendering a tagged node needs its original source text")
        tag = original.split(None, 1)[0]
        return f"{tag} {value}"
    if kind == "flow":
        payload: object = value
        if isinstance(value, (list, tuple)):
            sequence = CommentedSeq(value)
            sequence.fa.set_flow_style()
            payload = sequence
        return _value_dump(payload).rstrip("\n")

    text = str(value)
    if kind in ("literal", "folded"):
        if not text.endswith("\n"):
            text += "\n"
        rendered = _value_dump(_WRAP[kind](text))
        return _reindent_block(rendered, indent)

    rendered = _value_dump(_WRAP[kind](text))
    return rendered[:-1] if rendered.endswith("\n") else rendered


def _file_edits(
    spans: Mapping[NodePath, Span],
    edits: dict[NodePath, str],
) -> list[tuple[int, int, str]]:
    return [(spans[path].start, spans[path].end, new) for path, new in edits.items()]


def serialize(tree: ConfigTree) -> dict[Path, str]:
    """Return the text every file in ``tree`` would be written with - no disk access.

    A dirty file's entry is its original text spliced with its recorded edits; a
    clean file's entry is its cached original text verbatim. Plan 02-04's
    fixed-point harness is built on this, so it must be a pure function of the
    loaded tree.
    """
    out: dict[Path, str] = {}
    for node in tree.files.values():
        if node.edits:
            out[node.rel] = splice(node.text, _file_edits(node.spans, node.edits))
        else:
            out[node.rel] = node.text
    return out


def flush(tree: ConfigTree) -> tuple[Path, ...]:
    """Write every dirty file in ``tree`` atomically; return the paths written.

    A file with no recorded edit is never opened for writing (YAML-02 under
    D-01). The returned tuple is the truthful record of what changed on disk
    (threat T-02-15), root-relative and sorted.
    """
    written: list[Path] = []
    for node in tree.files.values():
        if not node.edits:
            continue
        new_text = splice(node.text, _file_edits(node.spans, node.edits))
        atomic_write(node.path, new_text)
        written.append(node.rel)
    return tuple(sorted(written, key=lambda path: path.as_posix()))


__all__ = [
    "atomic_write",
    "flush",
    "render_scalar",
    "serialize",
    "splice",
]
