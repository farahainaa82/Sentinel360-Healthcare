"""Shared utilities for Phase 2D-8 Decision Intelligence Validation."""

import hashlib
import json
import os
from pathlib import Path

import pandas as pd

BASE_DIR = Path(os.path.dirname(os.path.dirname(__file__)))
OUTPUT_DIR = BASE_DIR / "outputs" / "decision_intelligence"
CONFIG_DIR = BASE_DIR / "config"

EXPECTED_PACKAGES = 646


def load_register(name):
    """Load a 2D-7 or 2D-8 CSV register from the outputs directory."""
    path = OUTPUT_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False, on_bad_lines="skip")


def load_config(name):
    """Load a configuration CSV from the config directory."""
    path = CONFIG_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def compute_sha256(file_path):
    """Compute SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_write_csv(df, file_name):
    """Write DataFrame to CSV atomically via temp file."""
    out_path = OUTPUT_DIR / file_name
    tmp_path = out_path.with_suffix(".tmp")
    df.to_csv(tmp_path, index=False)
    tmp_path.replace(out_path)
    return out_path


def build_manifest(step, mode, outputs_dict):
    """Build a manifest dictionary for a validation step."""
    return {
        "step": step,
        "mode": mode,
        "timestamp": pd.Timestamp.now().isoformat(),
        "status": "COMPLETE",
        "outputs": outputs_dict,
    }


def _convert_for_json(obj):
    """Recursively convert numpy types to native Python types for JSON serialization."""
    import numpy as np
    if isinstance(obj, dict):
        return {k: _convert_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_for_json(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def write_manifest(manifest, file_name):
    """Write manifest JSON to outputs directory."""
    out_path = OUTPUT_DIR / file_name
    tmp_path = out_path.with_suffix(".tmp")
    manifest = _convert_for_json(manifest)
    with open(tmp_path, "w") as f:
        json.dump(manifest, f, indent=2)
    tmp_path.replace(out_path)
    return out_path


def validation_outcome(severity_counts):
    """
    Determine validation outcome based on severity counts.
    Returns one of the governed outcome levels.
    """
    if severity_counts.get("Critical", 0) > 0:
        return "Not Suitable"
    if severity_counts.get("High", 0) > 0:
        return "Requires Focused Correction"
    if severity_counts.get("Medium", 0) > 0:
        return "Validated with Conditions"
    if severity_counts.get("Low", 0) > 0:
        return "Validated with Conditions"
    return "Validated for Streamlit Handover"


def correction_class(outcome):
    """Map validation outcome to correction classification."""
    mapping = {
        "Validated for Streamlit Handover": "No Correction Required",
        "Validated with Conditions": "Documentation Clarification",
        "Requires Focused Correction": "Mapping Correction",
        "Requires Source Data Review": "Source Data Review",
        "Requires Upstream Analytical Review": "Upstream Analytical Review",
        "Requires Governance Review": "Governance Review",
        "Not Suitable": "Governance Review",
    }
    return mapping.get(outcome, "No Correction Required")
