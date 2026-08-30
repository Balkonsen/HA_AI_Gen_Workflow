"""Tests for :mod:`haco.configtree.writer` - the surgical splice writer (D-01..D-03).

The contract: editing one node and flushing rewrites exactly the file that owns
that node, by replacing only the changed node's source span; every other byte of
that file and every other file (bytes *and* mtime) is left exactly as it was on
disk. An unresolvable or alias-derived span raises and writes nothing.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from haco.configtree import atomic_write, flush, load_config_tree, serialize, splice
from haco.errors import UnspliceableNodeError
from tests.support.snapshots import snapshot_tree

_CONFIG = "configuration.yaml"
_AUTOMATIONS = "automations.yaml"
_ENCODING = "encoding/crlf_bom.yaml"

# Built from codepoints so this test source stays pure ASCII on disk.
_BOM = chr(0xFEFF)
_NAIVE = "plain na" + chr(0xEF) + "ve value"
_DEGREES = chr(0x22) + chr(0xB0) + "C" + chr(0x22)


def _text(root: Path, rel: str) -> str:
    return (root / rel).read_bytes().decode("utf-8")


# --------------------------------------------------------------------------- #
# Task 1: end-to-end tracer - edit one value, rewrite one file, touch one span
# --------------------------------------------------------------------------- #


def test_dirty_only_one_file_rewritten(ha_config_tree: Path) -> None:
    original = snapshot_tree(ha_config_tree)
    tree = load_config_tree(ha_config_tree)

    tree.set(_CONFIG, ("homeassistant", "name"), "My House")
    written = flush(tree)

    assert written == (Path(_CONFIG),)

    new_config = _text(ha_config_tree, _CONFIG)
    assert "name: My House" in new_config
    assert "My Home" not in new_config

    after = snapshot_tree(ha_config_tree)
    for path, (raw, mtime) in original.items():
        if path == ha_config_tree / _CONFIG:
            continue
        assert after[path][0] == raw, f"{path} bytes changed"
        assert after[path][1] == mtime, f"{path} mtime changed"


def test_splice_touches_only_the_span(ha_config_tree: Path) -> None:
    original_text = _text(ha_config_tree, _CONFIG)
    tree = load_config_tree(ha_config_tree)

    node_path = ("homeassistant", "name")
    span = tree.node(_CONFIG).spans[node_path]
    tree.set(_CONFIG, node_path, "My House")
    flush(tree)

    rewritten = _text(ha_config_tree, _CONFIG)
    assert rewritten == original_text[: span.start] + "My House" + original_text[span.end :]
    assert original_text[: span.start] == rewritten[: span.start]
    assert original_text[span.end :] == rewritten[len(rewritten) - (len(original_text) - span.end) :]


def test_set_performs_no_disk_io(ha_config_tree: Path) -> None:
    tree = load_config_tree(ha_config_tree)
    before = snapshot_tree(ha_config_tree)

    tree.set(_CONFIG, ("homeassistant", "name"), "My House")

    assert snapshot_tree(ha_config_tree) == before
    assert tree.dirty_files() == (Path(_CONFIG),)


def test_splice_is_pure_and_applies_descending() -> None:
    text = "abcdefghij"
    edits = [(2, 4, "XX"), (6, 8, "YYYY")]
    once = splice(text, edits)
    assert once == "abXXefYYYYij"
    assert splice(text, list(reversed(edits))) == once
    assert text == "abcdefghij"


def test_atomic_write_replaces_and_leaves_no_temp(tmp_path: Path) -> None:
    target = tmp_path / "sub" / "f.yaml"
    target.parent.mkdir()
    target.write_text("original\n", encoding="utf-8")

    atomic_write(target, "replaced\n")

    assert target.read_text(encoding="utf-8") == "replaced\n"
    assert [p.name for p in target.parent.iterdir()] == ["f.yaml"]


def test_atomic_write_unlinks_temp_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "f.yaml"
    target.write_text("original\n", encoding="utf-8")

    def boom(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("replace failed")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(RuntimeError):
        atomic_write(target, "replaced\n")

    assert target.read_text(encoding="utf-8") == "original\n"
    assert [p.name for p in tmp_path.iterdir()] == ["f.yaml"]


def test_flush_empty_change_set_writes_nothing(ha_config_tree: Path) -> None:
    before = snapshot_tree(ha_config_tree)
    tree = load_config_tree(ha_config_tree)

    assert flush(tree) == ()
    assert snapshot_tree(ha_config_tree) == before


# --------------------------------------------------------------------------- #
# Task 2: style-preserving rendering per scalar kind, encoding, multi-edit
# --------------------------------------------------------------------------- #

# (rel, node_path, new value, exact replacement text expected in the span)
_SPLICE_CASES: list[tuple[str, tuple[str | int, ...], object, str]] = [
    (_CONFIG, ("homeassistant", "name"), "My House", "My House"),
    (_CONFIG, ("homeassistant", "time_zone"), 'Europe/"Oslo"', '"Europe/\\"Oslo\\""'),
    (_AUTOMATIONS, (0, "id"), "1700000000099", "'1700000000099'"),
    (_AUTOMATIONS, (1, "variables", "template_body"), "Rear door opened\n", "|\n      Rear door opened\n"),
    (_AUTOMATIONS, (0, "description"), "All lights on", ">\n    All lights on\n"),
    (
        _AUTOMATIONS,
        (0, "action", 0, "target", "entity_id"),
        ["light.kitchen", "light.den"],
        "[light.kitchen, light.den]",
    ),
]


@pytest.mark.parametrize(("rel", "node_path", "new_value", "expected"), _SPLICE_CASES)
def test_splice_span_touches_only_target(
    ha_config_tree: Path,
    rel: str,
    node_path: tuple[str | int, ...],
    new_value: object,
    expected: str,
) -> None:
    original = _text(ha_config_tree, rel)
    tree = load_config_tree(ha_config_tree)
    span = tree.node(rel).spans[node_path]

    tree.set(rel, node_path, new_value)
    result = serialize(tree)[Path(rel)]

    assert result == original[: span.start] + expected + original[span.end :]
    # prefix and suffix around the span are byte-identical
    assert result.startswith(original[: span.start])
    assert result.endswith(original[span.end :])
    # the physical line after the edited node is untouched
    assert _line_after(original, span.end) == _line_after(result, span.start + len(expected))


def _line_after(text: str, pos: int) -> str:
    newline = text.find("\n", pos)
    if newline == -1:
        return ""
    end = text.find("\n", newline + 1)
    return text[newline + 1 : end if end != -1 else len(text)]


def test_double_quoted_replacement_escapes_embedded_quote(ha_config_tree: Path) -> None:
    tree = load_config_tree(ha_config_tree)
    node_path = ("homeassistant", "time_zone")

    tree.set(_CONFIG, node_path, 'a "quoted" zone')
    result = serialize(tree)[Path(_CONFIG)]

    assert '"a \\"quoted\\" zone"' in result
    assert 'a "quoted" zone' not in result  # the bare form never reaches the file


def test_literal_replacement_has_one_trailing_newline(ha_config_tree: Path) -> None:
    tree = load_config_tree(ha_config_tree)
    rel, node_path = _AUTOMATIONS, (1, "variables", "template_body")
    original = _text(ha_config_tree, rel)
    span = tree.node(rel).spans[node_path]

    tree.set(rel, node_path, "just one line")
    result = serialize(tree)[Path(rel)]

    replacement = result[span.start : len(result) - (len(original) - span.end)]
    assert replacement == "|\n      just one line\n"
    assert not replacement.endswith("\n\n")
    # the line that followed the block is still there, unchanged
    assert original[span.end :] == result[len(result) - (len(original) - span.end) :]


def test_encoding_crlf_bom_splice_preserves_bytes(ha_config_tree: Path) -> None:
    original = _text(ha_config_tree, _ENCODING)
    assert original.startswith(_BOM)
    assert original.count("\r\n") >= 3

    tree = load_config_tree(ha_config_tree)
    span = tree.node(_ENCODING).spans[("label",)]
    tree.set(_ENCODING, ("label",), "Flur")
    written = flush(tree)

    assert Path(_ENCODING) in written
    result = _text(ha_config_tree, _ENCODING)

    assert result == original[: span.start] + '"Flur"' + original[span.end :]
    assert result.startswith(_BOM)
    assert (ha_config_tree / _ENCODING).read_bytes().startswith(b"\xef\xbb\xbf")
    assert result.count("\r\n") == original.count("\r\n")
    assert _NAIVE in result
    assert _DEGREES in result


def test_multiple_edits_in_one_file(ha_config_tree: Path) -> None:
    original = _text(ha_config_tree, _CONFIG)
    tree = load_config_tree(ha_config_tree)
    spans = tree.node(_CONFIG).spans
    name_span = spans[("homeassistant", "name")]
    tz_span = spans[("homeassistant", "time_zone")]

    tree.set(_CONFIG, ("homeassistant", "name"), "House A")
    tree.set(_CONFIG, ("homeassistant", "time_zone"), "Zone B")
    result = serialize(tree)[Path(_CONFIG)]

    edits = [
        (name_span.start, name_span.end, "House A"),
        (tz_span.start, tz_span.end, '"Zone B"'),
    ]
    assert result == splice(original, edits)
    assert splice(original, edits) == splice(original, list(reversed(edits)))
    # applying them one at a time gives the same file
    one = splice(original, [edits[0]])
    assert splice(one, [edits[1]]) == result


# --------------------------------------------------------------------------- #
# Task 3: fail loud on unresolvable spans, and the untouched-file guarantee
# --------------------------------------------------------------------------- #


def test_ambiguous_span_fails_loud_alias(ha_config_tree: Path) -> None:
    before = snapshot_tree(ha_config_tree)
    tree = load_config_tree(ha_config_tree)

    with pytest.raises(UnspliceableNodeError) as caught:
        tree.set(_CONFIG, ("script", "other"), "anything")

    assert "wakeup_script" in str(caught.value)
    assert tree.dirty_files() == ()
    assert flush(tree) == ()
    # no whole-file dump fallback: every file's serialized text is its original
    assert serialize(tree) == {node.rel: node.text for node in tree.files.values()}
    assert snapshot_tree(ha_config_tree) == before


def test_ambiguous_span_fails_loud_unknown_path(ha_config_tree: Path) -> None:
    tree = load_config_tree(ha_config_tree)

    with pytest.raises(UnspliceableNodeError) as caught:
        tree.set(_CONFIG, ("does", "not", "exist"), "x")

    message = str(caught.value)
    assert _CONFIG in message
    assert "('does', 'not', 'exist')" in message
    assert tree.dirty_files() == ()


def test_ambiguous_span_fails_loud_collection(ha_config_tree: Path) -> None:
    tree = load_config_tree(ha_config_tree)

    with pytest.raises(UnspliceableNodeError) as caught:
        tree.set(_CONFIG, ("http",), {"server_port": 9000})

    assert "collection" in str(caught.value)
    assert tree.dirty_files() == ()
    assert flush(tree) == ()


def test_untouched_identical_after_flush(ha_config_tree: Path) -> None:
    before = snapshot_tree(ha_config_tree)
    tree = load_config_tree(ha_config_tree)

    written = flush(tree)

    assert written == ()
    assert snapshot_tree(ha_config_tree) == before


def test_serialize_matches_flush_without_touching_disk(ha_config_tree: Path) -> None:
    before = snapshot_tree(ha_config_tree)
    tree = load_config_tree(ha_config_tree)

    dry = serialize(tree)
    assert set(dry) == set(tree.files)
    assert snapshot_tree(ha_config_tree) == before  # serialize alone touched nothing

    tree.set(_CONFIG, ("homeassistant", "name"), "Serialized House")
    planned = serialize(tree)
    written = flush(tree)

    assert written == (Path(_CONFIG),)
    assert _text(ha_config_tree, _CONFIG) == planned[Path(_CONFIG)]
    for node in tree.files.values():
        if node.rel != Path(_CONFIG):
            assert planned[node.rel] == node.text
