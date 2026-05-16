"""Logging configuration for the Wealth Advisor Assistant."""

import logging
import sys
from datetime import datetime


def setup_logger(name: str = "wealth_advisor", log_file: str = "system.log") -> logging.Logger:
    """
    Configure logging to both console and file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers
    logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Create default logger
logger = setup_logger()