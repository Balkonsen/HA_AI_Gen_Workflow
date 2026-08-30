"""Tests for :mod:`haco.configtree.loader` - the single-file round-trip loader."""

from __future__ import annotations

from pathlib import Path

import pytest
from ruamel.yaml.comments import TaggedScalar

from haco.configtree import load_file


def _tag_str(value: object) -> str:
    """The string form of a ruamel node/value tag (``Tag`` object or plain str)."""
    tag = getattr(value, "tag", None)
    return getattr(tag, "value", None) or str(tag)


def test_load_file_gives_exact_source_span(ha_config_tree: Path) -> None:
    path = ha_config_tree / "configuration.yaml"
    loaded = load_file(path)

    # text is the file's own bytes, decoded UTF-8, with no newline translation
    assert loaded.text == path.read_bytes().decode("utf-8")

    name_span = loaded.spans[("homeassistant", "name")]
    assert loaded.text[name_span.start : name_span.end] == "My Home"

    include_span = loaded.spans[("automation",)]
    assert loaded.text[include_span.start : include_span.end] == "!include automations.yaml"


def test_include_tag_stays_opaque(ha_config_tree: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = ha_config_tree / "configuration.yaml"

    opened: list[Path] = []
    real_read_bytes = Path.read_bytes

    def spy_read_bytes(self: Path) -> bytes:
        opened.append(Path(self))
        return real_read_bytes(self)

    monkeypatch.setattr(Path, "read_bytes", spy_read_bytes)
    loaded = load_file(path)

    value = loaded.data["automation"]
    assert isinstance(value, TaggedScalar)
    assert _tag_str(value) == "!include"

    # D-06: includes are never inlined - no file other than the one asked for is read
    assert opened == [path]
