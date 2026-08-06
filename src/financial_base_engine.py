"""
Financial Base Engine for Phase 2C-3.

Provides shared utilities for:
- CSV loading with validation
- SHA-256 checksums
- Logging
- Temporary directory management
- Atomic file moves
- JSON parsing of assumption values
"""

import os
import sys
import json
import hashlib
import logging
import tempfile
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, List

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "analytical")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs", "financial_impact")
TMP_DIR = os.path.join(OUTPUT_DIR, "_tmp_2c3")

os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(os.path.join(OUTPUT_DIR, "step_2c3.log"), encoding="utf-8")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(fh)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(ch)
    return logger


def compute_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_csv(path: str, required: bool = True) -> Optional[pd.DataFrame]:
    if not os.path.exists(path):
        if required:
            raise FileNotFoundError(f"Required file not found: {path}")
        return pd.DataFrame()
    if os.path.getsize(path) <= 2:
        if required:
            return pd.DataFrame()
        return pd.DataFrame()
    return pd.read_csv(path)


def safe_write_csv(df: pd.DataFrame, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def atomic_move(src: str, dst: str):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)


def parse_assumption_values_json(val) -> Dict[str, Any]:
    if pd.isna(val) or val == "{}" or val == "":
        return {}
    try:
        return json.loads(val)
    except Exception:
        return {}


class FinancialBaseEngine:
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or setup_logger("financial_base")
        self.tmp_dir = TMP_DIR
        self.output_dir = OUTPUT_DIR
        self.data_dir = DATA_DIR
        self.config_dir = CONFIG_DIR

    def log(self, msg: str, level: str = "info"):
        if level == "error":
            self.logger.error(msg)
        elif level == "warning":
            self.logger.warning(msg)
        else:
            self.logger.info(msg)

    def load_config(self, filename: str) -> pd.DataFrame:
        path = os.path.join(self.config_dir, filename)
        return load_csv(path, required=True)

    def load_data(self, filename: str) -> pd.DataFrame:
        path = os.path.join(self.data_dir, filename)
        return load_csv(path, required=True)

    def write_output(self, df: pd.DataFrame, filename: str):
        path = os.path.join(self.tmp_dir, filename)
        safe_write_csv(df, path)
        self.log(f"Written {filename}: {len(df)} rows")

    def move_to_final(self, filename: str):
        src = os.path.join(self.tmp_dir, filename)
        dst = os.path.join(self.output_dir, filename)
        if os.path.exists(dst):
            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            backup = os.path.join(self.output_dir, f"{filename}.{ts}.backup")
            shutil.move(dst, backup)
        atomic_move(src, dst)
        self.log(f"Moved {filename} to final")
