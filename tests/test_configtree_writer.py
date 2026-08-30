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

from haco.configtree import atomic_write, flush, load_config_tree, splice

_CONFIG = "configuration.yaml"


def _snapshot(root: Path) -> dict[Path, tuple[bytes, int]]:
    """Every file under ``root`` mapped to its raw bytes and mtime in nanoseconds."""
    out: dict[Path, tuple[bytes, int]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            stat = path.stat()
            out[path] = (path.read_bytes(), stat.st_mtime_ns)
    return out


def _text(root: Path, rel: str) -> str:
    return (root / rel).read_bytes().decode("utf-8")


# --------------------------------------------------------------------------- #
# Task 1: end-to-end tracer - edit one value, rewrite one file, touch one span
# --------------------------------------------------------------------------- #


def test_dirty_only_one_file_rewritten(ha_config_tree: Path) -> None:
    original = _snapshot(ha_config_tree)
    tree = load_config_tree(ha_config_tree)

    tree.set(_CONFIG, ("homeassistant", "name"), "My House")
    written = flush(tree)

    assert written == (Path(_CONFIG),)

    new_config = _text(ha_config_tree, _CONFIG)
    assert "name: My House" in new_config
    assert "My Home" not in new_config

    after = _snapshot(ha_config_tree)
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
    before = _snapshot(ha_config_tree)

    tree.set(_CONFIG, ("homeassistant", "name"), "My House")

    assert _snapshot(ha_config_tree) == before
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
    before = _snapshot(ha_config_tree)
    tree = load_config_tree(ha_config_tree)

    assert flush(tree) == ()
    assert _snapshot(ha_config_tree) == before
