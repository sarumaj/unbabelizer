from typing import TypeAlias, TypedDict

from ..subcommand import SubCommandChoices


class Presets(TypedDict):
    override_existing_translations: bool | None
    fuzzy_new_translations: bool | None
    default_translation_service: str | None
    workflow_actions: list[SubCommandChoices] | None


Proxies: TypeAlias = dict[str, str | None] | None


class TranslationServiceConfig(TypedDict):
    source: str
    target: str
    api_key: str | None
    api_key_type: str | None
    proxies: Proxies | None
    model: str | None
    region: str | None
    presets: Presets
