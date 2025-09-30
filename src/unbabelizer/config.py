import argparse
import sys
import tomllib
from pathlib import Path
from typing import Any, Dict, List

import jmespath
from pydantic import BaseModel, Field

from .log import Logger

logger = Logger()


class CliArgument(dict[str, Any]):
    pass


class Config(BaseModel):
    """unbabelizer loads configuration from pyproject.toml and command line arguments."""

    author: str = Field(
        description="Author of the project",
        json_schema_extra={"pyproject.toml": "project.authors[0].name", "argparse": "--author"},
    )
    email: str = Field(
        description="Email of the author",
        json_schema_extra={"pyproject.toml": "project.authors[0].email", "argparse": "--email"},
    )
    version: str = Field(
        description="Version of the project",
        json_schema_extra={"pyproject.toml": "project.version", "argparse": "--version"},
    )
    title: str = Field(
        description="Title of the project", json_schema_extra={"pyproject.toml": "project.name", "argparse": "--title"}
    )
    locale_dir: Path = Field(
        default=Path("locale"),
        description="Directory for locale files",
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.locale_dir", "argparse": "--locale-dir"},
    )
    input_paths: List[Path] = Field(
        default=[Path.cwd()],
        description="Paths to search for source files",
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.input_paths", "argparse": "--input-paths"},
    )
    exclude_patterns: List[str] = Field(
        default=[],
        description="Paths to exclude from searching",
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.exclude_patterns", "argparse": "--exclude-patterns"},
    )
    src_lang: str = Field(
        default="en",
        description="Source language code",
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.src_lang", "argparse": "--src-lang"},
    )
    dest_lang: List[str] = Field(
        description="Destination language code",
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.dest_lang", "argparse": "--dest-lang"},
    )
    domain: str = Field(
        default="messages",
        description="Domain for the .po files",
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.domain", "argparse": "--domain"},
    )
    mapping_file: str = Field(
        default="[python: **.py]\nencoding = utf-8\n",
        description="Content of the Babel mapping file",
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.mapping_file_content", "argparse": "--mapping-file"},
    )
    line_width: int = Field(
        default=120,
        description="Line width for .po files",
        json_schema_extra={
            "pyproject.toml": "tool.unbabelizer.line_width",
            "argparse": "--line-width",
        },
    )
    keywords: List[str] = Field(
        default=[],
        description="Additional keywords to look for in source files",
        json_schema_extra={"pyproject.toml": "tool.unbabelizer.keywords", "argparse": "--keywords"},
    )

    @classmethod
    def source_cli_args(cls, args: List[str]) -> Dict[str, Any]:
        """Parse command line arguments to create a Config instance."""
        parser = argparse.ArgumentParser(description="unbabelizer configuration")
        for name, field in cls.model_fields.items():
            schema = (  # pyright: ignore[reportUnknownVariableType]
                field.json_schema_extra  # pyright: ignore[reportUnknownMemberType]
                if isinstance(field.json_schema_extra, dict)
                else {}
            )
            flag = schema.get(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                "argparse", f"--{name.replace('_', '-')}"
            )
            parser.add_argument(
                flag,  # pyright: ignore[reportArgumentType]
                help=field.description or "",
                default=None,
                nargs=None if field.annotation is not list else "+",
                type=field.annotation if field.annotation is not None else str,
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
