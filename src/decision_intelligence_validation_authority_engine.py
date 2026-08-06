"""Authority Validation Engine for 2D-8.

Validates checksums, file existence, and readability of frozen 2D-7 outputs.
"""

import os

import pandas as pd

from decision_intelligence_validation_utils import (
    OUTPUT_DIR,
    compute_sha256,
    load_register,
)


def validate(manifest_path="step_2d7_manifest.json"):
    """Run authority validation against frozen 2D-7 manifest."""
    manifest_file = OUTPUT_DIR / manifest_path
    if not manifest_file.exists():
        return pd.DataFrame({
            "validation_id": ["VA-AUTH-001"],
            "check": ["manifest_exists"],
            "status": ["FAIL"],
            "detail": ["2D-7 manifest not found"],
        })

    import json
    with open(manifest_file, "r") as f:
        manifest = json.load(f)

    rows = []
    for file_name, meta in manifest.get("outputs", {}).items():
        file_path = OUTPUT_DIR / file_name
        exists = file_path.exists()
        readable = os.access(file_path, os.R_OK) if exists else False
        expected_checksum = meta.get("checksum", "")
        actual_checksum = compute_sha256(file_path) if exists else ""
        checksum_match = actual_checksum == expected_checksum if exists else False

        rows.append({
            "validation_id": f"VA-AUTH-{len(rows)+1:03d}",
            "file_name": file_name,
            "expected_checksum": expected_checksum,
            "actual_checksum": actual_checksum,
            "exists": exists,
            "readable": readable,
            "checksum_match": checksum_match,
            "expected_rows": meta.get("rows", 0),
            "expected_columns": meta.get("columns", 0),
            "status": "PASS" if (exists and readable and checksum_match) else "FAIL",
        })

    return pd.DataFrame(rows)


def build_register(manifest_path="step_2d7_manifest.json"):
    """Build the authority validation register."""
    return validate(manifest_path)


def get_required_columns():
    return [
        "validation_id", "file_name", "expected_checksum", "actual_checksum",
        "exists", "readable", "checksum_match", "expected_rows",
        "expected_columns", "status",
    ]
