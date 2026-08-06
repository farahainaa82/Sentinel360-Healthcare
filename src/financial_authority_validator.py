"""
Financial Authority Validator for Phase 2C-3.

Verifies frozen Phase 2C-2F outputs before use.
"""

import os
import json
from typing import Dict, List
import pandas as pd

from financial_base_engine import FinancialBaseEngine, compute_sha256, load_csv


class FinancialAuthorityValidator(FinancialBaseEngine):
    def __init__(self):
        super().__init__()
        self.required_files = {
            "step_2c2f_authoritative_file_register.csv": "2C-2F",
            "step_2c2f_package_closure_register.csv": "2C-2F",
            "step_2c2f_scenario_run_closure_register.csv": "2C-2F",
            "step_2c2f_comparator_closure_register.csv": "2C-2F",
            "step_2c2f_management_scenario_package_register.csv": "2C-2F",
            "step_2c2f_financial_input_requirement_register.csv": "2C-2F",
            "step_2c2f_scenario_audit_traceability_register.csv": "2C-2F",
            "step_2c2f_deferred_and_non_ready_register.csv": "2C-2F",
            "step_2c2f_rejected_scenario_register.csv": "2C-2F",
            "step_2c2f_closure_issue_register.csv": "2C-2F",
            "step_2c2f_freeze_manifest.json": "2C-2F",
            "step_2c2f_execution_summary.csv": "2C-2F",
        }
        self.manifest_path = os.path.join(self.output_dir.replace("financial_impact", "scenario_modelling"), "step_2c2f_freeze_manifest.json")

    def validate(self) -> pd.DataFrame:
        self.log("Starting authority and immutability check...")
        rows = []
        manifest_checksums = {}

        # Load freeze manifest
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            for fname, info in manifest.get("closure_outputs", {}).items():
                manifest_checksums[fname] = info.get("checksum", "")
            for fname, info in manifest.get("authoritative_inputs", {}).items():
                manifest_checksums[fname] = info.get("checksum", "")
        else:
            self.log("Freeze manifest not found — proceeding with warning", level="warning")

        scenario_dir = self.output_dir.replace("financial_impact", "scenario_modelling")
        for fname, phase in self.required_files.items():
            fpath = os.path.join(scenario_dir, fname)
            exists = os.path.exists(fpath)
            readable = os.access(fpath, os.R_OK) if exists else False
            size = os.path.getsize(fpath) if exists else 0
            row_count = 0
            col_count = 0
            checksum = ""
            match = False
            frozen_checksum = manifest_checksums.get(fname, "")

            if exists and readable and size > 2:
                try:
                    df = pd.read_csv(fpath) if fname.endswith(".csv") else pd.DataFrame()
                    if fname.endswith(".csv"):
                        row_count = len(df)
                        col_count = len(df.columns)
                    checksum = compute_sha256(fpath)
                    match = (checksum == frozen_checksum) if frozen_checksum else True
                except Exception as e:
                    self.log(f"Parse error for {fname}: {e}", level="warning")

            auth_status = "Authoritative" if (exists and readable and size > 2 and match) else "Issue"
            financial_use = "Authoritative" if auth_status == "Authoritative" else "Excluded"
            note = ""
            if not exists:
                note = "File not found"
            elif size <= 2:
                note = "File is empty"
            elif not match and frozen_checksum:
                note = f"Checksum mismatch: expected {frozen_checksum[:16]}..., got {checksum[:16]}..."
            elif not frozen_checksum:
                note = "No frozen checksum available for comparison"

            rows.append({
                "file_name": fname,
                "file_path": fpath,
                "upstream_phase": phase,
                "row_count": row_count,
                "column_count": col_count,
                "checksum": checksum,
                "frozen_checksum": frozen_checksum,
                "checksum_match": match,
                "authoritative_status": auth_status,
                "financial_use_status": financial_use,
                "governance_note": note,
            })

        reg = pd.DataFrame(rows)
        auth_count = (reg["authoritative_status"] == "Authoritative").sum()
        self.log(f"Authority check complete: {auth_count}/{len(reg)} files authoritative.")
        return reg
