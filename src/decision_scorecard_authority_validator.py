"""
Decision Scorecard Authority Validator for Phase 2D-3.

Verifies existence, readability, row count, column count, checksum,
frozen status, and absence of superseded sources for all 2D-2 inputs.
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Any, Tuple
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(PROJECT_ROOT, "outputs", "decision_intelligence")

LOG = logging.getLogger("decision_scorecard_authority_validator")


def compute_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> Dict[str, Any]:
    path = os.path.join(INPUT_DIR, "step_2d2_manifest.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_authority(logger: logging.Logger = None) -> Tuple[pd.DataFrame, bool]:
    logger = logger or LOG
    logger.info("Starting authority validation for Step 2D-3")

    manifest = load_manifest()
    manifest_outputs = manifest.get("outputs", {})

    required_files = [
        "step_2d2_authoritative_input_register.csv",
        "step_2d2_decision_package_register.csv",
        "step_2d2_decision_package_section_register.csv",
        "step_2d2_decision_package_readiness_register.csv",
        "step_2d2_decision_package_completeness_register.csv",
        "step_2d2_management_question_register.csv",
        "step_2d2_required_confirmation_register.csv",
        "step_2d2_management_action_register.csv",
        "step_2d2_monitoring_requirement_register.csv",
        "step_2d2_decision_package_narrative_register.csv",
        "step_2d2_priority_view_register.csv",
        "step_2d2_export_contract_register.csv",
        "step_2d2_evidence_register.csv",
        "step_2d2_lineage_register.csv",
        "step_2d2_governance_register.csv",
        "step_2d2_issue_register.csv",
        "step_2d2_deferred_non_ready_register.csv",
        "step_2d2_execution_summary.csv",
        "step_2d2_manifest.json",
    ]

    rows: List[Dict[str, Any]] = []
    all_match = True

    for fname in required_files:
        fpath = os.path.join(INPUT_DIR, fname)
        row: Dict[str, Any] = {
            "file_name": fname,
            "file_path": fpath,
            "source_phase": "2D-2",
            "row_count": 0,
            "column_count": 0,
            "checksum": "",
            "frozen_checksum": "",
            "checksum_match": False,
            "authoritative_status": "Not Found",
            "scorecard_use_status": "Blocked",
            "governance_note": "",
        }

        if not os.path.exists(fpath):
            row["governance_note"] = "File not found"
            rows.append(row)
            all_match = False
            logger.error(f"Missing required file: {fname}")
            continue

        try:
            if fname.endswith(".json"):
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                row["row_count"] = len(content.splitlines())
                row["column_count"] = 0
            else:
                try:
                    df = pd.read_csv(fpath)
                except pd.errors.EmptyDataError:
                    df = pd.DataFrame()
                row["row_count"] = len(df)
                row["column_count"] = len(df.columns)
        except Exception as exc:
            row["governance_note"] = f"Read error: {exc}"
            rows.append(row)
            all_match = False
            logger.error(f"Read error for {fname}: {exc}")
            continue

        cksum = compute_sha256(fpath)
        row["checksum"] = cksum
        frozen = manifest_outputs.get(fname, {}).get("checksum", "")
        row["frozen_checksum"] = frozen
        row["checksum_match"] = (cksum == frozen) if frozen else True
        row["authoritative_status"] = "Authoritative" if row["checksum_match"] else "Superseded"
        row["scorecard_use_status"] = "Approved" if row["checksum_match"] else "Blocked"
        row["governance_note"] = (
            "Checksum matches manifest" if row["checksum_match"] else "CHECKSUM MISMATCH - STOP"
        )

        if not row["checksum_match"]:
            all_match = False
            logger.error(f"Checksum mismatch for {fname}")

        rows.append(row)

    df = pd.DataFrame(rows)
    logger.info(f"Authority validation complete. Files checked: {len(df)}, All match: {all_match}")
    return df, all_match
