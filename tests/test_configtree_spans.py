"""Tests for :mod:`haco.configtree.spans` - per-style span kinds and alias guarding."""

from __future__ import annotations

from pathlib import Path

import pytest

from haco.configtree.loader import make_yaml
from haco.configtree.spans import NodePath, Span, SpanKind, build_span_index

_GOLDEN = Path(__file__).parent / "fixtures" / "spans_golden.yaml"


def _index(path: Path) -> tuple[str, dict[NodePath, Span]]:
    text = path.read_bytes().decode("utf-8")
    root = make_yaml().compose(text)
    return text, build_span_index(root, path)


# (path, expected kind, expected exact source slice)
_KIND_CASES: list[tuple[NodePath, SpanKind, str]] = [
    (("name",), "plain", "Home"),
    (("num",), "plain", "42"),
    (("quoted",), "double", '"Quoted Name"'),
    (("single",), "single", "'single'"),
    (("block",), "literal", "|\n  line one\n  line two\n"),
    (("folded",), "folded", ">\n  wrapped\n  text\n"),
    (("flow",), "flow", "[a, b, c]"),
    (("tagged",), "tagged", "!include child.yaml"),
]


@pytest.mark.parametrize(("node_path", "kind", "slice_text"), _KIND_CASES)
def test_span_kinds_and_text(node_path: NodePath, kind: SpanKind, slice_text: str) -> None:
    text, index = _index(_GOLDEN)
    span = index[node_path]
    assert span.kind == kind
    assert text[span.start : span.end] == slice_text


def test_alias_path_is_unspliceable(ha_config_tree: Path) -> None:
    _text, index = _index(ha_config_tree / "configuration.yaml")

    anchor_span = index[("script", "wakeup")]
    alias_span = index[("script", "other")]

    assert anchor_span.unspliceable is None
    assert alias_span.unspliceable is not None
    assert "wakeup_script" in alias_span.unspliceable


# Frozen offset table for tests/fixtures/spans_golden.yaml, produced once by running
# build_span_index() over the committed file. A mismatch here means ruamel's
# compose() offset behaviour drifted (or .gitattributes stopped pinning the fixture
# bytes): re-examine the `ruamel.yaml>=0.19.1,<0.20` pin BEFORE changing anything else.
_GOLDEN_OFFSETS: dict[NodePath, tuple[int, int]] = {
    (): (0, 181),
    ("name",): (6, 10),
    ("num",): (16, 18),
    ("quoted",): (48, 61),
    ("single",): (70, 78),
    ("block",): (86, 110),
    ("folded",): (118, 137),
    ("flow",): (143, 152),
    ("flow", 0): (144, 145),
    ("flow", 1): (147, 148),
    ("flow", 2): (150, 151),
    ("tagged",): (161, 180),
}


def test_golden_offsets_match_table() -> None:
    _text, index = _index(_GOLDEN)
    actual = {path: (span.start, span.end) for path, span in index.items()}
    assert actual == _GOLDEN_OFFSETS
