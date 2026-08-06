"""
Sentinel360 Healthcare — Step 2B-1A Validation Suite

Performs:
  1. Schema validation (CSV headers and required columns)
  2. Key validation (foreign-key-like integrity)
  3. Formula verification (sampling)
  4. Immutability verification (checksums of protected files)
  5. Computational volume audit
  6. Output completeness check
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd


PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "threshold_calibration"
PROTECTED_FILES = [
    PROJECT_ROOT / "config" / "kpi_threshold_config.csv",
]
REQUIRED_OUTPUTS = {
    "threshold_distribution_profiles.csv": [
        "profile_record_id", "kpi_id", "kpi_name", "calculated_count", "data_sufficiency",
        "mean", "standard_deviation", "minimum", "maximum",
    ],
    "threshold_candidates_all.csv": [
        "threshold_candidate_id", "kpi_id", "candidate_name", "candidate_type",
        "calibration_method", "green_lower_boundary", "green_upper_boundary", "candidate_validity_status",
    ],
    "threshold_candidates_shortlisted.csv": [
        "threshold_candidate_id", "kpi_id", "candidate_name", "candidate_type",
        "calibration_method", "approval_status", "threshold_is_provisional",
    ],
    "threshold_classification_results.csv": [
        "candidate_classification_id", "threshold_candidate_id", "integration_record_id",
        "kpi_id", "kpi_value", "candidate_threshold_status", "threshold_is_provisional",
    ],
    "threshold_burden_results.csv": [
        "burden_record_id", "threshold_candidate_id", "kpi_id",
        "candidate_green_count", "candidate_amber_count", "candidate_red_count",
        "amber_plus_red_percentage", "classification_burden_level",
    ],
    "threshold_stability_results.csv": [
        "stability_record_id", "threshold_candidate_id", "kpi_id",
        "test_dimension", "test_segment", "stability_status",
    ],
    "threshold_trend_alignment.csv": [
        "alignment_record_id", "threshold_candidate_id", "kpi_id",
        "candidate_threshold_status", "agreement_status", "record_count",
    ],
    "threshold_recommendations.csv": [
        "recommendation_id", "kpi_id", "preferred_candidate_id",
        "recommendation_strength", "approval_status",
    ],
    "threshold_evidence_records.csv": [
        "evidence_record_id", "kpi_id", "evidence_category", "source_dataset",
    ],
    "threshold_issue_records.csv": [
        "issue_record_id", "kpi_id", "issue_category", "issue_severity", "blocking",
    ],
    "threshold_audit_records.csv": [
        "audit_record_id", "audit_phase", "audit_action", "entity_type", "entity_id", "audit_result",
    ],
    "threshold_calibration_manifest.json": [],
}


def file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_schema(filename: str, required_cols: List[str]) -> Tuple[bool, List[str]]:
    path = OUTPUT_DIR / filename
    if not path.exists():
        return False, [f"Missing file: {filename}"]
    if filename.endswith(".json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
            return True, []
        except Exception as e:
            return False, [f"Invalid JSON in {filename}: {e}"]
    df = pd.read_csv(path)
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        return False, [f"{filename} missing columns: {missing}"]
    return True, []


def validate_keys() -> Tuple[bool, List[str]]:
    issues: List[str] = []
    cand = pd.read_csv(OUTPUT_DIR / "threshold_candidates_shortlisted.csv")
    cls = pd.read_csv(OUTPUT_DIR / "threshold_classification_results.csv")
    burden = pd.read_csv(OUTPUT_DIR / "threshold_burden_results.csv")
    stability = pd.read_csv(OUTPUT_DIR / "threshold_stability_results.csv")
    trend = pd.read_csv(OUTPUT_DIR / "threshold_trend_alignment.csv")
    recs = pd.read_csv(OUTPUT_DIR / "threshold_recommendations.csv")

    # Classification -> Candidate
    orphan_cls = set(cls["threshold_candidate_id"]) - set(cand["threshold_candidate_id"])
    if orphan_cls:
        issues.append(f"Classification references unknown candidates: {orphan_cls}")

    # Burden -> Candidate
    orphan_brd = set(burden["threshold_candidate_id"]) - set(cand["threshold_candidate_id"])
    if orphan_brd:
        issues.append(f"Burden references unknown candidates: {orphan_brd}")

    # Stability -> Candidate
    orphan_stb = set(stability["threshold_candidate_id"]) - set(cand["threshold_candidate_id"])
    if orphan_stb:
        issues.append(f"Stability references unknown candidates: {orphan_stb}")

    # Trend -> Candidate
    orphan_aln = set(trend["threshold_candidate_id"]) - set(cand["threshold_candidate_id"])
    if orphan_aln:
        issues.append(f"Trend alignment references unknown candidates: {orphan_aln}")

    # Recommendation -> Candidate
    orphan_rec = set(recs["preferred_candidate_id"]) - set(cand["threshold_candidate_id"])
    if orphan_rec:
        issues.append(f"Recommendation references unknown candidates: {orphan_rec}")

    return len(issues) == 0, issues


def verify_formulas_sample(n_samples: int = 20) -> Tuple[bool, List[str]]:
    """Spot-check a sample of classifications against boundary rules."""
    issues: List[str] = []
    cls = pd.read_csv(OUTPUT_DIR / "threshold_classification_results.csv")
    cand = pd.read_csv(OUTPUT_DIR / "threshold_candidates_shortlisted.csv")
    sample = cls.sample(min(n_samples, len(cls)), random_state=42)

    for _, row in sample.iterrows():
        c = cand[cand["threshold_candidate_id"] == row["threshold_candidate_id"]].iloc[0]
        val = row["kpi_value"]
        status = row["candidate_threshold_status"]
        direction = c["directionality"]

        if pd.isna(val):
            continue

        expected = None
        if direction == "Higher is better":
            gl = c["green_lower_boundary"]
            if gl is not None and not pd.isna(gl):
                expected = "Candidate Green" if val >= gl else "Candidate Red"
        elif direction == "Lower is better":
            gu = c["green_upper_boundary"]
            if gu is not None and not pd.isna(gu):
                expected = "Candidate Green" if val <= gu else "Candidate Red"
        elif direction == "Context-sensitive":
            la = c["lower_amber_boundary"]
            gl = c["green_lower_boundary"]
            gu = c["green_upper_boundary"]
            ua = c["upper_amber_boundary"]
            if la is not None and not pd.isna(la) and val < la:
                expected = "Candidate Low Utilisation"
            elif gl is not None and not pd.isna(gl) and la is not None and not pd.isna(la) and la <= val < gl:
                expected = "Candidate Amber"
            elif gu is not None and not pd.isna(gu) and ua is not None and not pd.isna(ua) and gu < val <= ua:
                expected = "Candidate Amber"
            elif ua is not None and not pd.isna(ua) and val > ua:
                expected = "Candidate High Pressure"
            else:
                expected = "Candidate Green"

        if expected and status != expected:
            issues.append(
                f"Formula mismatch: {row['candidate_classification_id']} val={val:.2f} "
                f"got={status} expected={expected}"
            )

    return len(issues) == 0, issues


def verify_immutability() -> Tuple[bool, List[str]]:
    issues: List[str] = []
    checksum_path = OUTPUT_DIR / "checksums_pre_2b1a.json"
    if not checksum_path.exists():
        return False, ["Missing pre-2B-1A checksums file."]
    with open(checksum_path, "r", encoding="utf-8") as f:
        stored = json.load(f)
    for rel_path, expected_hash in stored.items():
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            issues.append(f"Protected file missing: {rel_path}")
            continue
        actual = file_checksum(full_path)
        if actual != expected_hash:
            issues.append(f"CHECKSUM MISMATCH (file modified!): {rel_path}")
    return len(issues) == 0, issues


def verify_volume() -> Tuple[bool, List[str]]:
    issues: List[str] = []
    manifest_path = OUTPUT_DIR / "threshold_calibration_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    if not manifest.get("volume_control_passed"):
        issues.append("Volume control failed in manifest.")
    if manifest.get("classification_rows_generated", 0) > 100_000:
        issues.append(f"Classification rows {manifest['classification_rows_generated']} exceed 100,000 limit.")
    return len(issues) == 0, issues


def run_all_validations() -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "validation_timestamp": datetime.now().isoformat(),
        "results": {},
        "overall_pass": True,
    }

    # Schema
    schema_pass = True
    schema_issues: List[str] = []
    for filename, cols in REQUIRED_OUTPUTS.items():
        ok, issues = validate_schema(filename, cols)
        if not ok:
            schema_pass = False
            schema_issues.extend(issues)
    report["results"]["schema_validation"] = {"passed": schema_pass, "issues": schema_issues}

    # Keys
    key_pass, key_issues = validate_keys()
    report["results"]["key_validation"] = {"passed": key_pass, "issues": key_issues}

    # Formulas
    formula_pass, formula_issues = verify_formulas_sample(n_samples=50)
    report["results"]["formula_verification"] = {"passed": formula_pass, "issues": formula_issues}

    # Immutability
    imm_pass, imm_issues = verify_immutability()
    report["results"]["immutability_verification"] = {"passed": imm_pass, "issues": imm_issues}

    # Volume
    vol_pass, vol_issues = verify_volume()
    report["results"]["volume_audit"] = {"passed": vol_pass, "issues": vol_issues}

    report["overall_pass"] = all(r["passed"] for r in report["results"].values())
    return report


def main():
    print("=" * 70)
    print("Sentinel360 — Step 2B-1A Validation Suite")
    print("=" * 70)
    report = run_all_validations()
    for check, result in report["results"].items():
        status = "PASS" if result["passed"] else "FAIL"
        print(f"\n[{status}] {check}")
        if result["issues"]:
            for issue in result["issues"]:
                print(f"  - {issue}")
    print("\n" + "-" * 70)
    overall = "ALL CHECKS PASSED" if report["overall_pass"] else "VALIDATION FAILED"
    print(f"Overall: {overall}")
    print("=" * 70)

    # Write report
    out_path = OUTPUT_DIR / "threshold_validation_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Validation report written to: {out_path}")


if __name__ == "__main__":
    main()
