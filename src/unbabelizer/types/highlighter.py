import re
from typing import List

from rich.highlighter import Highlighter
from rich.style import Style
from rich.text import Text
from rich.theme import Theme


class RegexHighlighter(Highlighter):
    """A custom highlighter that does nothing."""

    highlights: List[str]
    base_style: str = ""
    theme: Theme = Theme({})
    default_style: Style = Style(bold=True, color="magenta")

    def __init__(self):
        """Initialize the RegexHighlighter."""
        super().__init__()
        self.theme.styles.update(
            {
                style_name: self.theme.styles.get(style_name, self.default_style)
                for pattern in self.highlights
                for group_name in re.compile(pattern).groupindex
                for style_name in (f"{self.base_style.rstrip('.')}.{group_name}" if self.base_style else group_name,)
            }
        )

    def highlight(self, text: Text):
        """Return the text unchanged.

        Args:
            text (Text): The text to highlight.
        """
        theme_styles = self.theme.styles if self.theme else {}
        for highlight in self.highlights:
            pattern = re.compile(highlight)
            style_name = next(iter(pattern.groupindex), None)
            if style_name is None:
                continue

            style_name = f"{self.base_style.rstrip(".")}.{style_name}" if self.base_style else style_name
            for match in pattern.finditer(text.plain):
                text.stylize(theme_styles.get(style_name, self.default_style), match.start(), match.end())


class FStringHighlighter(RegexHighlighter):
    """A highlighter for f-strings in Python."""

    highlights = [
        r"(?P<expression>\{[^\{\}]+\})",  # Highlight expressions within {}
        r"(?P<escape>\\{1,2}.)",  # Highlight escape sequences
    ]
    base_style = "fstring."
    theme = Theme(
        {
            "fstring.expression": Style(bold=True, color="bright_blue"),
            "fstring.escape": Style(bold=True, color="magenta"),
        }
    )


class FnmatchHighlighter(RegexHighlighter):
    """A highlighter for fnmatch patterns."""

    highlights = [
        r"(?P<wildcard>\*)",  # Highlight wildcard *
        r"(?P<single_char>\?)",  # Highlight single character ?
        r"(?P<char_class>\[[^\]]+\])",  # Highlight character classes []
    ]
    base_style = "fnmatch."
    theme = Theme(
        {
            "fnmatch.wildcard": Style(bold=True, color="bright_green"),
            "fnmatch.single_char": Style(bold=True, color="bright_green"),
            "fnmatch.char_class": Style(bold=True, color="cyan"),
        }
    )
