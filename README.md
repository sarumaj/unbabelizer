<!-- markdownlint-disable MD041 -->
[![release](https://github.com/sarumaj/unbabelizer/actions/workflows/release.yml/badge.svg)](https://github.com/sarumaj/unbabelizer/actions/workflows/release.yml)
[![GitHub Release](https://img.shields.io/github/v/release/sarumaj/unbabelizer?logo=github)](https://github.com/sarumaj/unbabelizer/releases/latest)
[![Libraries.io dependency status for GitHub repo](https://img.shields.io/librariesio/github/sarumaj/unbabelizer)](https://github.com/sarumaj/unbabelizer/blob/main/pyproject.toml)

---
<!-- markdownlint-enable MD041 -->
# unbabelizer

`unbabelizer` is an interactive CLI and TUI (Text User Interface) tool for
managing gettext `.po` translation files.
It streamlines the localization workflow for Python projects by automating
extraction, translation, review, and compilation of translation files.

## Purpose

The main goal of `unbabelizer` is to simplify and automate the process of
internationalizing Python applications.
It provides a guided interface for developers and translators to:

- Extract translatable strings from source code using `babel`.
- Automatically translate `.po` files using `Google Translate`.
- Review and edit translations interactively.
- Compile `.po` files into binary `.mo` files for deployment.
- Manage multiple languages and domains with ease.
- Integrate seamlessly with Babel and polib for robust gettext support.

## Demo

[![!["Asciinema Demo"](https://github.com/sarumaj/unbabelizer/blob/main/docs/thumbnail.png?raw=true)](docs/thumbnail.png)](https://asciinema.org/a/ZKhYGHJ5AIi7MwEYCpWD64oFG)

The app is itself available in German language. Simply run

```shell
LANG=de unbabelizer
```

to execute the app in German language.

## Features

- **Interactive TUI:** Edit and review translations in a modern terminal UI
powered by [Textual](https://github.com/Textualize/textual).
- **Automated Extraction:** Find and extract translatable strings from your
codebase using Babel.
- **Batch Translation:** Translate `.po` files automatically via Google Translate,
with support for multiple target languages.
- **Review Workflow:** Step through translations, edit entries, and mark reviewed
items.
- **Compilation:** Compile `.po` files to `.mo` for production use.
- **Configurable:** Control all aspects via `pyproject.toml` or CLI arguments.
- **Exclusion Patterns:** Skip files or directories using glob patterns.
- **Custom Mapping:** Provide custom Babel mapping for source file types.
- **Logging:** Detailed logging for troubleshooting and auditing translation changes.

## Installation

You can install the package via pip:

```shell
pip install unbabelizer
```

## Usage

Execute in a directory with a `pyproject.toml` config file:

```shell
unbabelizer
```

The configuration section in `pyproject.toml` might look as follows:

```toml
[tool.unbabelizer]
# List of destination languages (e.g., German)
dest_lang = ["de"]

# Paths to search for source files
input_paths = ["src"]

# Directory for locale files
locale_dir = "src/unbabelizer/locales"

# Source language code
src_lang = "en"

# Domain for the .po files (default: "messages")
domain = "messages"

# Patterns to exclude from searching (optional)
exclude_patterns = ["tests/*", "docs/*"]

# Content of the Babel mapping file (optional)
mapping_file_content = """
[python: **.py]
encoding = utf-8
"""

# Line width for .po files (optional, default: 120)
line_width = 120
```

You can also override these settings using CLI arguments:

```shell
unbabelizer \
  --dest-lang de \
  --input-paths src \
  --locale-dir src/unbabelizer/locales \
  --src-lang en \
  --domain messages \
  --exclude-patterns tests/* docs/* \
  --mapping-file "~/mapping_file.txt" \
  --line-width 120
```

- `--dest-lang`: Destination language(s) (repeat or use multiple values)
- `--input-paths`: Source file paths (repeat or use multiple values)
- `--locale-dir`: Locale directory
- `--src-lang`: Source language code
- `--domain`: .po file domain
- `--exclude-patterns`: Patterns to exclude (optional)
- `--mapping-file`: Babel mapping file (optional)
- `--line-width`: Line width for .po files (optional)

Settings from the CLI override those in `pyproject.toml`.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.
