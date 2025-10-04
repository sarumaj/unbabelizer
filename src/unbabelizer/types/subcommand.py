from enum import Enum
from typing import TYPE_CHECKING, Literal, NamedTuple, TypeAlias, overload

if TYPE_CHECKING:

    @overload
    def _(message: str) -> str: ...  # pyright: ignore[reportInconsistentOverload, reportNoOverloadImplementation]


class SubCommand(NamedTuple):
    """A sub-command of the application."""

    name: str
    description: str
    requires_ui: bool
    default_check: bool


class SubCommands(Enum):
    """Enumeration of sub-commands."""

    EXTRACT_UPDATE = SubCommand("extract_update", _("Extract and Update"), False, True)
    TRANSLATE = SubCommand("translate", _("Translate"), True, False)
    REVIEW = SubCommand("review", _("Review"), True, True)
    COMPILE = SubCommand("compile", _("Compile"), False, True)

    @property
    def command_name(self) -> str:
        return self.value.name

    @property
    def command_description(self) -> str:
        return self.value.description

    @property
    def command_requires_ui(self) -> bool:
        return self.value.requires_ui

    @property
    def command_default_check(self) -> bool:
        return self.value.default_check


SubCommandChoices: TypeAlias = Literal["extract_update", "translate", "review", "compile"]
