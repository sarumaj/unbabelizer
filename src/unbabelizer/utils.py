import asyncio
import re
from contextlib import AbstractContextManager
from gettext import gettext as _
from types import TracebackType
from typing import Callable, Literal, Optional, ParamSpec, Protocol, Sequence, Type, TypeVar

from babel.messages.frontend import CommandLineInterface
from textual.notifications import SeverityLevel
from textual.widget import Widget

from .log import Logger

R = TypeVar("R")
P = ParamSpec("P")


class NotifyProtocol(Protocol):
    def notify(
        self,
        message: str,
        *,
        title: str = "",
        severity: SeverityLevel = "information",
        timeout: float | None = None,
        markup: bool = True,
    ): ...


class NotifyException(AbstractContextManager["NotifyException"]):
    """A context manager that notifies the user of any exceptions that occur within its block."""

    def __init__(self, notifier: NotifyProtocol):
        """Initialize the NotifyException context manager.

        Args:
            notifier (NotifyProtocol): An object with a notify method to send notifications.
        """
        self.notifier = notifier
        self.logger = Logger()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_instance: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        if exc_instance:
            self.notifier.notify(
                _("An error occurred: {error}").format(error=str(exc_instance)),
                title=_("⛔ Unexpected Error"),
                severity="error",
                timeout=None,
                markup=False,
            )
            self.logger.error(
                "An error occurred",
                extra={
                    "context": "NotifyException.__exit__",
                    "error": str(exc_instance),
                    "traceback": str(traceback),
                    "type": str(exc_type),
                },
            )
            return True


def apply_styles(
    widget: Widget,
    vertical: Literal["middle", "top", "bottom"] = "middle",
    horizontal: Literal["center", "left", "right"] = "center",
    width: str | int | None = None,
    height: str | int | None = None,
) -> Widget:
    """Center the content of a Textual widget both horizontally and vertically.

    Args:
        widget (Widget): The widget whose content is to be centered.
    """
    widget.styles.content_align = (horizontal, vertical)
    widget.styles.align = (horizontal, vertical)
    if width is not None:
        widget.styles.width = width
    if height is not None:
        widget.styles.height = height
    return widget


def correct_translation(msgid: str, translation: str) -> str:
    """Correct common issues in the translated text.

    This includes fixing placeholders, extra spaces, and punctuation spacing.

    Args:
        msgid (str): The original message ID with placeholders.
        translation (str): The translated text to be corrected.
    Returns:
        str: The corrected translation.
    """
    placeholders = re.findall(r"\{[^}]+\}", msgid)
    for ph in placeholders:
        translation = re.sub(r"\{[^}]+\}", ph, translation, count=1)

    translation = re.sub(r"\s+", " ", translation)
    translation = re.sub(r"\s+([.,;:!?%\)])", r"\1", translation)
    translation = re.sub(r"\(\s+", "(", translation)
    translation = re.sub(r"\s+-\s*(\w)", r"-\1", translation)
    return translation.strip()


def run_babel_cmd(args: Sequence[str]):
    """Run a Babel command with the given arguments."""
    cli = CommandLineInterface()
    print("Running Babel command with args:", args)
    cli.run(["pybabel", *args])  # pyright: ignore[reportUnknownMemberType]


async def wait_for_element(
    query_func: Callable[P, R],
    timeout: float = 5.0,
    interval: float = 0.1,
    *args: P.args,
    **kwargs: P.kwargs,
) -> R:
    """Wait for a UI element to be available by repeatedly calling the query function.

    Args:
        query_func (Callable[P, R]): The function to query the UI element.
        timeout (float): Maximum time to wait for the element.
        interval (float): Time between successive queries.
        *args: Positional arguments for the query function.
        **kwargs: Keyword arguments for the query function.

    Returns:
        R: The result from the query function.
    Raises:
        ValueError: If the element is not found within the timeout period.
    """
    total_time = 0.0
    while total_time < timeout:
        try:
            return query_func(*args, **kwargs)
        except Exception:
            await asyncio.sleep(interval)
            total_time += interval

    raise ValueError("UI element not found within timeout")
