from enum import Enum
from typing import TYPE_CHECKING, overload

import polib

if TYPE_CHECKING:

    @overload
    def _(message: str) -> str: ...  # pyright: ignore[reportInconsistentOverload, reportNoOverloadImplementation]


class POFileEntryTag(str, Enum):
    """Enumeration of possible tags for PO file entries."""

    UNKNOWN = _("unknown")  # Default tag when no known tag is found
    FUZZY = _("fuzzy")  # Indicates that the entry is fuzzy (translation may be inaccurate)
    UNCONFIRMED = _("unconfirmed")  # Optional replacement for "fuzzy" to indicate unconfirmed translation
    REVIEWED = _("reviewed")  # Indicates that the entry has been reviewed

    def apply(self, entry: polib.POEntry):
        """Apply this tag to the given PO entry, removing any other known tags.

        Args:
            entry (polib.POEntry): The PO entry to modify.
        """
        entry.flags = [
            flag for flag in (entry.flags or []) if flag not in tuple(member.value for member in self.__class__)
        ]
        entry.flags.append(self.value)

    @classmethod
    def fish(cls, entry: polib.POEntry, default: "POFileEntryTag") -> "POFileEntryTag":
        """Return the first matching tag from the entry's flags, or the default if none match.

        Args:
            entry (polib.POEntry): The PO entry to check.
            default (POFileEntryTags): The default tag to return if no match is found.

        Returns:
            POFileEntryTag: The matching tag or the default.
        """
        for flag in entry.flags or []:
            for member in cls:
                if flag == member.value:
                    return member

        return default
