"""Hospital Risk Summary Engine for Step 2B-3.

Aggregates department-date risk records into a single hospital-date summary.
"""

import uuid
from datetime import datetime

import pandas as pd
import numpy as np


class HospitalRiskSummaryEngine:
    """Produce one hospital-date risk summary from department risk records."""

    def __init__(self, engine_run_id=None):
        self.engine_run_id = engine_run_id or f"HOSP-RISK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.processed_at = datetime.now().isoformat()

    def run(self, dept_df, kpi_df):
        """Generate hospital-date summaries."""
        grp = dept_df.groupby(["hospital_id", "reporting_date"])

        summaries = []
        for (hid, rdate), g in grp:
            tier_counts = g["department_priority_tier"].value_counts().to_dict()
            urgency_counts = g["urgency_level"].value_counts().to_dict()

            assessable_depts = g[g["department_priority_tier"] != "Not Assessable"]

            # Top 3 departments by risk score
            top3 = g.sort_values("department_risk_score_normalized", ascending=False).head(3)
            top3_ids = top3["department_id"].tolist()
            top3_drivers = top3["dominant_kpi_name"].fillna(top3["dominant_kpi_id"]).tolist()

            # Provisional risk departments
            prov_depts = g[g["provisional_risk_flag"] == True]

            # Overall data availability
            overall_avail = g["department_data_availability_rate"].mean()

            # Maximum urgency
            urgency_order = {"Immediate Review": 4, "Prompt Review": 3, "Review Soon": 2, "Routine Monitoring": 1, "Not Assessable": 0}
            max_urgency = g["urgency_level"].map(urgency_order).idxmax()
            max_urgency_level = g.loc[max_urgency, "urgency_level"] if max_urgency in g.index else "Routine Monitoring"

            summaries.append({
                "hospital_risk_summary_id": f"HRS-{uuid.uuid4().hex[:12].upper()}",
                "hospital_id": hid,
                "reporting_date": rdate,
                "department_count": len(g),
                "assessable_department_count": len(assessable_depts),
                "stable_department_count": tier_counts.get("Stable", 0),
                "monitor_department_count": tier_counts.get("Monitor", 0),
                "elevated_department_count": tier_counts.get("Elevated", 0),
                "high_department_count": tier_counts.get("High", 0),
                "critical_department_count": tier_counts.get("Critical", 0),
                "not_assessable_department_count": tier_counts.get("Not Assessable", 0),
                "highest_department_risk_score": g["department_risk_score_normalized"].max(),
                "highest_risk_department_id": top3_ids[0] if top3_ids else None,
                "top_three_department_ids": "; ".join(top3_ids),
                "top_three_dominant_drivers": "; ".join([str(d) for d in top3_drivers]),
                "provisional_risk_department_count": len(prov_depts),
                "overall_data_availability_rate": round(overall_avail, 4),
                "maximum_urgency_level": max_urgency_level,
                "hospital_summary_status": "Generated",
                "engine_run_id": self.engine_run_id,
                "processed_at": self.processed_at,
            })

        return pd.DataFrame(summaries)

    def to_hospital_summary_dataframe(self, df):
        cols = [
            "hospital_risk_summary_id", "hospital_id", "reporting_date",
            "department_count", "assessable_department_count",
            "stable_department_count", "monitor_department_count",
            "elevated_department_count", "high_department_count",
            "critical_department_count", "not_assessable_department_count",
            "highest_department_risk_score", "highest_risk_department_id",
            "top_three_department_ids", "top_three_dominant_drivers",
            "provisional_risk_department_count", "overall_data_availability_rate",
            "maximum_urgency_level", "hospital_summary_status",
            "engine_run_id", "processed_at",
        ]
        available = [c for c in cols if c in df.columns]
        return df[available].copy()
