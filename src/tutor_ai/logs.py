import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGGER_NAME = "tutor_ai"
FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def setup_logging(log_file: str) -> None:
    path = Path(log_file).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter(FORMAT))

    logger = logging.getLogger(LOGGER_NAME)
    for old in [h for h in logger.handlers if isinstance(h, RotatingFileHandler)]:
        logger.removeHandler(old)
        old.close()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
