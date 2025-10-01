import argparse
import sys
import tomllib
from gettext import gettext as _
from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import jmespath
from pydantic import BaseModel, Field

from .log import Logger
from .types import TranslationServiceConfig
from .utils import get_base_type

logger = Logger()


class Config(BaseModel):
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
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.input_paths", "argparse.flag": "--input-paths"},
    )
    exclude_patterns: List[str] = Field(
        default=[],
        description=_("Paths to exclude from searching"),
        json_schema_extra={
            "pyproject.toml": "tool.unbabelizer.exclude_patterns",
            "argparse.flag": "--exclude-patterns",
        },
    )
    src_lang: str = Field(
        default="en",
        description=_("Source language code"),
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.src_lang", "argparse.flag": "--src-lang"},
    )
    dest_lang: List[str] = Field(
        description=_("Destination language code"),
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.dest_lang", "argparse.flag": "--dest-lang"},
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
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.keywords", "argparse.flag": "--keywords"},
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

    def get_translation_config(self, dest_lang_index: int) -> TranslationServiceConfig:
        """Prepare the configuration dictionary for the translation service."""
        return {
            "source": self.src_lang,
            "target": self.dest_lang[dest_lang_index],
            "api_key": self.api_key,
            "api_key_type": self.api_key_type,
            "proxies": {
                k: v
                for k, v in {
                    "http": self.http_proxy,
                    "https": self.https_proxy,
                }.items()
                if v is not None
            }
            or None,
            "model": self.model,
            "region": self.region,
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
            config_field = schema.get(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                "pyproject.toml", name
            )
            if choices is not None and not isinstance(choices, list):
                choices = [choices]  # pyright: ignore[reportUnknownVariableType]
            parser.add_argument(
                flag,  # pyright: ignore[reportArgumentType]
                help=(field.description or "")
                + " "
                + _('(overrides pyproject.toml setting: "{config_field}")').format(
                    config_field=config_field  # pyright: ignore[reportUnknownArgumentType]
                ),
                default=None,
                nargs=None if field.annotation is not list else "+",
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
