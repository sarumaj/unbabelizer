from enum import Enum
from gettext import gettext as _
from pathlib import Path
from typing import Any, Dict, NamedTuple, Tuple

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
            if isinstance(file, polib.POFile):
                self._po = file
            else:
                raise ValueError(f"Failed to load PO file from path: {value}")
        else:
            self._po = value


class SubCommand(NamedTuple):
    """A sub-command of the application."""

    name: str
    description: str
    requires_ui: bool
    default_check: bool

    @property
    def selection_list_item(self) -> Tuple[str, str, bool]:
        """Return a tuple suitable for use in a SelectionList item."""
        return (self.description, self.name, self.default_check)


class AppSubCommand(Enum):
    EXTRACT_UPDATE = SubCommand("extract_update", _("Extract and Update"), False, True)
    TRANSLATE = SubCommand("translate", _("Translate"), True, False)
    REVIEW = SubCommand("review", _("Review"), True, False)
    COMPILE = SubCommand("compile", _("Compile"), False, True)


class TableCell(NamedTuple):
    """A cell in the PO review table."""

    row_no: str
    type: str
    msgid: str
    msgstr: str
    msgstr: str
    msgstr: str


class SingletonType(type):
    """A metaclass for singleton classes."""

    _instances: Dict[str, object] = {}

    def __new__(cls, name: str, bases: Tuple[type, ...], attrs: Dict[str, Any]) -> Any:
        if name not in cls._instances:
            instance = super().__new__(cls, name, bases, attrs)
            cls._instances[name] = instance
        return cls._instances[name]
