from gettext import gettext as _

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Static

from ..log import Logger
from ..utils import apply_styles, wait_for_element


class ConfirmInevitable(ModalScreen[bool]):
    """A simple confirmation dialog modal."""

    BINDINGS = [
        Binding(key="left", action="focus_ok", description=_("Cancel"), show=False),
        Binding(key="right", action="focus_cancel", description=_("OK"), show=False),
    ]

    @property
    def logger(self) -> Logger:
        """Return the application logger."""
        return getattr(
            self.app,  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
            "logger",
        )

    def compose(self) -> ComposeResult:
        """Compose the modal's layout."""
        yield Header()
        yield apply_styles(
            Container(
                apply_styles(Static(_("Are you sure? This action cannot be undone.")), width="1fr"),
                apply_styles(
                    Horizontal(
                        Button(_("OK"), id="ok", variant="default"),
                        Button(_("Cancel"), id="cancel", variant="primary"),
                    ),
                    width="1fr",
                    height="1fr",
                ),
            ),
            width="1fr",
            height="1fr",
        )
        yield Footer()

    async def on_mount(self):
        """Focus the Cancel button when the modal is mounted."""
        (await wait_for_element(self.query_one, selector="#cancel", expect_type=Button)).focus()

    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button press events."""
        if event.button.id == "ok":
            self.logger.debug(
                "User confirmed inevitable action.", extra={"context": "ConfirmInevitable.on_button_pressed"}
            )
            self.dismiss(True)
        elif event.button.id == "cancel":
            self.logger.debug(
                "User canceled inevitable action.", extra={"context": "ConfirmInevitable.on_button_pressed"}
            )
            self.dismiss(False)

    async def action_focus_ok(self):
        """Focus the OK button."""
        (await wait_for_element(self.query_one, selector="#ok", expect_type=Button)).focus()

    async def action_focus_cancel(self):
        """Focus the Cancel button."""
        (await wait_for_element(self.query_one, selector="#cancel", expect_type=Button)).focus()
