"""Shared utilities for Phase 2D-9 closure and Streamlit handover."""

import hashlib
import json
import time
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs" / "decision_intelligence"
TMP_DIR = OUTPUT_DIR / "_tmp_2d9"
SCENARIO_DIR = BASE_DIR / "outputs" / "scenario_modelling"
CONFIG_DIR = BASE_DIR / "config"
DOCS_DIR = BASE_DIR / "docs"
SRC_DIR = BASE_DIR / "src"


def load_csv(name, dir_path=OUTPUT_DIR, nrows=None):
    path = dir_path / name
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, low_memory=False, on_bad_lines="skip", nrows=nrows)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def save_csv(df, name, dir_path=TMP_DIR):
    path = dir_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def atomic_move(name):
    src = TMP_DIR / name
    dst = OUTPUT_DIR / name
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.replace(dst)
    return dst


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(step, phase, outputs_dict):
    return {
        "step": step,
        "phase": phase,
        "timestamp": pd.Timestamp.now().isoformat(),
        "outputs": outputs_dict,
    }


def write_manifest(manifest, filename):
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)
    return path


def has_content(val):
    if pd.isna(val):
        return False
    return str(val).strip() not in ("", "nan", "NaN", "None", "null")


def log_progress(msg, elapsed=None):
    ts = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    if elapsed is not None:
        print(f"[{ts}] {msg} ({elapsed:.2f}s)")
    else:
        print(f"[{ts}] {msg}")
