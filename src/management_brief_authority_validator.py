"""Authority and version validation for Step 2D-7."""

import os
from management_brief_utils import load_csv, compute_sha256


def validate_authority_inputs(input_files, output_dir):
    """Validate all authoritative inputs and return register DataFrame."""
    import pandas as pd
    records = []
    for info in input_files:
        path = info["path"]
        if not os.path.exists(path):
            raise FileNotFoundError(f"Authoritative input missing: {path}")
        df = load_csv(path)
        row_count = len(df)
        col_count = len(df.columns)
        checksum = compute_sha256(path)
        frozen_checksum = info.get("frozen_checksum", "")
        match = checksum == frozen_checksum if frozen_checksum else True
        records.append({
            "file_name": info["name"],
            "file_path": path,
            "source_phase": info["phase"],
            "row_count": row_count,
            "column_count": col_count,
            "checksum": checksum,
            "frozen_checksum": frozen_checksum,
            "checksum_match": match,
            "authoritative_status": "Authoritative" if match else "Integrity Failure",
            "management_brief_use_status": "Ready" if match else "Blocked",
            "superseded_flag": info.get("superseded", False),
            "governance_note": "Validated for 2D-7 use" if match else "Checksum mismatch - STOP"
        })
    return pd.DataFrame(records)
