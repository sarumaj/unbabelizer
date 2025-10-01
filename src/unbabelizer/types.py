from enum import Enum
from gettext import gettext as _
from pathlib import Path
from typing import Any, Dict, NamedTuple, Protocol, Tuple, Type, TypedDict

import polib
from deep_translator import (  # pyright: ignore[reportMissingTypeStubs]
    ChatGptTranslator,
    GoogleTranslator,
    MicrosoftTranslator,
    MyMemoryTranslator,
    YandexTranslator,
)


class TranslationServiceConfig(TypedDict):
    source: str
    target: str
    api_key: str | None
    proxies: dict[str, str] | None
    model: str | None
    region: str | None


class GoogleTranslationService(GoogleTranslator):
    def __init__(self, config: TranslationServiceConfig):
        super().__init__(  # pyright: ignore[reportUnknownMemberType]
            source=config["source"], target=config["target"], proxies=config["proxies"]
        )

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
        return True

    async def translate(self, text: str) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().translate(text)  # pyright: ignore[reportUnknownMemberType]


class MyMemoryTranslationService(MyMemoryTranslator):
    def __init__(self, config: TranslationServiceConfig):
        super().__init__(  # pyright: ignore[reportUnknownMemberType]
            source=config["source"], target=config["target"], proxies=config["proxies"]
        )

    @classmethod
    def needs_api_key(cls) -> bool:
        return False

    @classmethod
    def supports_proxies(cls) -> bool:
        return True

    @classmethod
    def supports_model(cls) -> bool:
        return False

    @classmethod
    def supports_region(cls) -> bool:
        return False

    async def translate(self, text: str) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
        result = super().translate(text)  # pyright: ignore[reportUnknownMemberType]
        return " ".join(result).replace("  ", " ") if isinstance(result, list) else result


class MicrosoftTranslationService(MicrosoftTranslator):
    def __init__(self, config: TranslationServiceConfig):
        super().__init__(  # pyright: ignore[reportUnknownMemberType]
            source=config["source"],
            target=config["target"],
            api_key=config["api_key"],
            region=config["region"],
            proxies=config["proxies"],
        )

    @classmethod
    def needs_api_key(cls) -> bool:
        return True

    @classmethod
    def supports_model(cls) -> bool:
        return False

    @classmethod
    def supports_region(cls) -> bool:
        return True

    @classmethod
    def supports_proxies(cls) -> bool:
        return True

    async def translate(self, text: str) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().translate(text)  # pyright: ignore[reportUnknownMemberType]


class YandexTranslationService(YandexTranslator):
    def __init__(self, config: TranslationServiceConfig):
        self._proxies = config["proxies"]
        super().__init__(  # pyright: ignore[reportUnknownMemberType]
            source=config["source"], target=config["target"], api_key=config["api_key"]
        )

    @classmethod
    def needs_api_key(cls) -> bool:
        return True

    @classmethod
    def supports_model(cls) -> bool:
        return False

    @classmethod
    def supports_region(cls) -> bool:
        return False

    @classmethod
    def supports_proxies(cls) -> bool:
        return True

    async def translate(self, text: str) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().translate(text, proxies=self._proxies)  # pyright: ignore[reportUnknownMemberType]


class ChatGPTTranslationService(ChatGptTranslator):
    def __init__(self, config: TranslationServiceConfig):
        super().__init__(  # pyright: ignore[reportUnknownMemberType]
            source=config["source"], target=config["target"], api_key=config["api_key"], model=config["model"]
        )

    @classmethod
    def needs_api_key(cls) -> bool:
        return True

    @classmethod
    def supports_model(cls) -> bool:
        return True

    @classmethod
    def supports_region(cls) -> bool:
        return False

    @classmethod
    def supports_proxies(cls) -> bool:
        return False

    async def translate(self, text: str) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().translate(text)  # pyright: ignore[reportUnknownMemberType]


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
    @classmethod
    def requires_negotiation(cls) -> bool: ...
    async def translate(self, text: str) -> str: ...


class TranslationServices(str, Enum):
    GOOGLE_TRANSLATE = _("Google Translate")
    MY_MEMORY = _("MyMemory Translator")
    MICROSOFT_TRANSLATE = _("Microsoft Translator")
    YANDEX_TRANSLATE = _("Yandex Translate")
    CHATGPT = _("ChatGPT Translation Service")

    @property
    def translation_service_protocol(self) -> Type[TranslationServiceProtocol]:
        match self:
            case TranslationServices.GOOGLE_TRANSLATE:
                return GoogleTranslationService
            case TranslationServices.MY_MEMORY:
                return MyMemoryTranslationService
            case TranslationServices.MICROSOFT_TRANSLATE:
                return MicrosoftTranslationService
            case TranslationServices.YANDEX_TRANSLATE:
                return YandexTranslationService
            case TranslationServices.CHATGPT:
                return ChatGPTTranslationService
            case _:
                raise NotImplementedError(f"Translation service {self.value} is not implemented.")


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
