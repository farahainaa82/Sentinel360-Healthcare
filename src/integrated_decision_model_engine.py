"""
Integrated Decision Model Engine for Phase 2D-1.

Builds the core integrated decision record by joining frozen upstream outputs.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


class IntegratedDecisionModelEngine:
    def build_integrated_records(self, inputs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        inputs dict keys expected:
            package_closure, management_scenario, scenario_runs, comparator_closure,
            deferred_non_ready, financial_readiness, financial_comparison,
            financial_confidence, approval_package, risk_ranking
        """
        pkg = inputs["package_closure"].copy()

        # Start with package closure as master (646 packages)
        base = pkg.rename(columns={
            "approval_package_id": "approval_package_id",
            "episode_id": "episode_id",
            "hospital_id": "hospital_id",
            "hospital_name": "hospital_name",
            "department_id": "department_id",
            "department_name": "department_name",
            "reporting_date": "reporting_date",
            "dominant_kpi_id": "dominant_kpi_id",
            "dominant_kpi_name": "dominant_kpi_name",
            "scenario_family": "scenario_family",
            "risk_score": "risk_score",
            "risk_tier": "risk_tier",
            "priority_tier": "priority_tier",
            "urgency": "urgency",
            "closure_category": "closure_category",
            "scenario_readiness": "scenario_readiness",
        })

        # Add management scenario fields (311 packages)
        mgmt = inputs.get("management_scenario")
        if mgmt is not None and len(mgmt) > 0:
            mgmt_cols = ["approval_package_id", "management_scenario_package_id",
                         "representative_recommendation", "recommendation_horizon",
                         "recommendation_type", "recommendation_validation_status",
                         "comparator_completeness", "baseline_available",
                         "conservative_available", "expected_available", "higher_intensity_available",
                         "scenario_validation_status", "scenario_confidence",
                         "scenario_tradeoff_summary", "scenario_displacement_summary",
                         "scenario_sensitivity_summary", "scenario_dominance_summary"]
            mgmt_cols = [c for c in mgmt_cols if c in mgmt.columns]
            base = base.merge(mgmt[mgmt_cols], on="approval_package_id", how="left")

        # Add approval package / recommendation fields
        ap = inputs.get("approval_package")
        if ap is not None and len(ap) > 0:
            ap_cols = [c for c in ap.columns if c not in base.columns or c == "approval_package_id"]
            ap = ap[ap_cols]
            base = base.merge(ap, on="approval_package_id", how="left")

        # Add financial readiness fields
        fr = inputs.get("financial_readiness")
        if fr is not None and len(fr) > 0:
            fr_cols = ["approval_package_id", "financial_review_required", "cost_completeness_status",
                       "total_scenario_cost", "total_estimated_benefit", "net_financial_impact",
                       "roi_status", "payback_status", "affordability_status"]
            fr_cols = [c for c in fr_cols if c in fr.columns]
            base = base.merge(fr[fr_cols], on="approval_package_id", how="left")

        # Add financial comparison fields
        fc = inputs.get("financial_comparison")
        if fc is not None and len(fc) > 0:
            fc_cols = [c for c in fc.columns if c not in base.columns or c == "approval_package_id"]
            fc = fc[fc_cols]
            base = base.merge(fc, on="approval_package_id", how="left")

        # Add comparator closure aggregation
        comp = inputs.get("comparator_closure")
        if comp is not None and len(comp) > 0:
            comp_agg = comp.groupby("approval_package_id").agg({
                "comparator_type": lambda x: ",".join(sorted(x.unique())),
                "comparator_id": "count",
            }).rename(columns={
                "comparator_type": "comparator_types_present",
                "comparator_id": "comparator_count",
            }).reset_index()
            base = base.merge(comp_agg, on="approval_package_id", how="left")

        # Add scenario run aggregation
        runs = inputs.get("scenario_runs")
        if runs is not None and len(runs) > 0:
            run_agg = runs.groupby("approval_package_id").agg({
                "scenario_run_id": "count",
            }).rename(columns={"scenario_run_id": "scenario_run_count"}).reset_index()
            base = base.merge(run_agg, on="approval_package_id", how="left")

        # Add deferred / non-ready flag
        deferred = inputs.get("deferred_non_ready")
        if deferred is not None and len(deferred) > 0:
            status_col = "closure_status" if "closure_status" in deferred.columns else "closure_category"
            deferred_map = deferred.set_index("approval_package_id")[status_col].to_dict()
            base["deferred_closure_category"] = base["approval_package_id"].map(deferred_map)

        # Generate integrated_decision_id
        base["integrated_decision_id"] = base["approval_package_id"].apply(
            lambda x: f"ID-{x}" if pd.notna(x) else ""
        )

        return base
