from deep_translator import (  # pyright: ignore[reportMissingTypeStubs]
    ChatGptTranslator,
    DeeplTranslator,
    GoogleTranslator,
    MicrosoftTranslator,
    MyMemoryTranslator,
    YandexTranslator,
)

from .config import TranslationServiceConfig
from .service_definition import TranslationServiceBase


class DeeplTranslationService(DeeplTranslator, TranslationServiceBase):
    def __init__(self, config: TranslationServiceConfig):
        self.handle_unsupported_language(
            super().__init__  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        )(
            source=config["source"],
            target=config["target"],
            api_key=config["api_key"],
            use_free_api=config.get("api_key_type", "free") == "free",
        )

    @classmethod
    def needs_api_key(cls) -> bool:
        return True

    async def translate(self, text: str) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().translate(text)  # pyright: ignore[reportUnknownMemberType]


class GoogleTranslationService(GoogleTranslator, TranslationServiceBase):
    def __init__(self, config: TranslationServiceConfig):
        self.handle_unsupported_language(
            super().__init__  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        )(
            source=config["source"],
            target=config["target"],
            proxies={**config["proxies"]} if config["proxies"] else None,
        )

    @classmethod
    def supports_proxies(cls) -> bool:
        return True

    async def translate(self, text: str) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().translate(text)  # pyright: ignore[reportUnknownMemberType]


class MyMemoryTranslationService(MyMemoryTranslator, TranslationServiceBase):
    def __init__(self, config: TranslationServiceConfig):
        self.handle_unsupported_language(
            super().__init__  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        )(
            source=config["source"],
            target=config["target"],
            proxies={**config["proxies"]} if config["proxies"] else None,
        )

    @classmethod
    def supports_proxies(cls) -> bool:
        return True

    async def translate(self, text: str) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
        result = super().translate(text)  # pyright: ignore[reportUnknownMemberType]
        return " ".join(result).replace("  ", " ") if isinstance(result, list) else result


class MicrosoftTranslationService(MicrosoftTranslator, TranslationServiceBase):
    def __init__(self, config: TranslationServiceConfig):
        self.handle_unsupported_language(
            super().__init__  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        )(
            source=config["source"],
            target=config["target"],
            api_key=config["api_key"],
            region=config["region"],
            proxies={**config["proxies"]} if config["proxies"] else None,
        )

    @classmethod
    def needs_api_key(cls) -> bool:
        return True

    @classmethod
    def supports_region(cls) -> bool:
        return True

    @classmethod
    def supports_proxies(cls) -> bool:
        return True

    async def translate(self, text: str) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().translate(text)  # pyright: ignore[reportUnknownMemberType]


class YandexTranslationService(YandexTranslator, TranslationServiceBase):
    def __init__(self, config: TranslationServiceConfig):
        self._proxies = config["proxies"]
        self.handle_unsupported_language(
            super().__init__  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        )(
            source=config["source"],
            target=config["target"],
            api_key=config["api_key"],
        )

    @classmethod
    def needs_api_key(cls) -> bool:
        return True

    @classmethod
    def supports_proxies(cls) -> bool:
        return True

    async def translate(self, text: str) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
        return super(YandexTranslator, self).translate(  # pyright: ignore[reportUnknownMemberType]
            text, proxies={**self._proxies} if self._proxies else None
        )


class ChatGPTTranslationService(ChatGptTranslator, TranslationServiceBase):
    def __init__(self, config: TranslationServiceConfig):
        self.handle_unsupported_language(
            super().__init__  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        )(source=config["source"], target=config["target"], api_key=config["api_key"], model=config["model"])

    @classmethod
    def needs_api_key(cls) -> bool:
        return True

    @classmethod
    def supports_model(cls) -> bool:
        return True

    async def translate(self, text: str) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().translate(text)  # pyright: ignore[reportUnknownMemberType]
