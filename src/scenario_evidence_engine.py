"""Scenario evidence and lineage engine.

Phase 2C-2C — Tracks evidence, lineage, and traceability for every scenario result.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.scenario_models import EvidenceRecord, GovernanceRecord, IssueRecord, ScenarioResult
from src.scenario_config_loader import ScenarioConfigLoader


class ScenarioEvidenceEngine:
    """Creates evidence and lineage records for scenario runs."""

    def __init__(self, loader: ScenarioConfigLoader):
        self.loader = loader

    def create_evidence_for_result(
        self,
        result: ScenarioResult,
        baseline_sources: List[str],
        baseline_records: List[str],
        recommendation_ids: List[str],
        comparator_config: Dict[str, Any],
    ) -> List[EvidenceRecord]:
        """Create evidence records for a single scenario result."""
        records = []
        run_id = result.scenario_run_id

        # Baseline evidence
        for src in baseline_sources:
            records.append(EvidenceRecord(
                evidence_id=f"EV-{run_id}-BASE-{len(records)}",
                scenario_run_id=run_id,
                evidence_type="Baseline",
                source_type="Analytical Dataset",
                source_id=src,
                source_file=src,
                link_type="Derived From",
            ))

        for rec in baseline_records:
            records.append(EvidenceRecord(
                evidence_id=f"EV-{run_id}-REC-{len(records)}",
                scenario_run_id=run_id,
                evidence_type="Source Record",
                source_type="Analytical Record",
                source_id=rec,
                source_file="",
                link_type="Contributed To",
            ))

        # Recommendation linkage
        for rec_id in recommendation_ids:
            records.append(EvidenceRecord(
                evidence_id=f"EV-{run_id}-RECID-{len(records)}",
                scenario_run_id=run_id,
                evidence_type="Recommendation",
                source_type="Recommendation",
                source_id=rec_id,
                source_file="",
                link_type="Approved By",
            ))

        # Comparator config
        if comparator_config:
            records.append(EvidenceRecord(
                evidence_id=f"EV-{run_id}-COMP-{len(records)}",
                scenario_run_id=run_id,
                evidence_type="Comparator Configuration",
                source_type="Comparator Config",
                source_id=comparator_config.get("comparator_id", ""),
                source_file="config/scenario_comparator_config.csv",
                link_type="Defined By",
            ))

        # Package and episode
        records.append(EvidenceRecord(
            evidence_id=f"EV-{run_id}-PKG-{len(records)}",
            scenario_run_id=run_id,
            evidence_type="Approval Package",
            source_type="Package",
            source_id=result.approval_package_id,
            source_file="data/scenario_inputs/step_2c1d_episode_approval_package_register.csv",
            link_type="Authorised By",
        ))

        records.append(EvidenceRecord(
            evidence_id=f"EV-{run_id}-EP-{len(records)}",
            scenario_run_id=run_id,
            evidence_type="Episode",
            source_type="Episode",
            source_id=result.episode_id,
            source_file="data/scenario_inputs/step_2c1c_corrected_episode_register.csv",
            link_type="Based On",
        ))

        return records

    def create_governance_records(
        self,
        result: ScenarioResult,
        rule_checks: List[Any],
    ) -> List[GovernanceRecord]:
        """Create governance records from rule checks."""
        records = []
        run_id = result.scenario_run_id
        for check in rule_checks:
            if isinstance(check, tuple) and len(check) >= 3:
                rule_id, message, passed = check[0], check[1], check[2]
            elif isinstance(check, dict):
                rule_id = check.get("rule_id", "")
                message = check.get("message", "")
                passed = check.get("passed", True)
            else:
                continue

            records.append(GovernanceRecord(
                governance_id=f"GOV-{run_id}-{rule_id}",
                scenario_run_id=run_id,
                rule_id=rule_id,
                rule_name=rule_id,
                rule_applied=not passed,
                rule_outcome="Passed" if passed else "Blocked",
                message=message,
            ))
        return records

    def create_issue_records(
        self,
        result: ScenarioResult,
        issues: List[str],
    ) -> List[IssueRecord]:
        """Create issue records from issue messages."""
        records = []
        run_id = result.scenario_run_id
        for i, issue in enumerate(issues):
            records.append(IssueRecord(
                issue_id=f"ISS-{run_id}-{i}",
                scenario_run_id=run_id,
                issue_type="Execution Issue",
                severity="Warning" if "warning" in issue.lower() else "Error",
                message=issue,
                package_id=result.approval_package_id,
                episode_id=result.episode_id,
                template_id=result.scenario_template_id,
                comparator_id=result.comparator_id,
            ))
        return records

    def evidence_to_dict(self, records: List[EvidenceRecord]) -> List[Dict[str, Any]]:
        return [
            {
                "evidence_id": r.evidence_id,
                "scenario_run_id": r.scenario_run_id,
                "evidence_type": r.evidence_type,
                "source_type": r.source_type,
                "source_id": r.source_id,
                "source_file": r.source_file,
                "link_type": r.link_type,
                "recorded_at": r.recorded_at,
                "metadata_json": r.metadata_json,
            }
            for r in records
        ]

    def governance_to_dict(self, records: List[GovernanceRecord]) -> List[Dict[str, Any]]:
        return [
            {
                "governance_id": r.governance_id,
                "scenario_run_id": r.scenario_run_id,
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "rule_applied": r.rule_applied,
                "rule_outcome": r.rule_outcome,
                "message": r.message,
                "applied_at": r.applied_at,
            }
            for r in records
        ]

    def issues_to_dict(self, records: List[IssueRecord]) -> List[Dict[str, Any]]:
        return [
            {
                "issue_id": r.issue_id,
                "scenario_run_id": r.scenario_run_id,
                "issue_type": r.issue_type,
                "severity": r.severity,
                "message": r.message,
                "package_id": r.package_id,
                "episode_id": r.episode_id,
                "template_id": r.template_id,
                "comparator_id": r.comparator_id,
                "detected_at": r.detected_at,
                "resolution_status": r.resolution_status,
            }
            for r in records
        ]
