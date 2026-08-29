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
