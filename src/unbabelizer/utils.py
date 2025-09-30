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


def escape_control_chars(text: str) -> str:
    """Escape control characters using character class pattern"""

    def replace_func(match: re.Match[str]) -> str:
        char = match.group(0)
        escape_map = {
            "\n": "\\n",  # new line
            "\r": "\\r",  # carriage return
            "\t": "\\t",  # tab
            "\b": "\\b",  # backspace
            "\f": "\\f",  # form feed
            "\v": "\\v",  # vertical tab
            "\a": "\\a",  # bell/alert
            "\\": "\\\\",  # backslash
            "\0": "\\0",  # null character
        }
        return escape_map.get(char, f"\\x{ord(char):02x}")

    return re.sub(r"[\n\r\t\b\f\v\a\\\x00]", replace_func, text)


def run_babel_cmd(args: Sequence[str]):
    """Run a Babel command with the given arguments."""
    cli = CommandLineInterface()
    print("Running Babel command with args:", args)
    cli.run(["pybabel", *args])  # pyright: ignore[reportUnknownMemberType]


def unescape_control_chars(text: str) -> str:
    """Unescape control chars including hex notation"""

    def replace(match: re.Match[str]) -> str:
        esc = match.group(0)
        if esc == r"\n":
            return "\n"
        if esc == r"\r":
            return "\r"
        if esc == r"\t":
            return "\t"
        if esc == r"\b":
            return "\b"
        if esc == r"\f":
            return "\f"
        if esc == r"\v":
            return "\v"
        if esc == r"\a":
            return "\a"
        if esc == r"\0":
            return "\0"
        if esc == r"\\":
            return "\\"
        if esc.startswith(r"\x"):
            return chr(int(esc[2:], 16))
        return esc  # fallback

    return re.sub(r"\\n|\\r|\\t|\\b|\\f|\\v|\\a|\\0|\\\\|\\x[0-9a-fA-F]{2}", replace, text)


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
