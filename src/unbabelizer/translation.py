import locale
import sys
from collections import Counter
from gettext import translation
from pathlib import Path
from typing import Sequence

from babel import Locale, UnknownLocaleError


def determine_most_common_locale_separator(locales: Sequence[str]) -> str:
    """Determine the most common locale separator in a list of locales.
    Args:
        locales (Sequence[str]): A list of locale strings.
    Returns:
        str: The most common locale separator ("-" or "_"). If there is a tie or
             no separators found, returns "_".
    """
    counter = Counter(
        sep
        for locale in locales
        for sep in ("-" if "-" in locale else "_" if "_" in locale else None,)
        if sep is not None
    )

    results = counter.most_common(2)
    if not results:
        return "_"

    if len(results) == 1:
        return results[0][0]

    if results[0][1] == results[1][1]:
        return "_"

    return results[0][0]


def get_display_name_for_lang_code(lang_code: str) -> str:
    """Resolve a language code to its canonical form using Babel.

    Args:
        lang_code (str): The input language code to resolve.

    Returns:
        str: The resolved canonical language code. If resolution fails, returns the original lang_code.
    """
    try:
        return (
            Locale.parse(lang_code, sep=determine_most_common_locale_separator([lang_code])).get_display_name(
                locale.getdefaultlocale()[0]
            )
            or lang_code
        )
    except:
        return lang_code


def setup_translation():
    """Set up the translation system based on the user's locale."""
    locale.setlocale(locale.LC_ALL)
    try:
        lang = locale.getdefaultlocale()[0] or "en_US"
        lang = Locale.parse(lang, sep=determine_most_common_locale_separator([lang])).language or "en"
    except (locale.Error, UnknownLocaleError) as e:
        print(f"Warning: Could not determine system locale, defaulting to English: {e}", file=sys.stderr)
        lang = "en"

    tr = translation(
        domain="messages",
        localedir=(Path(__file__).parent / "locales").resolve(),
        languages=[lang],
        fallback=True,
    )
    tr.install(names=["ngettext"])
