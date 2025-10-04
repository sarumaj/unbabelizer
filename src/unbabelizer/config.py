import argparse
import sys
import tomllib
from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, overload

import jmespath
from pydantic import BaseModel, Field

from .log import Logger
from .types.subcommand import SubCommandChoices, SubCommands
from .types.translation_service.config import Presets as TranslationServicePresets
from .types.translation_service.config import TranslationServiceConfig
from .types.translation_service.services import TranslationServices
from .utils import get_base_type

if TYPE_CHECKING:

    @overload
    def _(message: str) -> str: ...  # pyright: ignore[reportInconsistentOverload, reportNoOverloadImplementation]


logger = Logger()


class Presets(BaseModel):
    workflow_actions: List[SubCommandChoices] = Field(
        default=["extract_update", "review", "compile"],
        description=_("Actions to perform in the workflow"),
        json_schema_extra={
            "pyproject.toml": "tool.unbabelizer.presets.workflow_actions",
            "argparse.flag": "--presets-workflow-actions",
            "argparse.choices": ["extract_update", "translate", "review", "compile"],
            "argparse.nargs": "*",
        },
    )
    override_existing_translations: bool = Field(
        default=False,
        description=_("Override existing translations"),
        json_schema_extra={
            "pyproject.toml": "tool.unbabelizer.presets.override_existing_translations",
            "argparse.flag": "--presets-override-existing-translations",
        },
    )
    fuzzy_new_translations: bool = Field(
        default=False,
        description=_("Mark new translations as fuzzy"),
        json_schema_extra={
            "pyproject.toml": "tool.unbabelizer.presets.fuzzy_new_translations",
            "argparse.flag": "--presets-fuzzy-new-translations",
        },
    )
    default_translation_service: str = Field(
        default=TranslationServices.GOOGLE_TRANSLATE.translation_service_name,
        description=_("Default translation service to use"),
        json_schema_extra={
            "pyproject.toml": "tool.unbabelizer.presets.default_translation_service",
            "argparse.flag": "--presets-default-translation-service",
            "argparse.choices": [s.translation_service_name for s in TranslationServices],
        },
    )


class Config(Presets):
    """unbabelizer loads configuration from pyproject.toml and command line arguments."""

    author: str = Field(
        description=_("Author of the project"),
        json_schema_extra={"pyproject.toml": "project.authors[0].name", "argparse.flag": "--author"},
    )
    email: str = Field(
        description=_("Email of the author"),
        json_schema_extra={"pyproject.toml": "project.authors[0].email", "argparse.flag": "--email"},
    )
    version: str = Field(
        description=_("Version of the project"),
        json_schema_extra={"pyproject.toml": "project.version", "argparse.flag": "--version"},
    )
    title: str = Field(
        description=_("Title of the project"),
        json_schema_extra={"pyproject.toml": "project.name", "argparse.flag": "--title"},
    )
    locale_dir: Path = Field(
        default=Path("locale"),
        description=_("Directory for locale files"),
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.locale_dir", "argparse.flag": "--locale-dir"},
    )
    input_paths: List[Path] = Field(
        default=[Path.cwd()],
        description=_("Paths to search for source files"),
        json_schema_extra={
            "pyproject.toml": "tool.unbabelizer.input_paths",
            "argparse.flag": "--input-paths",
            "argparse.nargs": "+",
        },
    )
    exclude_patterns: List[str] = Field(
        default=[],
        description=_("Paths to exclude from searching"),
        json_schema_extra={
            "pyproject.toml": "tool.unbabelizer.exclude_patterns",
            "argparse.flag": "--exclude-patterns",
            "argparse.nargs": "*",
        },
    )
    src_lang: str = Field(
        default="en",
        description=_("Source language code"),
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.src_lang", "argparse.flag": "--src-lang"},
    )
    dest_lang: List[str] = Field(
        description=_("Destination language code"),
        json_schema_extra={
            "pyproject.toml": "tool.unbabelizer.dest_lang",
            "argparse.flag": "--dest-lang",
            "argparse.nargs": "+",
        },
    )
    domain: str = Field(
        default="messages",
        description=_("Domain for the .po files"),
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.domain", "argparse.flag": "--domain"},
    )
    mapping_file: str = Field(
        default="[python: **.py]\nencoding = utf-8\n",
        description=_("Path to the Babel mapping file (as CLI argument) or its content (in pyproject.toml config)"),
        json_schema_extra={
            "pyproject.toml": "tool.unbabelizer.mapping_file_content",
            "argparse.flag": "--mapping-file",
        },
    )
    line_width: int = Field(
        default=120,
        description=_("Line width for .po files"),
        json_schema_extra={
            "pyproject.toml": "tool.unbabelizer.line_width",
            "argparse.flag": "--line-width",
        },
    )
    keywords: List[str] = Field(
        default=[],
        description=_("Additional keywords to look for in source files"),
        json_schema_extra={
            "pyproject.toml": "tool.unbabelizer.keywords",
            "argparse.flag": "--keywords",
            "argparse.nargs": "+",
        },
    )
    http_proxy: Optional[str] = Field(
        default=None,
        description=_("HTTP proxy URL"),
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.proxy_http", "argparse.flag": "--http-proxy"},
    )
    https_proxy: Optional[str] = Field(
        default=None,
        description=_("HTTPS proxy URL"),
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.proxy_https", "argparse.flag": "--https-proxy"},
    )
    api_key: Optional[str] = Field(
        default=None,
        description=_("API key for the translation service, if required"),
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.api_key", "argparse.flag": "--api-key"},
    )
    api_key_type: Optional[Literal["free", "paid"]] = Field(
        default=None,
        description=_('Type of API key, if applicable (either "free" or "paid")'),
        json_schema_extra={
            "pyproject.toml": "tool.unbabelizer.api_key_type",
            "argparse.flag": "--api-key-type",
            "argparse.choices": ["free", "paid"],
        },
        pattern="^(free|paid)$",
    )
    model: Optional[str] = Field(
        default=None,
        description=_("Model to use for the translation service, if applicable"),
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.model", "argparse.flag": "--model"},
    )
    region: Optional[str] = Field(
        default=None,
        description=_("Region for the translation service, if applicable"),
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.region", "argparse.flag": "--region"},
    )

    @property
    def presets(self) -> TranslationServicePresets:
        return TranslationServicePresets(
            workflow_actions=self.workflow_actions,
            override_existing_translations=self.override_existing_translations,
            fuzzy_new_translations=self.fuzzy_new_translations,
            default_translation_service=self.default_translation_service,
        )

    def is_workflow_action_enabled(self, action: SubCommands, default: bool) -> bool:
        if self.presets["workflow_actions"] is None:
            return default

        return action.command_name in self.presets["workflow_actions"]

    def get_translation_config(self, dest_lang_index: int) -> TranslationServiceConfig:
        """Prepare the configuration dictionary for the translation service."""
        return {
            "source": self.src_lang,
            "target": self.dest_lang[dest_lang_index],
            "api_key": self.api_key,
            "api_key_type": self.api_key_type,
            "proxies": {k: v for k, v in {"http": self.http_proxy, "https": self.https_proxy}.items() if v} or None,
            "model": self.model,
            "region": self.region,
            "presets": self.presets,
        }

    @classmethod
    def source_cli_args(cls, args: List[str]) -> Dict[str, Any]:
        """Parse command line arguments to create a Config instance."""
        parser = argparse.ArgumentParser(
            description=_("unbabelizer {version} configuration").format(version=pkg_version("unbabelizer"))
        )
        for name, field in cls.model_fields.items():
            schema = (  # pyright: ignore[reportUnknownVariableType]
                field.json_schema_extra  # pyright: ignore[reportUnknownMemberType]
                if isinstance(field.json_schema_extra, dict)
                else {}
            )

            flag = schema.get(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                "argparse.flag", f"--{name.replace('_', '-')}"
            )
            choices = schema.get(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                "argparse.choices", None
            )
            nargs = schema.get(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                "argparse.nargs", None
            )
            config_field = schema.get(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                "pyproject.toml", None
            )
            if choices is not None and not isinstance(choices, list):
                choices = [choices]  # pyright: ignore[reportUnknownVariableType]
            parser.add_argument(
                flag,  # pyright: ignore[reportArgumentType]
                help=(
                    (field.description or "")
                    + (
                        " "
                        + _('(overrides pyproject.toml setting: "{config_field}")').format(
                            config_field=config_field  # pyright: ignore[reportUnknownArgumentType]
                        )
                    )
                    if config_field
                    else ""
                ),
                default=None,
                nargs=nargs,  # pyright: ignore[reportArgumentType]
                type=get_base_type(field.annotation),
                choices=choices,  # pyright: ignore[reportUnknownArgumentType]
            )

        parsed_args = parser.parse_args(args)
        field_values = {k: v for k, v in vars(parsed_args).items() if v is not None}
        logger.debug("Parsed CLI args", extra={"context": "Config.source_cli_args", "data": field_values})
        return field_values

    @classmethod
    def source_pyproject_toml(cls, file_path: Path) -> Dict[str, Any]:
        """Load configuration from pyproject.toml using jmespath."""
        if not file_path.exists() or not file_path.is_file():
            return {}

        pyproject_data = tomllib.loads(file_path.read_text())
        logger.debug(
            "Loaded pyproject.toml data:", extra={"context": "Config.source_pyproject_toml", "data": pyproject_data}
        )
        field_values: Dict[str, Any] = {}
        for name, field in cls.model_fields.items():
            schema = (  # pyright: ignore[reportUnknownVariableType]
                field.json_schema_extra  # pyright: ignore[reportUnknownMemberType]
                if isinstance(field.json_schema_extra, dict)
                else {}
            )
            jmespath_query = schema.get(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                "pyproject.toml", name
            )
            value = jmespath.search(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                jmespath_query, pyproject_data  # pyright: ignore[reportArgumentType]c
            )
            logger.debug(
                "JMESPath query result",
                extra={  # pyright: ignore[reportUnknownArgumentType]
                    "context": "Config.source_pyproject_toml",
                    "field": name,
                    "query": jmespath_query,
                    "value": value,
                },
            )
            field_values[name] = value

        field_values = {k: v for k, v in field_values.items() if v is not None}
        logger.debug(
            "Extracted config data from pyproject.toml",
            extra={"context": "Config.source_pyproject_toml", "data": field_values},
        )
        return field_values

    @classmethod
    def build(cls, args: List[str] | None) -> "Config":
        """Validate and create a Config instance from source data."""
        config_data = cls.source_pyproject_toml(Path("pyproject.toml"))
        config_data.update(cls.source_cli_args(args or sys.argv[1:]))
        logger.info("Validated config data", extra={"context": "Config.build", "data": config_data})
        return cls.model_validate(config_data)
