"""
streamlit_executive_logging.py
Executive Overview logging utilities.
"""

import logging
import os
from datetime import datetime
from typing import Optional

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
_logger: Optional[logging.Logger] = None


def _ensure_dir(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def get_logger(name: str = "sentinel360.executive") -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger
    _ensure_dir(_LOG_DIR)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(
            os.path.join(_LOG_DIR, "executive_overview.log"),
            encoding="utf-8",
        )
        fh.setLevel(logging.INFO)
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    _logger = logger
    return _logger


def log_event(event: str, detail: str = "") -> None:
    logger = get_logger()
    logger.info("%s | %s", event, detail)
