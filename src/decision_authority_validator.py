"""
Decision Authority Validator for Phase 2D-1.

Verifies all authoritative upstream inputs before integration.
"""

import os
import pandas as pd
import hashlib
from typing import Dict, List, Tuple


class DecisionAuthorityValidator:
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.errors = []
        self.warnings = []

    def compute_sha256(self, filepath: str) -> str:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def verify_files(self, file_specs: List[dict]) -> pd.DataFrame:
        """
        file_specs: list of dicts with keys:
            name, path, source_phase, frozen_checksum (optional)
        """
        records = []
        all_ok = True

        for spec in file_specs:
            name = spec["name"]
            path = spec["path"]
            phase = spec.get("source_phase", "")
            frozen_checksum = spec.get("frozen_checksum", "")

            if not os.path.exists(path):
                self.errors.append(f"MISSING: {name} at {path}")
                records.append({
                    "file_name": name, "file_path": path, "source_phase": phase,
                    "row_count": 0, "column_count": 0, "checksum": "",
                    "frozen_checksum": frozen_checksum, "checksum_match": False,
                    "authoritative_status": "Missing", "integration_use_status": "Blocked",
                    "governance_note": "File not found",
                })
                all_ok = False
                continue

            try:
                df = pd.read_csv(path)
                row_count = len(df)
                col_count = len(df.columns)
                checksum = self.compute_sha256(path)
                match = (checksum == frozen_checksum) if frozen_checksum else True
                if not match and frozen_checksum:
                    self.errors.append(f"CHECKSUM MISMATCH: {name}")
                    all_ok = False

                status = "Authoritative" if match else "Checksum Failed"
                use_status = "Include" if match else "Blocked"

                records.append({
                    "file_name": name, "file_path": path, "source_phase": phase,
                    "row_count": row_count, "column_count": col_count,
                    "checksum": checksum, "frozen_checksum": frozen_checksum,
                    "checksum_match": match, "authoritative_status": status,
                    "integration_use_status": use_status,
                    "governance_note": "" if match else "Checksum mismatch — frozen file may have been modified",
                })
            except Exception as e:
                self.errors.append(f"READ ERROR: {name}: {e}")
                all_ok = False
                records.append({
                    "file_name": name, "file_path": path, "source_phase": phase,
                    "row_count": 0, "column_count": 0, "checksum": "",
                    "frozen_checksum": frozen_checksum, "checksum_match": False,
                    "authoritative_status": "Unreadable", "integration_use_status": "Blocked",
                    "governance_note": str(e),
                })

        return pd.DataFrame(records), all_ok
