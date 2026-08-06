"""
Sentinel360 Healthcare — Safe Runner for Step 2B-1B

Stakeholder Review, Approval and Threshold Promotion

Default mode: review-only (no promotion, no active config modification).

Explicit flags required for active promotion:
  --promote-active-config
  --confirm-stakeholder-approval

Usage:
  python src/run_kpi_threshold_approval.py [options]
"""

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from kpi_threshold_approval_engine import KPIThresholdApprovalEngine


def main():
    parser = argparse.ArgumentParser(description="Sentinel360 Step 2B-1B — Stakeholder Approval Engine")
    parser.add_argument("--project-root", type=str, default=str(project_root), help="Project root directory")
    parser.add_argument("--review-only", action="store_true", default=True, help="Generate review package only (default)")
    parser.add_argument("--validate-decisions", action="store_true", help="Validate stakeholder decisions")
    parser.add_argument("--execute-staging", action="store_true", help="Create staged configuration")
    parser.add_argument("--promote-active-config", action="store_true", help="Allow active config promotion (requires --confirm-stakeholder-approval)")
    parser.add_argument("--confirm-stakeholder-approval", action="store_true", help="Confirm explicit stakeholder approval evidence exists")
    parser.add_argument("--decision-file", type=str, default=None, help="Path to stakeholder decisions CSV")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    parser.add_argument("--kpi-id", type=str, default=None, help="Process single KPI only")
    parser.add_argument("--skip-reclassification", action="store_true", help="Skip sandbox reclassification")
    parser.add_argument("--skip-modified-boundary-impact", action="store_true", help="Skip modified boundary impact analysis")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as blocking")
    parser.add_argument("--report-only", action="store_true", help="Generate report without executing")

    args = parser.parse_args()

    # Determine mode
    mode = "review_only"
    if args.validate_decisions:
        mode = "validate_decisions"
    if args.execute_staging:
        mode = "execute_staging"
    if args.promote_active_config or args.confirm_stakeholder_approval:
        mode = "approval_validation"

    print("=" * 70)
    print("Sentinel360 — Step 2B-1B: Stakeholder Review and Approval")
    print("=" * 70)
    print(f"Mode: {mode}")
    print(f"Project root: {args.project_root}")
    print(f"Promote active config: {args.promote_active_config}")
    print(f"Confirm stakeholder approval: {args.confirm_stakeholder_approval}")

    engine = KPIThresholdApprovalEngine(
        project_root=Path(args.project_root),
        mode=mode,
        promote_active_config=args.promote_active_config,
        confirm_stakeholder_approval=args.confirm_stakeholder_approval,
        decision_file=args.decision_file,
        output_dir=Path(args.output_dir) if args.output_dir else None,
    )

    try:
        manifest = engine.run()
    except RuntimeError as e:
        print(f"\nRUNTIME ERROR (safe stop): {e}")
        sys.exit(1)

    print("\n" + "-" * 70)
    print("EXECUTION COMPLETE")
    print("-" * 70)
    print(f"Run ID:               {manifest.promotion_run_id}")
    print(f"Mode:                 {manifest.mode}")
    print(f"KPIs reviewed:        {manifest.kpis_reviewed}")
    print(f"Candidates presented: {manifest.candidates_presented}")
    print(f"Decisions received:   {manifest.decisions_received}")
    print(f"Complete decisions:   {manifest.complete_decisions}")
    print(f"Incomplete decisions: {manifest.incomplete_decisions}")
    print(f"Approved KPIs:        {manifest.approved_kpis}")
    print(f"Conditionally approved: {manifest.conditionally_approved_kpis}")
    print(f"Rejected KPIs:        {manifest.rejected_kpis}")
    print(f"Deferred KPIs:        {manifest.deferred_kpis}")
    print(f"More evidence:        {manifest.more_evidence_kpis}")
    print(f"Active config modified: {manifest.active_config_modified}")
    print(f"Backup created:       {manifest.backup_created}")
    print(f"Sandbox classifications: {manifest.sandbox_classification_count}")
    print(f"Blocking issues:      {manifest.blocking_issues_count}")
    print(f"Warnings:             {manifest.warnings_count}")
    print(f"Step 2B-2 readiness:  {manifest.step_2b2_readiness}")
    print(f"Recommended action:   {manifest.recommended_next_action}")
    print("-" * 70)
    print("All outputs written to: outputs/threshold_approval/")
    print("STOP — Step 2B-1B complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
