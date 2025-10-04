from pathlib import Path

import polib


class POFileHandler:
    def __init__(self, po_path: Path):
        """Initialize the POFileHandler with the given PO file path.

        Args:
            po_path (Path): Path to the PO file.
        """
        self.pofile_path = po_path
        self.pofile = po_path  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

    @property
    def pofile_path(self) -> Path:
        """Path to the PO file."""
        return self._po_path

    @pofile_path.setter
    def pofile_path(self, value: Path):
        """Set the PO file path."""
        self._po_path = value

    @property
    def pofile(self) -> polib.POFile:
        """Return the loaded PO file."""
        return self._po  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportReturnType]

    @pofile.setter
    def pofile(self, value: polib.POFile | Path) -> None:
        """Set the PO file."""
        if isinstance(value, Path):
            file = polib.pofile(str(value))  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            if isinstance(file, polib.POFile):  # pyright: ignore[reportUnnecessaryIsInstance]
                self._po = file
            else:
                raise ValueError(f"Failed to load PO file from path: {value}")
        else:
            self._po = value
