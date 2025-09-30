import gettext
import sys
import traceback
from gettext import gettext as _
from pathlib import Path

from .app import UnbabelizerApp
from .config import Config, logger

gettext.bindtextdomain(
    "messages",
    (Path(__file__).parent / "locales").resolve(),
)


def main(args: list[str] | None = None):
    """Entry point for the unbabelizer CLI application."""
    try:
        config = Config.build(args)
        logger.info("Running unbabelizerApp with config:", extra={"context": "cli.main", "config": config})
        app = UnbabelizerApp(config)
        logger.info("Starting unbabelizerApp...")
        app.run()
        logger.info("unbabelizerApp has terminated gracefully.")
    except Exception as e:
        logger.error(
            "An unhandled exception occurred: %s",
            str(e),
            extra={"context": "cli.main", "trace": traceback.format_exc()},
        )
        sys.exit(1)
