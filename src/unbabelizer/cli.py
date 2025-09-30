import gettext
import sys
import traceback
from gettext import gettext as _
from pathlib import Path

from pydantic import ValidationError

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
    except ValidationError as ve:
        logger.error(
            "Configuration validation error",
            extra={
                "context": "cli.main",
                "errors": ve.errors(),
                "trace": traceback.format_exc(),
                "exception": str(ve),
            },
        )
        print("Configuration Error:", file=sys.stderr)
        for err in ve.errors():
            print(
                ' - invalid field: "{field}", reason: "{reason}"'.format(
                    field=".".join(str(l) for l in err.get("loc", [])),
                    reason=err.get("msg", ""),
                ),
                file=sys.stderr,
            )
        sys.exit(1)

    except Exception as e:
        logger.critical(
            "An unhandled exception occurred: %s",
            str(e),
            extra={"context": "cli.main", "trace": traceback.format_exc()},
        )
        print(
            "An unexpected error occurred: {error}. Check details in {log_path}.".format(
                error=str(e), log_path=logger.log_path
            ),
            file=sys.stderr,
        )
        sys.exit(2)
