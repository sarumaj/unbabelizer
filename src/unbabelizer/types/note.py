import re

import polib


class Note(str):
    note_pattern: str = r'<note class="unbabelizer">(.+?)</note>'
    fstring_template = '<note class="unbabelizer">{note}</note>'

    @classmethod
    def parse_entry(cls, entry: polib.POEntry) -> "Note":
        """Extract note from the PO entry's translator comments.

        Args:
            entry (polib.POEntry): The PO entry to extract the note from.

        Returns:
            Note: The extracted note, or an empty note if none found.
        """
        if entry.comment:
            match = re.search(cls.note_pattern, entry.comment, re.DOTALL | re.MULTILINE)
            if match:
                return cls(match.group(1).strip())

        return cls("")

    def update_entry(self, entry: polib.POEntry):
        """Update the PO entry's translator comments with the current note.

        Args:
            entry (polib.POEntry): The PO entry to update.
        """
        if self:
            entry.comment = re.sub(self.note_pattern, "", entry.comment).strip()
            entry.comment = ("\n" if entry.comment else "") + self.fstring_template.format(note=self)
