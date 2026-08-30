"""Tests for :mod:`haco.configtree.tree` / :mod:`haco.configtree.includes`.

End-to-end tracer: one walk from ``configuration.yaml`` reaches every
transitively included file and loads each as its own editable node, and the
include graph carries one edge per resolved target. The three include failure
modes (cycle, missing target, containment escape) are added in Task 3.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from haco.configtree import load_config_tree
from haco.configtree.tree import FileNode

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
