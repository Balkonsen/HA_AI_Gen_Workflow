"""Tests for :mod:`haco.configtree.tree` / :mod:`haco.configtree.includes`.

End-to-end tracer: one walk from ``configuration.yaml`` reaches every
transitively included file and loads each as its own editable node, and the
include graph carries one edge per resolved target. The three include failure
modes (cycle, missing target, containment escape) each raise their own typed
``ConfigTreeError`` subclass naming the offending file.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest

from haco.configtree import load_config_tree, resolve_include_targets
from haco.configtree.tree import FileNode
from haco.errors import (
    ConfigTreeError,
    IncludeCycleError,
    IncludeEscapeError,
    MissingIncludeError,
)

# The exact set of root-relative paths reachable from configuration.yaml in the
# tests/fixtures/ha_config tree. configuration.yaml itself, one !include each for
# automations.yaml and encoding/crlf_bom.yaml, the recursive sensors/ scan (three
# files incl. the nested one), the two scenes/ files, the one non-secret groups/
# file, the one templates/ file, and both packages/ files discovered through
# homeassistant: -> packages: !include_dir_named.
_EXPECTED_FILES = {
    "configuration.yaml",
    "automations.yaml",
    "encoding/crlf_bom.yaml",
    "sensors/a_power.yaml",
    "sensors/b_energy.yaml",
    "sensors/nested/c_extra.yaml",
    "scenes/01_evening.yaml",
    "scenes/02_morning.yaml",
    "groups/living.yaml",
    "templates/weather.yaml",
    "packages/climate.yaml",
    "packages/lighting.yaml",
}

# Present in the fixture directory but must NOT become nodes.
_EXCLUDED_FILES = {
    "sensors/.hidden.yaml",  # dotfile
    "sensors/d_ignored.yml",  # .yml, not .yaml
    "groups/secrets.yaml",  # SECRET_YAML basename
    "blueprints/automation/example.yaml",  # not referenced from configuration.yaml
}


def _keys(tree_files: Mapping[Path, FileNode]) -> set[str]:
    return {p.as_posix() for p in tree_files}


def test_load_config_tree_reaches_every_file(ha_config_tree: Path) -> None:
    tree = load_config_tree(ha_config_tree)

    assert _keys(tree.files) == _EXPECTED_FILES
    assert _EXCLUDED_FILES.isdisjoint(_keys(tree.files))
    # the nested-subdirectory file proves the directory scan recurses
    assert "sensors/nested/c_extra.yaml" in _keys(tree.files)


def test_every_file_node_is_editable(ha_config_tree: Path) -> None:
    tree = load_config_tree(ha_config_tree)

    for node in tree.files.values():
        assert node.text, f"{node.rel} has empty text"
        assert len(node.spans) > 0, f"{node.rel} has an empty span index"
        assert node.path.is_absolute()
        assert not node.dirty


def test_include_graph_has_one_edge_per_resolved_target(ha_config_tree: Path) -> None:
    tree = load_config_tree(ha_config_tree)
    edges = tree.graph.edges

    # every edge in this fixture originates at configuration.yaml
    assert {e.parent.as_posix() for e in edges} == {"configuration.yaml"}
    # one edge per reachable file other than the entrypoint, no duplicates
    child_paths = [e.child.as_posix() for e in edges]
    assert sorted(child_paths) == sorted(_EXPECTED_FILES - {"configuration.yaml"})
    assert len(child_paths) == len(set(child_paths))

    by_child = {e.child.as_posix(): e for e in edges}
    assert by_child["automations.yaml"].tag == "!include"
    assert by_child["automations.yaml"].node_path == ("automation",)
    assert by_child["sensors/nested/c_extra.yaml"].tag == "!include_dir_merge_list"
    assert by_child["packages/climate.yaml"].node_path == ("homeassistant", "packages")


def test_include_cycle_raises_configtree_error(ha_config_bad: Path) -> None:
    with pytest.raises(IncludeCycleError) as excinfo:
        load_config_tree(ha_config_bad / "cycle")

    exc = excinfo.value
    # a typed ConfigTreeError, never the bare RecursionError HA dies with
    assert isinstance(exc, ConfigTreeError)
    assert not isinstance(exc, RecursionError)
    # the message names the files in the cycle, in walk order
    message = str(exc)
    assert "ring_a.yaml" in message
    assert "ring_b.yaml" in message
    assert [p.name for p in exc.cycle] == ["ring_a.yaml", "ring_b.yaml", "ring_a.yaml"]


def test_missing_include_target_raises(ha_config_bad: Path) -> None:
    with pytest.raises(MissingIncludeError) as excinfo:
        load_config_tree(ha_config_bad / "missing")

    exc = excinfo.value
    assert isinstance(exc, ConfigTreeError)
    # the message names both the parent file and the unresolved argument
    assert exc.argument == "nowhere.yaml"
    message = str(exc)
    assert "nowhere.yaml" in message
    assert "configuration.yaml" in message


def test_include_outside_root_is_refused(ha_config_bad: Path) -> None:
    # the escape subtree is loaded with its own directory as the config root, so
    # `!include ../escape_target.yaml` resolves one level above it
    with pytest.raises(IncludeEscapeError) as excinfo:
        load_config_tree(ha_config_bad / "escape")

    exc = excinfo.value
    assert isinstance(exc, ConfigTreeError)
    # containment is checked before the target is ever opened: a sibling
    # MissingIncludeError would mean the file was stat-ed first
    assert not isinstance(exc, MissingIncludeError)
    assert exc.resolved.name == "escape_target.yaml"
    assert (ha_config_bad / "escape") not in exc.resolved.parents


def test_dir_include_outside_root_refused_before_walk(ha_config_bad: Path) -> None:
    # a directory-variant argument that climbs out of the root is refused by the
    # containment check before os.walk is allowed to enumerate anything
    root = ha_config_bad / "escape"
    parent = root / "configuration.yaml"
    with pytest.raises(IncludeEscapeError):
        resolve_include_targets(parent, "!include_dir_merge_list", "..", root)
