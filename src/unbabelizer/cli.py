import sys
import traceback

from pydantic import ValidationError

from .translation import setup_translation

setup_translation()

from .app import UnbabelizerApp
from .config import Config, logger
from .types.subcommand import SubCommands


def main(args: list[str] | None = None):
    """Entry point for the unbabelizer CLI application."""
    try:
        config = Config.build(args)
        logger.info("Running unbabelizerApp with config:", extra={"context": "cli.main", "config": config})
        # Non-interactive (headless) mode: run non-UI workflow actions and exit
        if config.noninteractive:
            logger.info("Running in non-interactive mode, executing headless workflow.", extra={"context": "cli.main"})
            for idx, lang in enumerate(config.dest_lang):
                logger.info(
                    "Starting headless workflow for language", extra={"context": "cli.headless", "language": lang}
                )

                # Extraction
                if config.is_workflow_action_enabled(SubCommands.EXTRACT_UPDATE, True):
                    UnbabelizerApp.run_action_extract_and_update(
                        logger, config, idx, config.potfile_path, config.get_pofile_path(idx)
                    )

                # Compile
                if config.is_workflow_action_enabled(SubCommands.COMPILE, True):
                    UnbabelizerApp.run_action_compile_translations(logger, config)

                # Inform about skipped UI-required actions
                if config.is_workflow_action_enabled(SubCommands.TRANSLATE, False):
                    logger.warning(
                        "Translate action requires interactive UI and was skipped in non-interactive mode",
                        extra={"context": "cli.headless", "language": lang},
                    )
                if config.is_workflow_action_enabled(SubCommands.REVIEW, False):
                    logger.warning(
                        "Review action requires interactive UI and was skipped in non-interactive mode",
                        extra={"context": "cli.headless", "language": lang},
                    )

            logger.info("Headless workflow completed.", extra={"context": "cli.main"})
            return

        app = UnbabelizerApp(config, logger)
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
