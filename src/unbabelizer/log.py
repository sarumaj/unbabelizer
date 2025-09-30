import logging
import logging.handlers
from pathlib import Path
from typing import Any

from .types import SingletonType


class Logger(logging.LoggerAdapter[Any], metaclass=SingletonType):
    """A singleton logger class for the application."""

    def __init__(self, log_name: str = "unbabelizer", log_level: int = logging.DEBUG):
        logger = logging.getLogger(log_name)
        logger.setLevel(log_level)

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        log_dir = Path.home() / ".unbabelizer"
        log_dir.mkdir(parents=True, exist_ok=True)

        fh = logging.handlers.RotatingFileHandler(
            log_dir / "unbabelizer.log",
            maxBytes=20 * 1024**2,  # 20 MB
            backupCount=1,
        )
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        super().__init__(logger)

    @property
    def log_path(self) -> Path | None:
        """Get the path to the log file."""
        handlers = self.logger.handlers
        for handler in handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                return Path(handler.baseFilename)
        return Path()

    def process(self, msg: str, kwargs: Any):
        if "extra" in kwargs:
            msg = f"{msg} - {str(kwargs['extra'])}"
        return msg, kwargs
