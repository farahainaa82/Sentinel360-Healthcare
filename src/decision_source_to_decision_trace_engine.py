"""
decision_source_to_decision_trace_engine.py
Phase 2D-6 — Source-to-decision trace per package.
"""

import pandas as pd
import uuid


def build_source_to_decision_traces(routing_df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, row in routing_df.iterrows():
        package_id = row["decision_package_id"]
        status = row["final_readiness_status"]

        trace_summary = (
            f"Source data -> Processed data -> KPI calculation -> "
            f"Threshold/trend analysis -> Risk prioritisation -> "
            f"Contributing-factor analysis -> Recommendation generation -> "
            f"Recommendation validation -> Approval-package preparation -> "
            f"Scenario modelling -> Scenario validation -> Financial analysis -> "
            f"Decision integration -> Decision package -> Scorecard -> "
            f"Readiness assessment -> Action routing"
        )

        records.append({
            "source_to_decision_trace_id": f"TRC-{uuid.uuid4().hex[:8].upper()}",
            "decision_package_id": package_id,
            "trace_summary": trace_summary,
            "source_phase_path": "1 -> 2A -> 2B -> 2C-1 -> 2C-2 -> 2C-3 -> 2D-1 -> 2D-2 -> 2D-3 -> 2D-4 -> 2D-5",
            "source_record_path": f"episode_{row.get('episode_id','')}_hospital_{row.get('hospital_id','')}_dept_{row.get('department_id','')}",
            "transformation_path": "TXF-1 through TXF-17",
            "configuration_version_path": "1.0",
            "evidence_reference_path": f"EVP-{package_id}",
            "lineage_reference_path": f"LNP-{package_id}",
            "trace_status": "Complete" if status in ["Ready for Integrated Management Review", "Ready with Conditions"] else "Partial",
            "trace_limitation": "" if status in ["Ready for Integrated Management Review", "Ready with Conditions"] else f"Limited by readiness status: {status}",
            "governance_note": "Trace does not claim completed management decision",
        })
    return pd.DataFrame(records)
