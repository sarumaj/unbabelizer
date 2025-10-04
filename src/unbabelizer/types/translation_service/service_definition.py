import re
from abc import ABCMeta, abstractmethod
from ast import literal_eval
from functools import wraps
from typing import Callable, ParamSpec, Protocol, TypeVar

from babel import negotiate_locale
from deep_translator.exceptions import LanguageNotSupportedException  # pyright: ignore[reportMissingTypeStubs]

from ...translation import determine_most_common_locale_separator
from .config import TranslationServiceConfig


class TranslationServiceProtocol(Protocol):
    def __init__(self, config: TranslationServiceConfig): ...
    @classmethod
    def needs_api_key(cls) -> bool: ...
    @classmethod
    def supports_model(cls) -> bool: ...
    @classmethod
    def supports_region(cls) -> bool: ...
    @classmethod
    def supports_proxies(cls) -> bool: ...
    async def translate(self, text: str) -> str: ...


P = ParamSpec("P")
R = TypeVar("R")


class TranslationServiceBase(metaclass=ABCMeta):
    @staticmethod
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

    @classmethod
    def needs_api_key(cls) -> bool:
        return False

    @classmethod
    def supports_model(cls) -> bool:
        return False

    @classmethod
    def supports_region(cls) -> bool:
        return False

    @classmethod
    def supports_proxies(cls) -> bool:
        return False

    @abstractmethod
    async def translate(self, text: str) -> str:
        raise NotImplementedError()
