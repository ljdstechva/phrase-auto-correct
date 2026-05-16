"""Local logging setup."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(project_root: Path, debug: bool) -> logging.Logger:
    """Configure local logs without recording selected user text."""

    log_dir = project_root / "sources" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "app.log"

    level = logging.DEBUG if debug else logging.INFO
    logger = logging.getLogger("phrase_auto_correct")
    logger.setLevel(level)
    logger.propagate = False

    if not logger.handlers:
        handler = RotatingFileHandler(
            log_path,
            maxBytes=512_000,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s: %(message)s"
            )
        )
        logger.addHandler(handler)

    logger.debug("Logging initialized")
    return logger
