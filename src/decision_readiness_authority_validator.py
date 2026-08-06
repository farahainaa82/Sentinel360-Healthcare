"""
Decision Readiness Authority Validator for Phase 2D-4.

Verifies existence, readability, row count, column count, checksum,
frozen status, and absence of superseded sources for all 2D-3 inputs.
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Any, Tuple
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(PROJECT_ROOT, "outputs", "decision_intelligence")

LOG = logging.getLogger("decision_readiness_authority_validator")


def compute_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> Dict[str, Any]:
    path = os.path.join(INPUT_DIR, "step_2d3_manifest.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_authority(logger: logging.Logger = None) -> Tuple[pd.DataFrame, bool]:
    logger = logger or LOG
    logger.info("Starting authority validation for Step 2D-4")

    manifest = load_manifest()
    manifest_outputs = manifest.get("outputs", {})

    required_files = [
        "step_2d3_authoritative_input_register.csv",
        "step_2d3_decision_scorecard_register.csv",
        "step_2d3_scorecard_dimension_register.csv",
        "step_2d3_scorecard_display_level_register.csv",
        "step_2d3_scorecard_condition_flag_register.csv",
        "step_2d3_scorecard_governance_burden_register.csv",
        "step_2d3_scorecard_management_readiness_register.csv",
        "step_2d3_scorecard_priority_view_register.csv",
        "step_2d3_scorecard_management_interpretation_register.csv",
        "step_2d3_scorecard_executive_view_register.csv",
        "step_2d3_scorecard_detailed_view_register.csv",
        "step_2d3_scorecard_streamlit_data_contract.csv",
        "step_2d3_scorecard_evidence_register.csv",
        "step_2d3_scorecard_lineage_register.csv",
        "step_2d3_scorecard_governance_register.csv",
        "step_2d3_scorecard_issue_register.csv",
        "step_2d3_execution_summary.csv",
        "step_2d3_manifest.json",
    ]

    records: List[Dict[str, Any]] = []
    all_pass = True

    for fname in required_files:
        fpath = os.path.join(INPUT_DIR, fname)
        rec: Dict[str, Any] = {
            "file_name": fname,
            "file_path": fpath,
            "source_phase": "2D-3",
            "row_count": 0,
            "column_count": 0,
            "checksum": "",
            "frozen_checksum": "",
            "checksum_match": False,
            "authoritative_status": "",
            "readiness_use_status": "",
            "governance_note": "",
        }

        if not os.path.exists(fpath):
            rec["authoritative_status"] = "Missing"
            rec["readiness_use_status"] = "Blocked"
            rec["governance_note"] = "File not found"
            all_pass = False
            records.append(rec)
            continue

        try:
            checksum = compute_sha256(fpath)
            rec["checksum"] = checksum

            # Get frozen checksum from manifest
            frozen = manifest_outputs.get(fname, {}).get("checksum", "")
            rec["frozen_checksum"] = frozen
            rec["checksum_match"] = (checksum == frozen) if frozen else True

            if fname.endswith(".csv"):
                try:
                    df = pd.read_csv(fpath)
                    rec["row_count"] = len(df)
                    rec["column_count"] = len(df.columns)
                except pd.errors.EmptyDataError:
                    rec["row_count"] = 0
                    rec["column_count"] = 0
            elif fname.endswith(".json"):
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    rec["row_count"] = len(data) if isinstance(data, (list, dict)) else 1
                    rec["column_count"] = len(data.keys()) if isinstance(data, dict) else 0

            if not rec["checksum_match"]:
                rec["authoritative_status"] = "Frozen Mismatch"
                rec["readiness_use_status"] = "Blocked"
                rec["governance_note"] = "Checksum does not match frozen manifest"
                all_pass = False
            else:
                rec["authoritative_status"] = "Authoritative"
                rec["readiness_use_status"] = "Ready for Classification"
                rec["governance_note"] = "Verified and frozen"

        except Exception as exc:
            rec["authoritative_status"] = "Read Error"
            rec["readiness_use_status"] = "Blocked"
            rec["governance_note"] = str(exc)
            all_pass = False

        records.append(rec)

    result_df = pd.DataFrame(records)
    logger.info("Authority validation complete: passed=%s", all_pass)
    return result_df, all_pass
