"""
Step 2C-2E Validation Evidence Engine.
Aggregates evidence, lineage, governance, and issue records
from all validation engines into unified output files.
"""

import pandas as pd
from scenario_validation_base_engine import ValidationEngineBase


class ValidationEvidenceEngine(ValidationEngineBase):
    def __init__(self, **kwargs):
        super().__init__(engine_name="validation_evidence", **kwargs)

    def run(self, engines: list) -> dict:
        """
        Collect evidence, lineage, governance, and issues from all engines.
        engines: list of engine instances that have already run.
        Returns dict of DataFrames.
        """
        all_lineage = []
        all_evidence = []
        all_governance = []
        all_issues = []

        for engine in engines:
            if hasattr(engine, "lineage_records"):
                all_lineage.extend(engine.lineage_records)
            if hasattr(engine, "evidence_records"):
                all_evidence.extend(engine.evidence_records)
            if hasattr(engine, "governance_records"):
                all_governance.extend(engine.governance_records)
            if hasattr(engine, "issue_records"):
                all_issues.extend(engine.issue_records)

        lineage_df = pd.DataFrame(all_lineage) if all_lineage else pd.DataFrame(columns=[
            "lineage_id", "scenario_run_id", "source_type", "source_id", "source_file", "link_type", "recorded_at"
        ])
        evidence_df = pd.DataFrame(all_evidence) if all_evidence else pd.DataFrame(columns=[
            "evidence_id", "scenario_run_id", "evidence_type", "source_type", "source_id", "source_file", "link_type", "recorded_at", "metadata_json"
        ])
        governance_df = pd.DataFrame(all_governance) if all_governance else pd.DataFrame(columns=[
            "governance_id", "scenario_run_id", "rule_id", "rule_name", "rule_applied", "rule_outcome", "message", "applied_at"
        ])
        issues_df = pd.DataFrame(all_issues) if all_issues else pd.DataFrame(columns=[
            "issue_id", "scenario_run_id", "approval_package_id", "issue_type", "issue_severity", "issue_description", "recommended_action", "recorded_at"
        ])

        self.write_output(lineage_df, "analytical_scenario_validation_lineage.csv")
        self.write_output(evidence_df, "analytical_scenario_validation_evidence.csv")
        self.write_output(governance_df, "analytical_scenario_validation_governance.csv")
        self.write_output(issues_df, "analytical_scenario_validation_issues.csv")

        return {
            "lineage": lineage_df,
            "evidence": evidence_df,
            "governance": governance_df,
            "issues": issues_df,
        }
