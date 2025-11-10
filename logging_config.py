"""Logging configuration for Vanna AI application."""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Final, Optional

# Constants
LOGGER_NAME: Final[str] = "vanna_app"
DEFAULT_LOG_LEVEL: Final[str] = "INFO"
DEFAULT_LOG_FILE: Final[str] = "logs/vanna_app.log"
MB_TO_BYTES: Final[int] = 1024 * 1024
DEFAULT_MAX_BYTES: Final[int] = 10 * MB_TO_BYTES  # 10MB
DEFAULT_BACKUP_COUNT: Final[int] = 5

# Log format templates
DETAILED_FORMAT: Final[str] = (
    "%(asctime)s - %(name)s - %(levelname)s - "
    "[%(filename)s:%(lineno)d] - %(message)s"
)
CONSOLE_FORMAT: Final[str] = "%(asctime)s - %(levelname)s - %(message)s"
DETAILED_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"
CONSOLE_DATE_FORMAT: Final[str] = "%H:%M:%S"


def setup_logging(
    log_level: Optional[str] = None,
    log_file: str = DEFAULT_LOG_FILE,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> logging.Logger:
    """
    Configure application-wide logging with both file and console handlers.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured logger instance
    """
    # Get log level from environment or use provided value or default to INFO
    log_level = log_level or os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()

    # Create logs directory if it doesn't exist
    log_dir = Path(log_file).parent
    log_dir.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(getattr(logging, log_level))

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt=DETAILED_FORMAT,
        datefmt=DETAILED_DATE_FORMAT,
    )

    console_formatter = logging.Formatter(
        fmt=CONSOLE_FORMAT,
        datefmt=CONSOLE_DATE_FORMAT,
    )

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Log initial setup message
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance. If the main logger hasn't been configured,
    this will configure it with default settings.

    Args:
        name: Optional name for the logger. If provided, creates hierarchical
              logger (e.g., 'vanna_app.config'). Defaults to root logger.

    Returns:
        Logger instance
    """
    if name:
        # Create hierarchical logger for better organization
        return logging.getLogger(f"{LOGGER_NAME}.{name}")

    logger = logging.getLogger(LOGGER_NAME)

    # If logger hasn't been configured yet, configure it with defaults
    if not logger.handlers:
        setup_logging()

    return logger
