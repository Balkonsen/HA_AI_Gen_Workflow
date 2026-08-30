"""D-10 no-op stability: the engine is a fixed point over an unedited tree.

Requirement YAML-05 asks that re-running analysis on an already-optimised tree
proposes zero changes. No analysis engine exists in Phase 2, so CONTEXT.md D-10
asserts the property one level down, at the engine itself, as three no-op
stability properties exercised against the whole representative fixture tree
(``tests/fixtures/ha_config/``) rather than a single toy file:

1. ``load -> serialize -> load -> serialize`` is a per-file fixed point - the
   second serialisation equals the first, byte for byte, for every file
   (:func:`test_serialize_is_fixed_point`).
2. Flushing with no ``set`` call writes zero files and moves no mtime
   (:func:`test_empty_changeset_zero_writes`).
3. Mutating a node and then setting it back to its exact original source text
   leaves every file byte-identical to the pre-mutation snapshot, across a
   plain, a single-quoted, a double-quoted and a literal-block scalar
   (:func:`test_apply_then_revert_is_byte_identical`).

Every test runs against the ``ha_config_tree`` conftest fixture, which is a
throwaway ``tmp_path`` copy - the committed fixture bytes are never touched.
"""

from __future__ import annotations

from pathlib import Path

from haco.configtree import load_config_tree, serialize

# Every file reachable from configuration.yaml in tests/fixtures/ha_config/.
# The fixed-point harness must visit all of them; a harness that silently walked
# a subset would still report a green fixed point, which is the failure mode
# D-10.1's coverage guard exists to catch.
_REACHABLE_FIXTURE_FILES = {
    "automations.yaml",
    "configuration.yaml",
    "encoding/crlf_bom.yaml",
    "groups/living.yaml",
    "packages/climate.yaml",
    "packages/lighting.yaml",
    "scenes/01_evening.yaml",
    "scenes/02_morning.yaml",
    "sensors/a_power.yaml",
    "sensors/b_energy.yaml",
    "sensors/nested/c_extra.yaml",
    "templates/weather.yaml",
}


def _write_tree(dest: Path, files: dict[Path, str]) -> None:
    """Write ``files`` (root-relative path -> text) under ``dest``, layout preserved.

    ``newline=""`` and ``encoding="utf-8"`` so the round trip launders neither
    line endings nor a leading BOM - the encoding probe carries both.
    """
    for rel, text in files.items():
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="") as handle:
            handle.write(text)


# --------------------------------------------------------------------------- #
# D-10.1 - load -> serialize -> load -> serialize is a per-file fixed point
# --------------------------------------------------------------------------- #


def test_serialize_is_fixed_point(ha_config_tree: Path, tmp_path: Path) -> None:
    first = serialize(load_config_tree(ha_config_tree))

    second_root = tmp_path / "round_trip"
    _write_tree(second_root, first)
    second = serialize(load_config_tree(second_root))

    assert set(second) == set(first), "the second load reached a different set of files"
    for rel in sorted(first, key=lambda path: path.as_posix()):
        assert second[rel] == first[rel], f"{rel.as_posix()} drifted on the second serialization"


def test_fixed_point_covers_every_fixture_file(ha_config_tree: Path) -> None:
    tree = load_config_tree(ha_config_tree)
    serialized = serialize(tree)

    # the harness serialised exactly the files it loaded - no subset, no extras
    assert set(serialized) == set(tree.files)

    posix_keys = {rel.as_posix() for rel in serialized}
    assert posix_keys == _REACHABLE_FIXTURE_FILES
    assert len(posix_keys) >= 11
    assert "encoding/crlf_bom.yaml" in posix_keys, "the BOM + CRLF probe file was not visited"
