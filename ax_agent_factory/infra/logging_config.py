"""Logging configuration helper for AX Agent Factory."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    level: int = logging.INFO,
    log_file: str = "logs/app.log",
    max_bytes: int = 1_000_000,
    backup_count: int = 3,
) -> None:
    """Initialize root logger with console and rotating file handlers."""
    root_logger = logging.getLogger()
    if getattr(root_logger, "_ax_logging_configured", False):
        return

    root_logger.setLevel(level)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(log_path, maxBytes=max_bytes, backupCount=backup_count)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    root_logger._ax_logging_configured = True  # type: ignore[attr-defined]
