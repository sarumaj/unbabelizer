import asyncio
import re
import traceback
from ast import literal_eval
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Literal,
    LiteralString,
    Optional,
    ParamSpec,
    Protocol,
    Sequence,
    TypeVar,
    Union,
    overload,
)

import polib
from babel import negotiate_locale
from babel.messages.frontend import CommandLineInterface
from deep_translator.exceptions import LanguageNotSupportedException  # pyright: ignore[reportMissingTypeStubs]
from textual.notifications import SeverityLevel
from textual.widget import Widget

from .log import Logger
from .translation import determine_most_common_locale_separator

if TYPE_CHECKING:

    @overload
    def _(message: str) -> str: ...  # pyright: ignore[reportInconsistentOverload, reportNoOverloadImplementation]


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


def get_base_type(ann: Any) -> Any:
    """Recursively extract the base type from complex type annotations.

    Args:
        ann (Any): The type annotation to process.
    Returns:
        Any: The base type extracted from the annotation.
    """
    origin = getattr(ann, "__origin__", None)
    if origin is Optional:
        return get_base_type(ann.__args__[0])

    if origin is Union:
        non_none_args = [arg for arg in ann.__args__ if arg is not type(None)]
        if len(non_none_args) == 1:
            return get_base_type(non_none_args[0])

    if origin is Literal or origin is LiteralString:
        return type(ann.__args__[0])  # pyright: ignore[reportUnknownVariableType]

    return ann


@contextmanager
def handle_exception(notifier: NotifyProtocol, logger: Logger):
    """A context manager that notifies the user of any exceptions that occur within its block.

    Args:
        notifier (NotifyProtocol): An object with a notify method to send notifications.
        logger (Logger): Logger instance for error logging.

    Yields:
        None: This context manager doesn't yield any value.
    """
    try:
        yield
    except Exception as exc_instance:
        notifier.notify(
            _("An error occurred: {error}").format(error=str(exc_instance)),
            title=_("⛔ Unexpected Error"),
            severity="error",
            timeout=None,
            markup=False,
        )
        logger.error(
            "An error occurred",
            extra={
                "context": "handle_exception",
                "error": str(exc_instance),
                "traceback": traceback.format_exception(type(exc_instance), exc_instance, exc_instance.__traceback__),
                "type": str(type(exc_instance)),
            },
        )


def handle_unsupported_language(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator to handle LanguageNotSupportedException by negotiating closest supported language.
    If negotiation fails, the original exception is raised.

    Args:
        func (Callable[P, R]): The function to be decorated.

    Returns:
        Callable[P, R]: The wrapped function with enhanced error handling.
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except LanguageNotSupportedException as e:
            match = next(re.finditer(r"^.*(\{.+\})$", f"{e.message}", re.MULTILINE), None)
            if not match:
                raise e

            supported_languages_dict = literal_eval(match.group(1))
            if not isinstance(supported_languages_dict, dict):
                raise e

            supported_languages = [
                f"{l}" for l in supported_languages_dict.values()  # pyright: ignore[reportUnknownVariableType]
            ]

            separator = determine_most_common_locale_separator(supported_languages)
            if len(args) >= 2 and all(isinstance(arg, str) for arg in args[:2]):
                source = negotiate_locale(
                    [args[0]], supported_languages, sep=separator  # pyright: ignore[reportArgumentType]
                )
                target = negotiate_locale(
                    [args[1]], supported_languages, sep=separator  # pyright: ignore[reportArgumentType]
                )
                if not source or not target:
                    raise e

                args = (source, target, *args[2:])  # pyright: ignore[reportAssignmentType]
                return func(*args, **kwargs)

            if all(isinstance(v, str) for k, v in kwargs.items() if k in ("source", "target")):
                source = negotiate_locale(
                    [kwargs["source"]], supported_languages, sep=separator  # pyright: ignore[reportArgumentType]
                )
                target = negotiate_locale(
                    [kwargs["target"]], supported_languages, sep=separator  # pyright: ignore[reportArgumentType]
                )
                if not source or not target:
                    raise e

                kwargs["source"] = source
                kwargs["target"] = target
                return func(*args, **kwargs)

            raise e

    return wrapper


def run_babel_cmd(args: Sequence[str]):
    """Run a Babel command with the given arguments."""
    cli = CommandLineInterface()
    try:
        cli.run(["pybabel", *args])  # pyright: ignore[reportUnknownMemberType]
    except SystemExit as e:
        raise SystemExit(
            f'Babel command failed with exit code {e.code}: command was: "pybabel {" ".join(args)}"'
        ) from e


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


def write_new_tcomment(entry: polib.POEntry, comment: str):
    """Write a new translator comment to a PO entry, replacing any existing comment with the same prefix.

    Args:
        entry (polib.POEntry): The PO entry to modify.
        comment (str): The new translator comment to add.
    """
    entry.tcomment = "\n".join(
        (
            (entry.tcomment or ""),
            (
                comment.format(
                    timestamp=datetime.now().isoformat(sep=" ", timespec="seconds"),
                )
                if "{timestamp}" in comment
                else comment
            ),
        )
    )
