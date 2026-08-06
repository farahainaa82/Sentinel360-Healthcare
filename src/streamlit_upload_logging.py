"""Upload logging module for local application log output."""

import os
import logging
from datetime import datetime
from typing import Optional


LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "streamlit_upload.log")


def _ensure_dir(path: str) -> None:
    """Ensure directory exists for log file."""
    dir_path = os.path.dirname(path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)


def get_logger(name: str = "streamlit_upload") -> logging.Logger:
    """Get configured logger for upload module."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    _ensure_dir(LOG_FILE_PATH)
    fh = logging.FileHandler(LOG_FILE_PATH, mode="a")
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def log_event(message: str, level: str = "info") -> None:
    """Log a single event."""
    logger = get_logger()
    if level.lower() == "debug":
        logger.debug(message)
    elif level.lower() == "warning":
        logger.warning(message)
    elif level.lower() == "error":
        logger.error(message)
    else:
        logger.info(message)


def log_exception(message: str) -> None:
    """Log an exception with traceback."""
    logger = get_logger()
    logger.exception(message)
