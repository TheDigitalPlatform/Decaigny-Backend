import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import settings

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def setup_logging() -> None:
    """
    Configure application logging for the `app` package.
    Streams logs to stdout and writes to LOG_FILE with rotation.
    """
    global _configured
    if _configured:
        return

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    app_logger = logging.getLogger("app")
    app_logger.setLevel(log_level)
    app_logger.propagate = False

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    app_logger.addHandler(stream_handler)

    log_file = Path(settings.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    app_logger.addHandler(file_handler)

    _configured = True
