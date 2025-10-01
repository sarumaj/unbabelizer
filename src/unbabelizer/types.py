from enum import Enum
from gettext import gettext as _
from pathlib import Path
from typing import Any, Dict, NamedTuple, Protocol, Tuple, Type

import polib
from deep_translator import (  # pyright: ignore[reportMissingTypeStubs]
    ChatGptTranslator,
    GoogleTranslator,
    MicrosoftTranslator,
    MyMemoryTranslator,
    YandexTranslator,
)


class GoogleTranslationService(GoogleTranslator):
    def __init__(
        self,
        source: str = "auto",
        target: str = "en",
        api_key: str | None = None,
        proxies: Dict[str, str] | None = None,
        model: str | None = None,
        region: str | None = None,
    ):
        _ = (model, region, api_key)  # Unused
        super().__init__(source=source, target=target, proxies=proxies)  # pyright: ignore[reportUnknownMemberType]

    @classmethod
    def needs_proxies(cls) -> bool:
        return True

    @classmethod
    def needs_api_key(cls) -> bool:
        return False

    @classmethod
    def needs_model(cls) -> bool:
        return False

    @classmethod
    def needs_region(cls) -> bool:
        return False

    async def translate(self, text: str) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().translate(text)  # pyright: ignore[reportUnknownMemberType]


class MyMemoryTranslationService(MyMemoryTranslator):
    def __init__(
        self,
        source: str = "auto",
        target: str = "en",
        api_key: str | None = None,
        proxies: Dict[str, str] | None = None,
        model: str | None = None,
        region: str | None = None,
    ):
        _ = (model, region, api_key)  # Unused
        super().__init__(source=source, target=target, proxies=proxies)  # pyright: ignore[reportUnknownMemberType]

    @classmethod
    def needs_proxies(cls) -> bool:
        return True

    @classmethod
    def needs_api_key(cls) -> bool:
        return False

    @classmethod
    def needs_model(cls) -> bool:
        return False

    @classmethod
    def needs_region(cls) -> bool:
        return False

    async def translate(self, text: str) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
        result = super().translate(text)  # pyright: ignore[reportUnknownMemberType]
        return "".join(result) if isinstance(result, list) else result


class MicrosoftTranslationService(MicrosoftTranslator):
    def __init__(
        self,
        source: str = "auto",
        target: str = "en",
        api_key: str | None = None,
        proxies: Dict[str, str] | None = None,
        model: str | None = None,
        region: str | None = None,
    ):
        _ = model  # Unused
        super().__init__(  # pyright: ignore[reportUnknownMemberType]
            source=source, target=target, api_key=api_key, proxies=proxies, region=region
        )

    @classmethod
    def needs_proxies(cls) -> bool:
        return True

    @classmethod
    def needs_api_key(cls) -> bool:
        return True

    @classmethod
    def needs_model(cls) -> bool:
        return False

    @classmethod
    def needs_region(cls) -> bool:
        return True

    async def translate(self, text: str) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().translate(text)  # pyright: ignore[reportUnknownMemberType]


class YandexTranslationService(YandexTranslator):
    def __init__(
        self,
        source: str = "auto",
        target: str = "en",
        api_key: str | None = None,
        proxies: Dict[str, str] | None = None,
        model: str | None = None,
        region: str | None = None,
    ):
        _ = (model, region)  # Unused
        self.proxies = proxies
        super().__init__(source=source, target=target, api_key=api_key)  # pyright: ignore[reportUnknownMemberType]

    @classmethod
    def needs_proxies(cls) -> bool:
        return True

    @classmethod
    def needs_api_key(cls) -> bool:
        return True

    @classmethod
    def needs_model(cls) -> bool:
        return False

    @classmethod
    def needs_region(cls) -> bool:
        return False

    async def translate(self, text: str) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().translate(text, proxies=self.proxies)  # pyright: ignore[reportUnknownMemberType]


class ChatGPTTranslationService(ChatGptTranslator):
    def __init__(
        self,
        source: str = "auto",
        target: str = "en",
        api_key: str | None = None,
        proxies: Dict[str, str] | None = None,
        model: str | None = None,
        region: str | None = None,
    ):
        _ = (api_key, region)  # Unused
        super().__init__(  # pyright: ignore[reportUnknownMemberType]
            source=source, target=target, proxies=proxies, model=model
        )

    @classmethod
    def needs_proxies(cls) -> bool:
        return True

    @classmethod
    def needs_api_key(cls) -> bool:
        return True

    @classmethod
    def needs_model(cls) -> bool:
        return True

    @classmethod
    def needs_region(cls) -> bool:
        return False

    async def translate(self, text: str) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().translate(text)  # pyright: ignore[reportUnknownMemberType]


class TranslationServiceProtocol(Protocol):
    def __init__(
        self,
        source: str = "auto",
        target: str = "en",
        api_key: str | None = None,
        proxies: Dict[str, str] | None = None,
        model: str | None = None,
        region: str | None = None,
    ): ...
    @classmethod
    def needs_proxies(cls) -> bool: ...
    @classmethod
    def needs_api_key(cls) -> bool: ...
    @classmethod
    def needs_model(cls) -> bool: ...
    @classmethod
    def needs_region(cls) -> bool: ...
    async def translate(self, text: str) -> str: ...


class TranslationServices(Enum):
    GOOGLE_TRANSLATE = "GoogleTranslationService"
    MY_MEMORY = "MyMemoryTranslationService"
    MICROSOFT_TRANSLATE = "MicrosoftTranslationService"
    YANDEX_TRANSLATE = "YandexTranslationService"
    CHATGPT = "ChatGPTTranslationService"

    def init_translation_service(
        self,
        source: str = "auto",
        target: str = "en",
        api_key: str | None = None,
        proxies: Dict[str, str] | None = None,
        model: str | None = None,
        region: str | None = None,
    ) -> TranslationServiceProtocol:
        svc_class: Type[TranslationServiceProtocol] = GoogleTranslationService
        match self:
            case TranslationServices.GOOGLE_TRANSLATE:
                svc_class = GoogleTranslationService
            case TranslationServices.MY_MEMORY:
                svc_class = MyMemoryTranslationService
            case TranslationServices.MICROSOFT_TRANSLATE:
                svc_class = MicrosoftTranslationService
            case TranslationServices.YANDEX_TRANSLATE:
                svc_class = YandexTranslationService
            case TranslationServices.CHATGPT:
                svc_class = ChatGPTTranslationService
            case _:
                raise NotImplementedError(f"Translation service {self.value} is not implemented.")
        return svc_class(  # pyright: ignore[reportUnknownMemberType, reportCallIssue]
            source=source,
            target=target,
            api_key=api_key,
            proxies=proxies,
            model=model,
            region=region,
        )


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


class TableCell(NamedTuple):
    """A cell in the PO review table."""

    row_no: str
    type: str
    msgid: str
    msgstr: str


class SingletonType(type):
    """A metaclass for singleton classes."""

    _instances: Dict[str, object] = {}

    def __new__(cls, name: str, bases: Tuple[type, ...], attrs: Dict[str, Any]) -> Any:
        if name not in cls._instances:
            instance = super().__new__(cls, name, bases, attrs)
            cls._instances[name] = instance
        return cls._instances[name]
