"""Exception hierarchy for haco.

All messages are human-readable and MUST NOT contain secret values
(passwords, key bytes, tokens). Later plans extend this family; this module
defines the base error, the profile-related errors, and the connection /
remote-command errors used by the SSH layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


class HacoError(Exception):
    """Base class for every error raised by haco."""


class ProfileError(HacoError):
    """A host profile could not be read, written, or validated."""


class ProfileNotFound(ProfileError):
    """No stored profile exists for the requested name."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"No profile named {name!r}. Run 'haco profile add {name} ...' to create one.")


class ConnectionError(HacoError):
    """An SSH connection to the Home Assistant host could not be established.

    Deliberately shadows the builtin ``ConnectionError`` within haco so callers
    can catch a single ``haco.errors`` hierarchy.
    """


class AuthError(ConnectionError):
    """SSH authentication failed: bad key, wrong password, or no credentials available.

    The message never contains the attempted password or any key material.
    """


class HostKeyError(ConnectionError):
    """The SSH server host key could not be verified against the known_hosts file."""


class RemoteCommandError(HacoError):
    """A remote command exited non-zero when a zero exit was required.

    Carries the command and a short tail of stderr - never stdin or secrets.
    """


class DiscoveryError(HacoError):
    """The Home Assistant install type or config directory could not be resolved.

    Raised when autodetection is inconclusive and the profile does not supply
    the missing piece (``install_type``, ``container_name``, or ``config_dir``).
    The message names the override that would unblock discovery.
    """


class CheckError(HacoError):
    """The baseline config-check command could not be executed at all.

    Distinct from a check that *ran* and reported problems: that outcome is
    returned as data (:class:`haco.check.CheckResult` with ``ok=False``), never
    raised. Reserved for callers that need a hard failure signal; the connect
    flow does not raise it.
    """


class PreflightError(HacoError):
    """A permission preflight probe could not be run.

    As with :class:`CheckError`, a preflight that runs and finds a missing grant
    is returned as data (:class:`haco.preflight.PreflightResult` with
    ``ok=False``), not raised.
    """


class ConfigTreeError(HacoError):
    """Assembling, mutating, or writing back the config tree failed.

    Raised for structural problems found *after* a file parses: a node whose
    source byte range cannot be resolved unambiguously, a value reached through
    a YAML alias that cannot be spliced in place, or a write-back that would
    have to fall back to a whole-file dump. The message never contains secret
    material; a ``!secret`` argument is a key name, not a value, and is still
    not echoed above DEBUG.
    """


class UnspliceableNodeError(ConfigTreeError):
    """A node cannot be rewritten by surgical text splice, so nothing is written.

    This is CONTEXT.md D-03's fail-loud contract. A node is unspliceable when its
    source byte range cannot be resolved unambiguously: the path has no span at
    all, the value was reached through a YAML alias or ``<<`` merge (its span
    points at the anchor, not the alias), or the span covers a whole block
    collection rather than a single scalar. There is deliberately **no** fallback
    to re-emitting the whole file - a silent whole-file reformat is exactly what
    the splice writer exists to avoid. The message names the file, the node path
    and the reason; a ``!secret`` argument is a key name, never a value, and is
    still not echoed above DEBUG.
    """

    def __init__(self, file: Path | str, node_path: tuple[str | int, ...], reason: str) -> None:
        self.file = file
        self.node_path = tuple(node_path)
        self.reason = reason
        super().__init__(f"{file}: cannot splice node {self.node_path!r}: {reason}")


class YamlError(HacoError):
    """A single YAML file could not be parsed into an editable tree.

    Carries the offending file path and, where useful, the key or marker that
    triggered the failure. A ``!secret`` argument is a key *name*, never a
    value, and is still not to be echoed above DEBUG; no message in this family
    includes one.
    """


class DuplicateKeyError(YamlError):
    """A mapping key appears twice in one file.

    Home Assistant's own loader rejects duplicate keys; so do we, rather than
    silently keeping the last one. The message names the file and, when it can
    be recovered from the parser, the offending key.
    """

    def __init__(self, path: Path, key: str | None = None) -> None:
        self.path = path
        self.key = key
        detail = f" (key {key!r})" if key is not None else ""
        super().__init__(f"{path} contains a duplicate mapping key{detail}")


class MultiDocumentError(YamlError):
    """The file carries more than one YAML document (a second ``---``).

    Home Assistant config files are single-document; a trailing document is
    almost always a mistake, so it is refused rather than silently dropped.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"{path} contains more than one YAML document; expected a single document")


class IncludeError(ConfigTreeError):
    """An ``!include`` / ``!include_dir_*`` reference could not be honoured.

    The message names the *including* file, the include tag, and the include
    argument (a relative path or directory). ``!secret`` is not an include tag
    and is never followed, so no message in this family carries a secret key.
    """


class IncludeCycleError(IncludeError):
    """The include walk revisited a file already on the loading stack.

    Home Assistant's own loader has no cycle guard and dies with a bare
    :class:`RecursionError`; this fails cleanly instead. The message lists the
    files in the cycle in walk order.
    """

    def __init__(self, cycle: Sequence[Path]) -> None:
        self.cycle = tuple(cycle)
        rendered = " -> ".join(str(p) for p in self.cycle)
        super().__init__(f"include cycle detected: {rendered}")


class IncludeEscapeError(IncludeError):
    """A resolved include target lies outside the config root.

    ASVS V12: an include argument is an untrusted string. A target that
    resolves - via ``..`` or a symlink - outside the pulled config root is
    refused here and never loaded as an editable node, nor is its directory
    handed to ``os.walk``.
    """

    def __init__(self, parent: Path, argument: str, resolved: Path, root: Path) -> None:
        self.parent = parent
        self.argument = argument
        self.resolved = resolved
        self.root = root
        super().__init__(
            f"{parent}: include target {argument!r} resolves to {resolved}, outside the config root {root}"
        )


class MissingIncludeError(IncludeError):
    """A resolved include target does not exist on disk.

    An include that resolves to nothing is a config bug the user needs told
    about, not a silently empty node. The message names the parent file and
    the unresolved argument.
    """

    def __init__(self, parent: Path, argument: str, resolved: Path) -> None:
        self.parent = parent
        self.argument = argument
        self.resolved = resolved
        super().__init__(f"{parent}: include target {argument!r} not found (looked for {resolved})")
