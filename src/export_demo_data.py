"""
Export Demo Data — Sentinel360 Healthcare

Reproducibly generates synthetic operational source data and exports it as
UTF-8 CSV files into data/demo/. Also creates a generation manifest.

This module does NOT calculate KPI values, statuses, forecasts,
recommendations, or any analytical outputs.

Usage:
    python src/export_demo_data.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# Ensure src/ is importable when running from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _PROJECT_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from demo_data_generator import SyntheticHospitalDataGenerator
from demo_generation_config import get_default_config

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXPECTED_DATASETS: List[str] = [
    "hospital_master",
    "department_master",
    "staff_role_master",
    "staff_master",
    "staff_roster",
    "staff_attendance",
    "staffing_requirement",
    "patient_encounters",
    "patient_queue_records",
    "bed_capacity_records",
    "patient_complaints",
    "patient_surveys",
    "service_schedule",
]

DEFAULT_OUTPUT_DIR: Path = _PROJECT_ROOT / "data" / "demo"

# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------


def build_demo_datasets(seed: int = 360) -> Dict[str, pd.DataFrame]:
    """
    Instantiate the generator and produce all 13 source datasets.

    Parameters
    ----------
    seed : int
        Deterministic random seed (default 360, matching Step 2A).

    Returns
    -------
    Dict[str, pd.DataFrame]
        Dictionary of generated DataFrames.
    """
    config = get_default_config()
    config.seed = seed
    generator = SyntheticHospitalDataGenerator(config=config, seed=seed)
    data = generator.generate_all()
    return data


def validate_export_schemas(data: Dict[str, pd.DataFrame]) -> None:
    """
    Validate that every expected dataset is present and contains approved columns.

    Raises
    ------
    RuntimeError
        If validation fails.
    """
    missing_datasets = set(EXPECTED_DATASETS) - set(data.keys())
    if missing_datasets:
        raise RuntimeError(f"Validation failed: missing datasets {missing_datasets}")

    unexpected = set(data.keys()) - set(EXPECTED_DATASETS)
    if unexpected:
        raise RuntimeError(f"Validation failed: unexpected datasets {unexpected}")

    # Column-order validation: ensure DataFrames use the generator's approved order
    from demo_data_generator import (
        HOSPITAL_MASTER_COLS,
        DEPARTMENT_MASTER_COLS,
        STAFF_ROLE_MASTER_COLS,
        STAFF_MASTER_COLS,
        STAFF_ROSTER_COLS,
        STAFF_ATTENDANCE_COLS,
        STAFFING_REQUIREMENT_COLS,
        PATIENT_ENCOUNTER_COLS,
        PATIENT_QUEUE_RECORD_COLS,
        BED_CAPACITY_RECORD_COLS,
        PATIENT_COMPLAINT_COLS,
        PATIENT_SURVEY_COLS,
        SERVICE_SCHEDULE_COLS,
    )

    schema_map = {
        "hospital_master": HOSPITAL_MASTER_COLS,
        "department_master": DEPARTMENT_MASTER_COLS,
        "staff_role_master": STAFF_ROLE_MASTER_COLS,
        "staff_master": STAFF_MASTER_COLS,
        "staff_roster": STAFF_ROSTER_COLS,
        "staff_attendance": STAFF_ATTENDANCE_COLS,
        "staffing_requirement": STAFFING_REQUIREMENT_COLS,
        "patient_encounters": PATIENT_ENCOUNTER_COLS,
        "patient_queue_records": PATIENT_QUEUE_RECORD_COLS,
        "bed_capacity_records": BED_CAPACITY_RECORD_COLS,
        "patient_complaints": PATIENT_COMPLAINT_COLS,
        "patient_surveys": PATIENT_SURVEY_COLS,
        "service_schedule": SERVICE_SCHEDULE_COLS,
    }

    for name, df in data.items():
        expected_cols = schema_map[name]
        actual_cols = list(df.columns)
        if actual_cols != expected_cols:
            diff = [c for c in expected_cols if c not in actual_cols] + [c for c in actual_cols if c not in expected_cols]
            raise RuntimeError(f"Validation failed: column mismatch in {name}. Differences: {diff}")


def calculate_file_checksum(filepath: Path) -> str:
    """Return SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def build_generation_manifest(
    data: Dict[str, pd.DataFrame],
    output_dir: Path,
    seed: int,
) -> Dict[str, Any]:
    """
    Build the generation manifest dictionary.

    Parameters
    ----------
    data : Dict[str, pd.DataFrame]
        Exported datasets.
    output_dir : Path
        Directory where CSV files were written.
    seed : int
        Random seed used.

    Returns
    -------
    Dict[str, Any]
        Manifest contents.
    """
    config = get_default_config()
    row_counts = {name: len(df) for name, df in data.items()}

    date_ranges: Dict[str, Dict[str, Optional[str]]] = {}
    for name, df in data.items():
        date_col = None
        for c in [
            "effective_from",
            "roster_date",
            "attendance_date",
            "encounter_date",
            "queue_date",
            "record_date",
            "complaint_received_date",
            "survey_date",
            "service_date",
            "requirement_date",
        ]:
            if c in df.columns:
                date_col = c
                break
        if date_col:
            date_ranges[name] = {
                "earliest": str(df[date_col].min()),
                "latest": str(df[date_col].max()),
            }
        else:
            date_ranges[name] = {"earliest": None, "latest": None}

    file_checksums: Dict[str, str] = {}
    file_names: Dict[str, str] = {}
    for name in EXPECTED_DATASETS:
        filepath = output_dir / f"{name}.csv"
        file_names[name] = filepath.name
        if filepath.exists():
            file_checksums[name] = calculate_file_checksum(filepath)
        else:
            file_checksums[name] = ""

    import platform

    manifest: Dict[str, Any] = {
        "generation_run_id": f"RUN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{seed}",
        "generator_name": "SyntheticHospitalDataGenerator",
        "generator_version": "1.0.0-step2b",
        "generation_datetime": datetime.now().isoformat(),
        "random_seed": seed,
        "configured_start_date": str(config.start_date),
        "configured_end_date": str(config.end_date),
        "number_of_hospitals": 1,
        "demonstration_hospital_id": config.hospital["hospital_id"],
        "demonstration_hospital_name": config.hospital["hospital_name"],
        "dataset_count": len(EXPECTED_DATASETS),
        "generated_dataset_names": EXPECTED_DATASETS,
        "row_count_by_dataset": row_counts,
        "date_range_by_dataset": date_ranges,
        "storyline_phase_definitions": config.storyline_phases,
        "defect_injection_enabled": any(config.defects.values()),
        "defect_types_enabled": [k for k, v in config.defects.items() if v],
        "configuration_source": "src/demo_generation_config.py",
        "source_schema_reference": "docs/data_dictionary_source.md",
        "python_version": platform.python_version(),
        "pandas_version": pd.__version__,
        "numpy_version": __import__("numpy").__version__,
        "output_directory": str(output_dir.resolve()),
        "file_name_by_dataset": file_names,
        "file_checksum_by_dataset": file_checksums,
        "export_status": "Success",
        "known_limitations": [
            "Single hospital only; multi-hospital support is logical but not yet exercised.",
            "Queue records are daily aggregates; shift-level aggregation not yet implemented.",
            "Survey scale defaults to 5-point; mixed-scale support requires additional metadata.",
            "Staff replacement references are symbolic; no additional roster records are generated for replacements.",
        ],
    }
    return manifest


def export_demo_datasets(
    data: Dict[str, pd.DataFrame],
    output_dir: Path,
) -> Dict[str, Path]:
    """
    Write each DataFrame to a UTF-8 CSV file preserving column order.

    Parameters
    ----------
    data : Dict[str, pd.DataFrame]
        Datasets to export.
    output_dir : Path
        Target directory.

    Returns
    -------
    Dict[str, Path]
        Mapping of dataset name to exported file path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    exported: Dict[str, Path] = {}
    for name in EXPECTED_DATASETS:
        df = data[name]
        filepath = output_dir / f"{name}.csv"
        df.to_csv(filepath, index=False, encoding="utf-8")
        exported[name] = filepath
    return exported


def main(output_dir: Optional[Path] = None, seed: int = 360) -> Dict[str, Any]:
    """
    Full export pipeline: generate, validate, export, manifest.

    Parameters
    ----------
    output_dir : Path, optional
        Directory for exported files. Defaults to data/demo/.
    seed : int
        Deterministic seed.

    Returns
    -------
    Dict[str, Any]
        Export result summary.
    """
    out = output_dir or DEFAULT_OUTPUT_DIR
    print("[export_demo_data] Building demo datasets...")
    data = build_demo_datasets(seed=seed)
    print("[export_demo_data] Validating schemas...")
    validate_export_schemas(data)
    print("[export_demo_data] Exporting CSV files...")
    export_demo_datasets(data, out)
    print("[export_demo_data] Building generation manifest...")
    manifest = build_generation_manifest(data, out, seed=seed)
    manifest_path = out / "generation_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)
    print(f"[export_demo_data] Manifest written to {manifest_path}")
    print("[export_demo_data] Export complete.")
    return {
        "status": "success",
        "output_directory": str(out.resolve()),
        "datasets_exported": list(data.keys()),
        "manifest": manifest,
    }


if __name__ == "__main__":
    main()
