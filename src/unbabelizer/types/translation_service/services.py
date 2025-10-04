from enum import Enum
from typing import TYPE_CHECKING, NamedTuple, Type, overload

from .service_definition import TranslationServiceProtocol
from .service_definitions import (
    ChatGPTTranslationService,
    DeeplTranslationService,
    GoogleTranslationService,
    MicrosoftTranslationService,
    MyMemoryTranslationService,
    YandexTranslationService,
)

if TYPE_CHECKING:

    @overload
    def _(message: str) -> str: ...  # pyright: ignore[reportInconsistentOverload, reportNoOverloadImplementation]


class TranslationServiceEntry(NamedTuple):
    name: str
    service: Type[TranslationServiceProtocol]


class TranslationServices(Enum):
    GOOGLE_TRANSLATE = TranslationServiceEntry(_("Google Translate"), GoogleTranslationService)
    MY_MEMORY = TranslationServiceEntry(_("MyMemory Translator"), MyMemoryTranslationService)
    MICROSOFT_TRANSLATE = TranslationServiceEntry(_("Microsoft Translator"), MicrosoftTranslationService)
    YANDEX_TRANSLATE = TranslationServiceEntry(_("Yandex Translate"), YandexTranslationService)
    CHATGPT = TranslationServiceEntry(_("ChatGPT Translation Service"), ChatGPTTranslationService)
    DEEPL_TRANSLATOR = TranslationServiceEntry(_("DeepL Translator"), DeeplTranslationService)

    @classmethod
    def from_service_name(cls, name: str) -> "TranslationServices":
        for service in cls:
            if service.name == name or service.value.name == name:
                return service
        raise ValueError(f"Unknown translation service name: {name}")

    @property
    def translation_service_name(self) -> str:
        return self.value.name

    @property
    def translation_service_protocol(self) -> Type[TranslationServiceProtocol]:
        return self.value.service
