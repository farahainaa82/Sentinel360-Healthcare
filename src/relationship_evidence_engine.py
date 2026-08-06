"""Relationship Evidence Engine — Step 2B-4."""

import os
import pandas as pd
import numpy as np
from datetime import datetime
import uuid


class RelationshipEvidenceEngine:
    """Generate evidence and lineage records for relationship analysis."""

    def __init__(self, engine_run_id=None):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        self.project_root = project_root
        self.engine_run_id = engine_run_id or f"EVID-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.processed_at = datetime.utcnow().isoformat()

    def create_evidence_records(self, pair_df, lag_df, stability_df, cf_df, hypotheses):
        records = []
        for _, row in pair_df.iterrows():
            records.append({
                "evidence_record_id": f"EVID-{self.engine_run_id}-{row['relationship_record_id']}",
                "relationship_record_id": row["relationship_record_id"],
                "evidence_type": "Pairwise Association",
                "source_reference": "analytical_six_kpi_daily.csv",
                "records_used": row.get("paired_observation_count", 0),
                "calculation_method": "Pearson and Spearman correlation; direction agreement",
                "result_summary": f"Pearson={row.get('pearson_correlation', np.nan)}; Spearman={row.get('spearman_correlation', np.nan)}",
                "engine_run_id": self.engine_run_id,
                "processed_at": self.processed_at,
            })
        for _, row in lag_df.iterrows():
            records.append({
                "evidence_record_id": f"EVID-{self.engine_run_id}-{row['lag_record_id']}",
                "relationship_record_id": row["lag_record_id"],
                "evidence_type": "Temporal Lag",
                "source_reference": "analytical_six_kpi_daily.csv",
                "records_used": row.get("lagged_observation_count", 0),
                "calculation_method": "Lagged Pearson correlation; temporal precedence rate",
                "result_summary": f"Best lag={row.get('best_supported_lag', 0)}d; precedence rate={row.get('temporal_precedence_rate', np.nan)}",
                "engine_run_id": self.engine_run_id,
                "processed_at": self.processed_at,
            })
        for _, row in cf_df.iterrows():
            records.append({
                "evidence_record_id": f"EVID-{self.engine_run_id}-{row['cf_record_id']}",
                "relationship_record_id": row["cf_record_id"],
                "evidence_type": "Contributing Factor Score",
                "source_reference": "analytical_kpi_risk_scores_daily.csv",
                "records_used": row.get("evidence_quality_component", 0),
                "calculation_method": "Weighted component scoring with contradiction penalty",
                "result_summary": f"CF score={row.get('contributing_factor_score_normalized', np.nan)}; class={row.get('contributing_factor_classification', '')}",
                "engine_run_id": self.engine_run_id,
                "processed_at": self.processed_at,
            })
        for _, row in hypotheses.iterrows():
            records.append({
                "evidence_record_id": f"EVID-{self.engine_run_id}-{row['hypothesis_id']}",
                "relationship_record_id": row["hypothesis_id"],
                "evidence_type": "Potential Root-Cause Hypothesis",
                "source_reference": "analytical_department_risk_daily.csv",
                "records_used": 1,
                "calculation_method": "Hypothesis generation from contributing-factor eligibility rules",
                "result_summary": f"Problem={row.get('observed_problem_summary', '')}; pathway={row.get('potential_pathway', '')}",
                "engine_run_id": self.engine_run_id,
                "processed_at": self.processed_at,
            })
        return pd.DataFrame(records)

    def create_lineage_records(self, pair_df, lag_df, stability_df, cf_df, hypotheses, network, summary):
        records = []
        for df, name in [(pair_df, "pairwise"), (lag_df, "lag"), (stability_df, "stability"),
                         (cf_df, "contributing_factor"), (hypotheses, "hypothesis"),
                         (network, "network"), (summary, "summary")]:
            records.append({
                "lineage_record_id": f"LINEAGE-{self.engine_run_id}-{name}",
                "output_dataset": f"analytical_kpi_{name}_relationships.csv",
                "source_datasets": "analytical_six_kpi_daily.csv; analytical_kpi_threshold_classification_daily.csv; analytical_kpi_trend_signals.csv; analytical_kpi_risk_scores_daily.csv; analytical_department_risk_daily.csv",
                "transformation_logic": f"{name.replace('_', ' ').title()} analysis via Step 2B-4 engine",
                "record_count": len(df),
                "engine_run_id": self.engine_run_id,
                "processed_at": self.processed_at,
            })
        return pd.DataFrame(records)

    def run(self, pair_df, lag_df, stability_df, cf_df, hypotheses, network, summary):
        evidence = self.create_evidence_records(pair_df, lag_df, stability_df, cf_df, hypotheses)
        lineage = self.create_lineage_records(pair_df, lag_df, stability_df, cf_df, hypotheses, network, summary)
        return evidence, lineage
