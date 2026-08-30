"""The include graph - a byproduct of the load walk (YAML-03, CONTEXT.md D-05).

An edge records ``parent file --(tag at node_path)--> child file``, with the
``!include_dir_*`` variants expanded to one edge per matched ``.yaml`` file.
Both frozen dataclasses stay hashable in the Phase 1 result-type style:
:class:`IncludeGraph` stores its edges and files as tuples.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from haco.configtree.spans import NodePath

_HOMEASSISTANT_KEY = "homeassistant"
_PACKAGES_KEY = "packages"
_ENTRYPOINT = Path("configuration.yaml")


@dataclass(frozen=True)
class IncludeEdge:
    """One resolved include reference.

    ``parent`` and ``child`` are paths relative to the config root, so graph
    assertions read cleanly and are portable across checkouts. ``node_path`` is
    where in ``parent`` the include tag sits.
    """

    parent: Path
    node_path: NodePath
    tag: str
    child: Path


@dataclass(frozen=True)
class IncludeGraph:
    """Every include edge discovered by the load walk, plus every reachable file."""

    root: Path
    edges: tuple[IncludeEdge, ...]
    files: tuple[Path, ...]

    def children(self, parent: Path) -> tuple[Path, ...]:
        """Root-relative child paths of every edge leaving ``parent`` (abs or rel)."""
        key = self._relative(parent)
        return tuple(edge.child for edge in self.edges if edge.parent == key)

    def parents(self, child: Path) -> tuple[Path, ...]:
        """Root-relative parent paths of every edge entering ``child`` (abs or rel)."""
        key = self._relative(child)
        return tuple(edge.parent for edge in self.edges if edge.child == key)

    def reachable(self) -> frozenset[Path]:
        """Every file reachable from ``configuration.yaml`` by following edges.

        Equals the :attr:`ConfigTree.files` key set - the load walk and the edge
        set are the same walk.
        """
        seen: set[Path] = set()
        frontier: list[Path] = [_ENTRYPOINT]
        while frontier:
            current = frontier.pop()
            if current in seen:
                continue
            seen.add(current)
            frontier.extend(edge.child for edge in self.edges if edge.parent == current)
        return frozenset(seen)

    def package_files(self) -> tuple[Path, ...]:
        """Child paths of every edge whose ``node_path`` is under ``homeassistant: -> packages:``.

        Selected by node path, not by tag, so it works whether ``packages:`` is
        written ``!include_dir_named packages/`` or as an explicit mapping of
        single-file ``!include`` tags.
        """
        return tuple(edge.child for edge in self.edges if edge.node_path[:2] == (_HOMEASSISTANT_KEY, _PACKAGES_KEY))

    def _relative(self, path: Path) -> Path:
        if path.is_absolute():
            return path.resolve().relative_to(self.root.resolve())
        return path


__all__ = ["IncludeEdge", "IncludeGraph"]
