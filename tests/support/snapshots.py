"""Filesystem snapshot helper shared across the config-tree test suite.

:func:`snapshot_tree` captures every file under a directory as ``(bytes, mtime)``
so a test can assert, after some engine operation, that untouched files are
byte-identical *and* were not rewritten with identical content (an mtime move).
It lives here - not in a single test module - so the writer tests and the
idempotency tests use exactly one implementation.
"""

from __future__ import annotations

from pathlib import Path

__all__ = ["snapshot_tree"]


def snapshot_tree(root: Path) -> dict[Path, tuple[bytes, int]]:
    """Map every file under ``root`` to its raw bytes and mtime in nanoseconds."""
    out: dict[Path, tuple[bytes, int]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            stat = path.stat()
            out[path] = (path.read_bytes(), stat.st_mtime_ns)
    return out
