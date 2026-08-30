"""Tests for :mod:`haco.configtree.graph` and the HA directory-scan rules.

One focused test per rule of ``annotatedyaml._find_files`` (recursion,
``.yaml``-only, dotfile skip, ``secrets.yaml`` skip, per-directory sort), plus
package discovery through the graph and the ``children`` / ``parents`` /
``reachable`` query surface.
"""

from __future__ import annotations

from pathlib import Path

from haco.configtree import find_dir_yaml, load_config_tree


def test_dir_scan_is_recursive(ha_config_tree: Path) -> None:
    tree = load_config_tree(ha_config_tree)

    names = find_dir_yaml(ha_config_tree / "sensors")
    assert (ha_config_tree / "sensors" / "nested" / "c_extra.yaml").resolve() in [p.resolve() for p in names]

    assert "sensors/nested/c_extra.yaml" in {p.as_posix() for p in tree.files}
    assert "sensors/nested/c_extra.yaml" in {e.child.as_posix() for e in tree.graph.edges}


def test_dir_scan_yaml_only(ha_config_tree: Path) -> None:
    tree = load_config_tree(ha_config_tree)

    scanned = {p.name for p in find_dir_yaml(ha_config_tree / "sensors")}
    assert "d_ignored.yml" not in scanned
    assert "sensors/d_ignored.yml" not in {p.as_posix() for p in tree.files}


def test_dir_scan_skips_dotfiles(ha_config_tree: Path) -> None:
    tree = load_config_tree(ha_config_tree)

    scanned = {p.name for p in find_dir_yaml(ha_config_tree / "sensors")}
    assert ".hidden.yaml" not in scanned
    assert "sensors/.hidden.yaml" not in {p.as_posix() for p in tree.files}


def test_dir_scan_skips_secrets_yaml(ha_config_tree: Path) -> None:
    tree = load_config_tree(ha_config_tree)

    scanned = {p.name for p in find_dir_yaml(ha_config_tree / "groups")}
    assert "secrets.yaml" not in scanned
    assert "groups/secrets.yaml" not in {p.as_posix() for p in tree.files}
    assert "groups/secrets.yaml" not in {e.child.as_posix() for e in tree.graph.edges}


def test_dir_scan_sorted_per_directory(ha_config_tree: Path) -> None:
    scanned = find_dir_yaml(ha_config_tree / "scenes")
    assert [p.name for p in scanned] == ["01_evening.yaml", "02_morning.yaml"]


def test_packages_are_discovered(ha_config_tree: Path) -> None:
    tree = load_config_tree(ha_config_tree)

    packages = {p.as_posix() for p in tree.graph.package_files()}
    assert packages == {"packages/climate.yaml", "packages/lighting.yaml"}

    for edge in tree.graph.edges:
        if edge.child.as_posix().startswith("packages/"):
            assert edge.node_path[:2] == ("homeassistant", "packages")


def test_graph_queries_agree_with_edges(ha_config_tree: Path) -> None:
    tree = load_config_tree(ha_config_tree)
    edges = tree.graph.edges

    # children(): exactly the edge children leaving configuration.yaml
    children = set(tree.graph.children(Path("configuration.yaml")))
    assert children == {e.child for e in edges if e.parent == Path("configuration.yaml")}

    # parents(): every reachable non-root file points back at configuration.yaml
    assert tree.graph.parents(Path("automations.yaml")) == (Path("configuration.yaml"),)
    assert tree.graph.parents(Path("packages/lighting.yaml")) == (Path("configuration.yaml"),)

    # reachable(): the same set as the ConfigTree.files keys
    assert tree.graph.reachable() == frozenset(tree.files)

    # absolute paths resolve to the same answer as root-relative ones
    assert set(tree.graph.children(ha_config_tree / "configuration.yaml")) == children
