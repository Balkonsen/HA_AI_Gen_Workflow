"""Exception hierarchy for haco.

All messages are human-readable and MUST NOT contain secret values
(passwords, key bytes, tokens). Later plans extend this family; this module
defines the base error, the profile-related errors, and the connection /
remote-command errors used by the SSH layer.
"""

from __future__ import annotations


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


class YamlError(HacoError):
    """A single YAML file could not be parsed into an editable tree.

    Carries the offending file path and, where useful, the key or marker that
    triggered the failure. A ``!secret`` argument is a key *name*, never a
    value, and is still not to be echoed above DEBUG; no message in this family
    includes one.
    """
