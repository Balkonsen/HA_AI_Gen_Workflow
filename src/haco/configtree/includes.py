"""Home-Assistant-faithful ``!include`` / ``!include_dir_*`` resolution.

Re-implements ``annotatedyaml._find_files`` and the include path-join rule from
Home Assistant's own loader (see ``02-RESEARCH.md`` -> "HA ``!include*`` /
``packages:`` Semantics - Pinned from Source"):

* the include argument is joined onto the *including file's* directory, not the
  config root (``os.path.join(os.path.dirname(loader.get_name), node.value)``);
* the directory scan is ``os.walk`` - recursive, ``topdown=True``, symlink
  following left at its default ``False`` - keeps only ``*.yaml`` (``.yml`` is
  deliberately not matched by the directory variants), drops dot-names, and
  skips any basename equal to :data:`SECRET_YAML`.

Every resolved target - a single file *and* a directory before it is walked - is
run through :func:`ensure_contained` first: an untrusted include argument must
never enumerate or load a file outside the pulled config root (ASVS V12,
``02-RESEARCH.md`` Pitfall 9). This is in the resolution path from the first
commit, not bolted on, because everything downstream treats a node in the tree
as trusted and editable.
"""

from __future__ import annotations

import fnmatch
import os
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any, Final

from haco.configtree.spans import NodePath
from haco.errors import IncludeEscapeError, MissingIncludeError

SECRET_YAML: Final[str] = "secrets.yaml"
"""The basename Home Assistant's directory helpers skip inside every scan."""

INCLUDE_FILE_TAG: Final[str] = "!include"
INCLUDE_DIR_TAGS: Final[frozenset[str]] = frozenset(
    {
        "!include_dir_list",
        "!include_dir_merge_list",
        "!include_dir_named",
        "!include_dir_merge_named",
    }
)
INCLUDE_TAGS: Final[frozenset[str]] = INCLUDE_DIR_TAGS | {INCLUDE_FILE_TAG}
"""The five include tags: the four ``!include_dir_*`` variants plus ``!include``."""


def _is_valid_name(name: str) -> bool:
    """HA's ``_is_file_valid``: a name is valid unless it starts with a dot."""
    return not name.startswith(".")


def find_dir_yaml(directory: Path) -> list[Path]:
    """Recursively list ``*.yaml`` files under ``directory``, Home-Assistant-faithfully.

    Mirrors ``annotatedyaml._find_files``: ``os.walk(topdown=True)`` with symlink
    following left at its default (``followlinks=False``), dot-directories
    filtered from the descent, ``sorted(files)`` per directory, the ``"*.yaml"``
    glob only, and any basename equal to :data:`SECRET_YAML` skipped. The
    assembled list is then sorted as a whole so cross-directory order is
    deterministic - HA guarantees only the per-directory order, so a total sort
    is stricter than HA rather than divergent (``02-RESEARCH.md`` assumption A5).
    """
    out: list[Path] = []
    for root, dirs, files in os.walk(directory, topdown=True):
        dirs[:] = sorted(d for d in dirs if _is_valid_name(d))
        for name in sorted(files):
            if not _is_valid_name(name) or not fnmatch.fnmatch(name, "*.yaml"):
                continue
            if name == SECRET_YAML:
                continue
            out.append(Path(root) / name)
    return sorted(out)


def _tag_string(node: Any) -> str | None:
    """The string form of a node's YAML tag, or ``None`` if it carries no ``!`` tag."""
    tag = getattr(node, "tag", None)
    if tag is None:
        return None
    value = getattr(tag, "value", tag)
    return value if isinstance(value, str) else None


def iter_include_refs(data: Any) -> Iterator[tuple[NodePath, str, str]]:
    """Yield ``(node_path, tag, argument)`` for every include reference in ``data``.

    Walks the round-trip tree. A node whose tag is in :data:`INCLUDE_TAGS` is an
    include reference; ``argument`` is that tagged scalar's own value string (the
    relative path or directory Home Assistant would resolve). ``!secret``,
    ``!env_var`` and ``!input`` are not include tags and are skipped, so a
    ``!secret`` key name is never yielded.
    """
    seen: set[int] = set()

    def walk(node: Any, path: NodePath) -> Iterator[tuple[NodePath, str, str]]:
        tag = _tag_string(node)
        if tag in INCLUDE_TAGS:
            yield path, str(tag), str(getattr(node, "value", ""))
            return
        if isinstance(node, Mapping):
            if id(node) in seen:
                return
            seen.add(id(node))
            for key, value in node.items():
                yield from walk(value, (*path, str(key)))
        elif isinstance(node, list):
            if id(node) in seen:
                return
            seen.add(id(node))
            for index, value in enumerate(node):
                yield from walk(value, (*path, index))

    yield from walk(data, ())


def ensure_contained(
    candidate: Path,
    root: Path,
    *,
    parent: Path | None = None,
    argument: str | None = None,
) -> Path:
    """Resolve ``candidate`` and assert it stays within ``root``; return the resolved path.

    Raises :class:`haco.errors.IncludeEscapeError` - naming ``parent`` and
    ``argument`` when supplied, never a secret - if the resolved candidate is
    neither ``root`` itself nor a descendant of it. Applied to single-file
    targets and to the directory argument of a ``!include_dir_*`` before
    ``os.walk`` is allowed to run on it (ASVS V12, ``02-RESEARCH.md`` Pitfall 9).
    """
    resolved_root = root.resolve()
    resolved = candidate.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise IncludeEscapeError(
            parent if parent is not None else candidate,
            argument if argument is not None else str(candidate),
            resolved,
            resolved_root,
        )
    return resolved


def resolve_include_targets(parent: Path, tag: str, argument: str, root: Path) -> list[Path]:
    """Resolve one include reference to the list of target files it names.

    ``argument`` is joined onto the *including file's* directory (HA resolves
    relative to ``loader.get_name``, not the config root), the join is checked
    for containment, then:

    * ``!include`` -> a one-element list ``[target]``; a target file that does
      not exist raises :class:`haco.errors.MissingIncludeError`.
    * ``!include_dir_*`` -> :func:`find_dir_yaml` of the resolved directory; a
      directory that does not exist raises the same error rather than silently
      yielding an empty list.
    """
    base = parent.parent
    if not argument.strip():
        raise MissingIncludeError(parent, argument, base)
    joined = base / argument
    if tag == INCLUDE_FILE_TAG:
        target = ensure_contained(joined, root, parent=parent, argument=argument)
        if not target.is_file():
            raise MissingIncludeError(parent, argument, target)
        return [target]
    target_dir = ensure_contained(joined, root, parent=parent, argument=argument)
    if not target_dir.is_dir():
        raise MissingIncludeError(parent, argument, target_dir)
    return find_dir_yaml(target_dir)


__all__ = [
    "INCLUDE_DIR_TAGS",
    "INCLUDE_FILE_TAG",
    "INCLUDE_TAGS",
    "SECRET_YAML",
    "ensure_contained",
    "find_dir_yaml",
    "iter_include_refs",
    "resolve_include_targets",
]
