"""Tests for :mod:`haco.configtree.loader` - the single-file round-trip loader."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from ruamel.yaml.comments import CommentedMap, CommentedSeq, TaggedScalar

from haco.configtree import (
    DuplicateKeyError,
    MultiDocumentError,
    load_file,
    make_yaml,
)

_FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "ha_config"
_YAML_FIXTURES = sorted(p.relative_to(_FIXTURE_ROOT).as_posix() for p in _FIXTURE_ROOT.rglob("*.yaml"))

_D08_TAGS = [
    "!include",
    "!include_dir_list",
    "!include_dir_merge_list",
    "!include_dir_named",
    "!include_dir_merge_named",
    "!secret",
    "!env_var",
    "!input",
]

_OPAQUE_TYPES = (TaggedScalar, CommentedMap, CommentedSeq)


def _tag_str(value: object) -> str | None:
    tag = getattr(value, "tag", None)
    if tag is None:
        return None
    resolved = getattr(tag, "value", tag)
    return resolved if isinstance(resolved, str) else None


def _tagged_values(data: object) -> list[tuple[str, object]]:
    """Every ``(tag, value)`` pair carrying an explicit ``!`` tag, depth-first."""
    found: list[tuple[str, object]] = []

    def visit(obj: object) -> None:
        tag = _tag_str(obj)
        if tag is not None and tag.startswith("!"):
            found.append((tag, obj))
        if isinstance(obj, dict):
            for item in obj.values():
                visit(item)
        elif isinstance(obj, list):
            for item in obj:
                visit(item)

    visit(data)
    return found


def _dedent2(text: str) -> str:
    return "\n".join(line[2:] if line.startswith("  ") else line for line in text.split("\n"))


def test_load_file_gives_exact_source_span(ha_config_tree: Path) -> None:
    path = ha_config_tree / "configuration.yaml"
    loaded = load_file(path)

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


@pytest.mark.parametrize("tag", _D08_TAGS)
def test_known_ha_tags_parse(ha_config_tree: Path, tag: str) -> None:
    fixture = "blueprints/automation/example.yaml" if tag == "!input" else "configuration.yaml"
    loaded = load_file(ha_config_tree / fixture)

    tagged = [value for found_tag, value in _tagged_values(loaded.data) if found_tag == tag]
    assert tagged, f"{tag} not present in {fixture}"
    assert all(isinstance(value, _OPAQUE_TYPES) for value in tagged)
    # a known tag is never reported as unknown and never warns
    assert tag not in loaded.unknown_tags


def test_input_tag_parses_in_scalar_and_mapping_form(ha_config_tree: Path) -> None:
    loaded = load_file(ha_config_tree / "blueprints" / "automation" / "example.yaml")
    scalar_form = loaded.data["trigger"][0]["entity_id"]
    mapping_form = loaded.data["action"][0]["target"]
    assert isinstance(scalar_form, TaggedScalar)
    assert isinstance(mapping_form, CommentedMap)
    assert _tag_str(scalar_form) == "!input"
    assert _tag_str(mapping_form) == "!input"


def test_unknown_tag_round_trips_and_warns_once(ha_config_tree: Path) -> None:
    with pytest.warns(UserWarning) as record:
        loaded = load_file(ha_config_tree / "configuration.yaml")

    greet = loaded.data["shell_command"]["greet"]
    assert isinstance(greet, TaggedScalar)  # inert, not a constructed Python object
    assert _tag_str(greet) == "!custom_tag"

    custom_warnings = [w for w in record if "!custom_tag" in str(w.message)]
    assert len(custom_warnings) == 1
    assert loaded.unknown_tags == frozenset({"!custom_tag"})


@pytest.mark.parametrize("rel", _YAML_FIXTURES)
def test_roundtrip_diagnostic_is_byte_identical(rel: str) -> None:
    """ruamel-drift canary for YAML-02: ``load`` then ``dump`` with the pinned indent.

    Mapping-root files must reproduce byte for byte. For a file whose document
    root is a block *sequence*, ruamel's ``offset=2`` unavoidably indents the
    whole root list by two columns; that single, uniform shift is removed before
    comparing so the canary still fires on any real emitter drift.
    """
    path = _FIXTURE_ROOT / rel
    text = path.read_bytes().decode("utf-8")
    yaml = make_yaml()
    data = yaml.load(text)
    buf = io.StringIO()
    yaml.dump(data, buf)
    dumped = buf.getvalue()

    if isinstance(data, list):
        assert _dedent2(dumped) == text
    else:
        assert dumped == text


def test_duplicate_key_raises(ha_config_bad: Path) -> None:
    with pytest.raises(DuplicateKeyError) as excinfo:
        load_file(ha_config_bad / "dupkey" / "configuration.yaml")
    assert "configuration.yaml" in str(excinfo.value)


def test_multi_document_raises(ha_config_bad: Path) -> None:
    with pytest.raises(MultiDocumentError) as excinfo:
        load_file(ha_config_bad / "multidoc" / "configuration.yaml")
    assert "configuration.yaml" in str(excinfo.value)


def test_encoding_probe_has_bom_and_crlf(ha_config_tree: Path) -> None:
    raw = (ha_config_tree / "encoding" / "crlf_bom.yaml").read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" in raw
