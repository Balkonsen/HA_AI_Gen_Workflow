"""Exception hierarchy for haco.

All messages are human-readable and MUST NOT contain secret values
(passwords, key bytes, tokens). Later plans extend this family; this module
only defines the base error and the profile-related errors.
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
