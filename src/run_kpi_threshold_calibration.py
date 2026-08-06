"""
Sentinel360 Healthcare — Safe Runner for Step 2B-1A

KPI Threshold Calibration and Validation

Guarantees:
  - Does NOT modify config/kpi_threshold_config.csv
  - Does NOT overwrite Phase 1, Phase 2A, or Step 2B-1 accepted files
  - Respects the 100,000-row classification limit
  - Produces only provisional candidate outputs (v1.0-candidate)
  - Stops safely before Step 2B-1B
"""

import sys
from pathlib import Path

# Ensure src is on path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from kpi_threshold_calibration_engine import KPIThresholdCalibrationEngine


def main():
    print("=" * 70)
    print("Sentinel360 — Step 2B-1A: KPI Threshold Calibration and Validation")
    print("=" * 70)

    engine = KPIThresholdCalibrationEngine(
        project_root=project_root,
        max_candidates_per_kpi=3,
        classification_row_limit=100_000,
    )

    print(f"\nCalibration Run ID: {engine.calibration_run_id}")
    print(f"Output directory: {engine.output_dir}")
    print(f"Classification row limit: {engine.classification_row_limit:,}")

    try:
        manifest = engine.run_full_calibration()
    except RuntimeError as e:
        print(f"\nRUNTIME ERROR (safe stop): {e}")
        sys.exit(1)

    print("\n" + "-" * 70)
    print("CALIBRATION COMPLETE")
    print("-" * 70)
    print(f"KPIs processed:           {manifest.kpis_processed}")
    print(f"Distribution profiles:    {manifest.distribution_profiles_generated}")
    print(f"Candidates generated:     {manifest.candidates_generated}")
    print(f"Candidates valid:         {manifest.candidates_valid}")
    print(f"Candidates invalid:       {manifest.candidates_invalid}")
    print(f"Candidates duplicate:     {manifest.candidates_duplicate}")
    print(f"Candidates shortlisted:   {manifest.candidates_shortlisted}")
    print(f"Classification rows:      {manifest.classification_rows_generated:,}")
    print(f"Volume control passed:    {manifest.volume_control_passed}")
    print(f"Burden results:           {manifest.burden_results_generated}")
    print(f"Stability results:        {manifest.stability_results_generated}")
    print(f"Trend alignments:         {manifest.trend_alignment_results_generated}")
    print(f"Recommendations:          {manifest.recommendations_generated}")
    print(f"Evidence records:         {manifest.evidence_records_generated}")
    print(f"Issue records:            {manifest.issue_records_generated}")
    print(f"Audit records:            {manifest.audit_records_generated}")
    print(f"Blocking issues:          {manifest.blocking_issues_count}")
    print(f"Warnings:                 {manifest.warnings_count}")
    print(f"Readiness for 2B-1B:      {manifest.readiness_for_2b1b}")
    print("-" * 70)
    print("All outputs written to: outputs/threshold_calibration/")
    print("STOP — Step 2B-1A complete. Awaiting stakeholder review (2B-1B).")
    print("=" * 70)


if __name__ == "__main__":
    main()
