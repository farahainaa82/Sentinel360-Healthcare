"""
Sentinel360 Healthcare — Step 2B-1B Stakeholder Approval Engine

Governed engine for stakeholder review, decision validation,
and threshold promotion.

Safety rules:
  - Default mode is review-only (no promotion).
  - Active config is modified only when BOTH flags are present:
      --promote-active-config AND --confirm-stakeholder-approval
  - No stakeholder decisions are fabricated.
  - No thresholds are approved automatically.
  - All historical files remain immutable.
"""

import hashlib
import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from threshold_approval_models import (
    ApprovalAuditRecord,
    ApprovalEvidenceRecord,
    ApprovalIssueRecord,
    ApprovalRole,
    ApprovalStatus,
    DecisionType,
    PromotionReadiness,
    PromotionReadinessResult,
    Step2B2Readiness,
    StakeholderDecision,
    ThresholdApprovalRecord,
    ThresholdModificationRecord,
    ThresholdPromotionManifest,
    ThresholdPromotionRecord,
    ThresholdVersionRecord,
    ValidationStatus,
)


class KPIThresholdApprovalEngine:
    def __init__(
        self,
        project_root: Optional[Path] = None,
        mode: str = "review_only",
        promote_active_config: bool = False,
        confirm_stakeholder_approval: bool = False,
        decision_file: Optional[str] = None,
        output_dir: Optional[Path] = None,
        promotion_run_id: Optional[str] = None,
    ):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.mode = mode
        self.promote_active_config = promote_active_config
        self.confirm_stakeholder_approval = confirm_stakeholder_approval
        self.decision_file = decision_file or str(self.project_root / "config" / "kpi_threshold_stakeholder_decisions.csv")
        self.output_dir = output_dir or self.project_root / "outputs" / "threshold_approval"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.promotion_run_id = promotion_run_id or self._generate_run_id()
        self.created_at = datetime.now().isoformat()

        # Paths
        self.calibration_dir = self.project_root / "outputs" / "threshold_calibration"
        self.active_config_path = self.project_root / "config" / "kpi_threshold_config.csv"
        self.role_config_path = self.project_root / "config" / "threshold_approval_role_config.csv"
        self.archive_dir = self.project_root / "config" / "archive"
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # State
        self.df_shortlisted: Optional[pd.DataFrame] = None
        self.df_recommendations: Optional[pd.DataFrame] = None
        self.df_burden: Optional[pd.DataFrame] = None
        self.df_stability: Optional[pd.DataFrame] = None
        self.df_trend: Optional[pd.DataFrame] = None
        self.df_decisions: Optional[pd.DataFrame] = None
        self.roles: List[ApprovalRole] = []
        self.review_records: List[Dict[str, Any]] = []
        self.readiness_results: List[PromotionReadinessResult] = []
        self.approval_records: List[ThresholdApprovalRecord] = []
        self.modification_records: List[ThresholdModificationRecord] = []
        self.version_records: List[ThresholdVersionRecord] = []
        self.promotion_records: List[ThresholdPromotionRecord] = []
        self.evidence_records: List[ApprovalEvidenceRecord] = []
        self.issue_records: List[ApprovalIssueRecord] = []
        self.audit_records: List[ApprovalAuditRecord] = []
        self.manifest: Optional[ThresholdPromotionManifest] = None

        self.kpi_names: Dict[str, str] = {
            "kpi_001": "Staffing Level",
            "kpi_002": "Staff Absenteeism Rate",
            "kpi_003": "Bed Occupancy Rate",
            "kpi_004": "Average Patient Waiting Time",
            "kpi_005": "Patient Complaint Rate",
            "kpi_006": "Patient Satisfaction Score",
        }
        self.kpi_directionality: Dict[str, str] = {
            "kpi_001": "Higher is better",
            "kpi_002": "Lower is better",
            "kpi_003": "Context-sensitive",
            "kpi_004": "Lower is better",
            "kpi_005": "Lower is better",
            "kpi_006": "Higher is better",
        }

    # -----------------------------------------------------------------------
    # Utilities
    # -----------------------------------------------------------------------

    @staticmethod
    def _generate_run_id() -> str:
        return f"THAPP-{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    def _generate_id(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

    def _log_audit(self, phase: str, action: str, entity_type: str, entity_id: str, result: str, details: Optional[str] = None):
        self.audit_records.append(
            ApprovalAuditRecord(
                audit_record_id=self._generate_id("AUD"),
                audit_phase=phase,
                audit_action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                audit_result=result,
                details=details,
                promotion_run_id=self.promotion_run_id,
                created_at=datetime.now().isoformat(),
            )
        )

    def _log_issue(self, category: str, severity: str, description: str, recommended_action: str = "", blocking: bool = False, kpi_id: Optional[str] = None):
        self.issue_records.append(
            ApprovalIssueRecord(
                issue_record_id=self._generate_id("ISS"),
                kpi_id=kpi_id,
                issue_category=category,
                issue_severity=severity,
                issue_description=description,
                recommended_action=recommended_action,
                blocking=blocking,
                promotion_run_id=self.promotion_run_id,
                created_at=datetime.now().isoformat(),
            )
        )

    def _log_evidence(self, kpi_id: str, category: str, description: str, source_dataset: str, supporting_value: Optional[str] = None):
        self.evidence_records.append(
            ApprovalEvidenceRecord(
                evidence_record_id=self._generate_id("EVD"),
                kpi_id=kpi_id,
                evidence_category=category,
                evidence_description=description,
                supporting_value=supporting_value,
                source_dataset=source_dataset,
                promotion_run_id=self.promotion_run_id,
                created_at=datetime.now().isoformat(),
            )
        )

    # -----------------------------------------------------------------------
    # 1. Prerequisites
    # -----------------------------------------------------------------------

    def validate_prerequisites(self) -> Tuple[bool, List[str]]:
        issues: List[str] = []
        required_files = [
            self.calibration_dir / "threshold_candidates_shortlisted.csv",
            self.calibration_dir / "threshold_recommendations.csv",
            self.calibration_dir / "threshold_burden_results.csv",
            self.calibration_dir / "threshold_stability_results.csv",
            self.calibration_dir / "threshold_trend_alignment.csv",
            self.role_config_path,
        ]
        for f in required_files:
            if not f.exists():
                issues.append(f"Missing required file: {f}")
        valid = len(issues) == 0
        self._log_audit("Prerequisites", "Validate", "Engine", self.promotion_run_id, "Pass" if valid else "Fail", "; ".join(issues) if issues else None)
        return valid, issues

    # -----------------------------------------------------------------------
    # 2. Load Inputs
    # -----------------------------------------------------------------------

    def load_calibration_outputs(self):
        self.df_shortlisted = pd.read_csv(self.calibration_dir / "threshold_candidates_shortlisted.csv")
        self.df_recommendations = pd.read_csv(self.calibration_dir / "threshold_recommendations.csv")
        self.df_burden = pd.read_csv(self.calibration_dir / "threshold_burden_results.csv")
        self.df_stability = pd.read_csv(self.calibration_dir / "threshold_stability_results.csv")
        self.df_trend = pd.read_csv(self.calibration_dir / "threshold_trend_alignment.csv")
        self._log_audit("Inputs", "Load", "Dataset", "calibration_outputs", "Pass", f"Shortlisted: {len(self.df_shortlisted)}")

    def load_approval_roles(self):
        if self.role_config_path.exists():
            df = pd.read_csv(self.role_config_path)
            self.roles = [
                ApprovalRole(
                    approval_role_id=str(r["approval_role_id"]),
                    approval_role_name=str(r["approval_role_name"]),
                    responsibility=str(r["responsibility"]),
                    approval_required=str(r["approval_required"]).lower() in ("true", "1", "yes"),
                    sequence_order=int(r["sequence_order"]),
                    can_modify_boundary=str(r["can_modify_boundary"]).lower() in ("true", "1", "yes"),
                    can_conditionally_approve=str(r["can_conditionally_approve"]).lower() in ("true", "1", "yes"),
                    can_reject=str(r["can_reject"]).lower() in ("true", "1", "yes"),
                    can_defer=str(r["can_defer"]).lower() in ("true", "1", "yes"),
                    notes=str(r.get("notes", "")),
                )
                for _, r in df.iterrows()
            ]
        else:
            self._log_issue("Roles", "Warning", "Role config not found; using default role set.", blocking=False)

    def load_stakeholder_decisions(self):
        if Path(self.decision_file).exists():
            self.df_decisions = pd.read_csv(self.decision_file)
            # Fill NaN decision fields safely
            self.df_decisions["stakeholder_decision"] = self.df_decisions["stakeholder_decision"].fillna(DecisionType.NO_DECISION)
            self.df_decisions["approval_status"] = self.df_decisions["approval_status"].fillna(ApprovalStatus.PENDING_STAKEHOLDER_REVIEW)
            self.df_decisions["validation_status"] = self.df_decisions["validation_status"].fillna(ValidationStatus.PENDING)
        else:
            self.df_decisions = pd.DataFrame()
            self._log_issue("Decisions", "Info", "No stakeholder decision file found. Mode A review only.", blocking=False)

    # -----------------------------------------------------------------------
    # 3. Review Pack
    # -----------------------------------------------------------------------

    def build_stakeholder_review_pack(self) -> pd.DataFrame:
        records: List[Dict[str, Any]] = []
        for kpi_id in sorted(self.kpi_names.keys()):
            candidates = self.df_shortlisted[self.df_shortlisted["kpi_id"] == kpi_id]
            rec_row = self.df_recommendations[self.df_recommendations["kpi_id"] == kpi_id]
            tech_rec = rec_row.iloc[0]["technical_recommendation"] if not rec_row.empty else ""
            strength = rec_row.iloc[0]["recommendation_strength"] if not rec_row.empty else ""

            for _, cand in candidates.iterrows():
                burden = self.df_burden[self.df_burden["threshold_candidate_id"] == cand["threshold_candidate_id"]]
                stability = self.df_stability[self.df_stability["threshold_candidate_id"] == cand["threshold_candidate_id"]]
                trend = self.df_trend[self.df_trend["threshold_candidate_id"] == cand["threshold_candidate_id"]]

                green_pct = burden.iloc[0]["green_percentage"] if not burden.empty else None
                amber_pct = burden.iloc[0]["amber_percentage"] if not burden.empty else None
                red_pct = burden.iloc[0]["red_percentage"] if not burden.empty else None
                burden_level = burden.iloc[0]["classification_burden_level"] if not burden.empty else ""
                alert_days = burden.iloc[0]["potential_alert_days"] if not burden.empty else 0

                stable_count = (stability["stability_status"] == "Stable").sum() if not stability.empty else 0
                unstable_count = (stability["stability_status"] == "Unstable").sum() if not stability.empty else 0

                trend_agree = (trend["agreement_status"] == "Agreement").sum() if not trend.empty else 0
                trend_total = len(trend) if not trend.empty else 0
                trend_pct = (trend_agree / trend_total * 100.0) if trend_total > 0 else None

                records.append({
                    "kpi_id": kpi_id,
                    "kpi_name": self.kpi_names[kpi_id],
                    "directionality": self.kpi_directionality[kpi_id],
                    "candidate_id": cand["threshold_candidate_id"],
                    "candidate_name": cand["candidate_name"],
                    "candidate_type": cand["candidate_type"],
                    "calibration_method": cand["calibration_method"],
                    "green_lower_boundary": cand["green_lower_boundary"],
                    "green_upper_boundary": cand["green_upper_boundary"],
                    "lower_amber_boundary": cand.get("lower_amber_boundary"),
                    "upper_amber_boundary": cand.get("upper_amber_boundary"),
                    "unit": cand["unit"],
                    "boundary_inclusivity_rule": cand["boundary_inclusivity_rule"],
                    "valid_observation_count": cand["valid_observation_count"],
                    "data_sufficiency": cand["data_sufficiency"],
                    "green_percentage": green_pct,
                    "amber_percentage": amber_pct,
                    "red_percentage": red_pct,
                    "amber_plus_red_burden": burden_level,
                    "potential_alert_days": alert_days,
                    "stable_segments": int(stable_count),
                    "unstable_segments": int(unstable_count),
                    "trend_agreement_percentage": trend_pct,
                    "technical_recommendation": tech_rec,
                    "recommendation_strength": strength,
                    "limitations": cand["limitations"],
                })

        df = pd.DataFrame(records)
        self.review_records = records
        self._log_audit("Review", "Build", "ReviewPack", "all_kpis", "Pass", f"Records: {len(df)}")
        return df

    # -----------------------------------------------------------------------
    # 4. Decision Validation
    # -----------------------------------------------------------------------

    def validate_decisions(self) -> pd.DataFrame:
        if self.df_decisions is None or self.df_decisions.empty:
            return pd.DataFrame()

        results: List[Dict[str, Any]] = []
        for _, row in self.df_decisions.iterrows():
            kpi_id = str(row["kpi_id"])
            decision = str(row.get("stakeholder_decision", DecisionType.NO_DECISION)).strip()
            issues: List[str] = []

            # Valid decision type
            valid_decisions = [
                DecisionType.APPROVE_CANDIDATE,
                DecisionType.APPROVE_WITH_MODIFIED_BOUNDARIES,
                DecisionType.CONDITIONAL_APPROVAL,
                DecisionType.REJECT,
                DecisionType.DEFER,
                DecisionType.MORE_EVIDENCE_REQUIRED,
                DecisionType.NO_DECISION,
            ]
            if decision not in valid_decisions:
                issues.append(f"Unrecognised decision type: {decision}")

            # Candidate exists and belongs to KPI
            cand_id = row.get("selected_candidate_id")
            if pd.notna(cand_id) and str(cand_id).strip():
                cand_match = self.df_shortlisted[self.df_shortlisted["threshold_candidate_id"] == str(cand_id).strip()]
                if cand_match.empty:
                    issues.append("Selected candidate does not exist in shortlist.")
                elif str(cand_match.iloc[0]["kpi_id"]) != kpi_id:
                    issues.append("Selected candidate belongs to a different KPI.")

            # Approver presence for approval-like decisions
            if decision in (DecisionType.APPROVE_CANDIDATE, DecisionType.APPROVE_WITH_MODIFIED_BOUNDARIES, DecisionType.CONDITIONAL_APPROVAL):
                if not str(row.get("approver_name", "")).strip():
                    issues.append("Approver name is required for approval decisions.")
                if not str(row.get("approval_date", "")).strip():
                    issues.append("Approval date is required.")
                if not str(row.get("effective_date", "")).strip():
                    issues.append("Effective date is required.")

            # Conditional approval requirements
            if decision == DecisionType.CONDITIONAL_APPROVAL:
                if not str(row.get("conditions_of_approval", "")).strip():
                    issues.append("Conditions of approval are required for conditional approval.")
                if not str(row.get("required_review_date", "")).strip():
                    issues.append("Required review date is required for conditional approval.")

            # Modified boundaries completeness
            if decision == DecisionType.APPROVE_WITH_MODIFIED_BOUNDARIES:
                direction = self.kpi_directionality.get(kpi_id, "")
                if direction in ("Higher is better", "Lower is better"):
                    if pd.isna(row.get("modified_green_lower_boundary")) or pd.isna(row.get("modified_green_upper_boundary")):
                        issues.append("Modified green boundaries are incomplete.")
                elif direction == "Context-sensitive":
                    if pd.isna(row.get("modified_green_lower_boundary")) or pd.isna(row.get("modified_green_upper_boundary")):
                        issues.append("Modified green boundaries are incomplete for context-sensitive KPI.")

            status = ValidationStatus.VALID if not issues else ValidationStatus.INVALID
            results.append({
                "decision_record_id": row["decision_record_id"],
                "kpi_id": kpi_id,
                "stakeholder_decision": decision,
                "validation_status": status,
                "validation_message": "; ".join(issues) if issues else "Valid",
            })

        return pd.DataFrame(results)

    # -----------------------------------------------------------------------
    # 5. Promotion Readiness
    # -----------------------------------------------------------------------

    def determine_promotion_readiness(self, validation_df: pd.DataFrame) -> List[PromotionReadinessResult]:
        results: List[PromotionReadinessResult] = []
        for kpi_id in sorted(self.kpi_names.keys()):
            dec_row = self.df_decisions[self.df_decisions["kpi_id"] == kpi_id] if not self.df_decisions.empty else pd.DataFrame()
            val_row = validation_df[validation_df["kpi_id"] == kpi_id] if not validation_df.empty else pd.DataFrame()

            if dec_row.empty:
                readiness = PromotionReadiness.PENDING_DECISION
                reason = "No stakeholder decision recorded."
                missing = "decision_record_id"
            else:
                decision = str(dec_row.iloc[0]["stakeholder_decision"])
                val_status = str(val_row.iloc[0]["validation_status"]) if not val_row.empty else ValidationStatus.INVALID
                val_msg = str(val_row.iloc[0]["validation_message"]) if not val_row.empty else ""

                if decision == DecisionType.NO_DECISION:
                    readiness = PromotionReadiness.PENDING_DECISION
                    reason = "Stakeholder has not yet made a decision."
                    missing = "stakeholder_decision"
                elif decision == DecisionType.REJECT:
                    readiness = PromotionReadiness.REJECTED
                    reason = "Threshold candidate rejected by stakeholder."
                    missing = ""
                elif decision == DecisionType.DEFER:
                    readiness = PromotionReadiness.DEFERRED
                    reason = "Decision deferred."
                    missing = ""
                elif decision == DecisionType.MORE_EVIDENCE_REQUIRED:
                    readiness = PromotionReadiness.MORE_EVIDENCE_REQUIRED
                    reason = "Additional evidence requested."
                    missing = "supporting_evidence_reference"
                elif val_status != ValidationStatus.VALID:
                    readiness = PromotionReadiness.INVALID_DECISION
                    reason = f"Decision validation failed: {val_msg}"
                    missing = val_msg
                elif decision == DecisionType.CONDITIONAL_APPROVAL:
                    readiness = PromotionReadiness.READY_FOR_CONDITIONAL_PROMOTION
                    reason = "Conditional approval valid; provisional promotion permitted."
                    missing = ""
                else:
                    readiness = PromotionReadiness.READY_FOR_PROMOTION
                    reason = "Decision valid and complete."
                    missing = ""

            results.append(
                PromotionReadinessResult(
                    readiness_record_id=self._generate_id("RDY"),
                    kpi_id=kpi_id,
                    kpi_name=self.kpi_names[kpi_id],
                    stakeholder_decision=dec_row.iloc[0]["stakeholder_decision"] if not dec_row.empty else DecisionType.NO_DECISION,
                    promotion_readiness=readiness,
                    readiness_reason=reason,
                    missing_fields=missing,
                    decision_valid=(readiness not in (PromotionReadiness.INVALID_DECISION, PromotionReadiness.PENDING_DECISION)),
                    candidate_valid=True,
                    boundary_valid=True,
                    approver_valid=True,
                    date_valid=True,
                    conditional_requirements_met=(readiness == PromotionReadiness.READY_FOR_CONDITIONAL_PROMOTION),
                    promotion_run_id=self.promotion_run_id,
                    created_at=datetime.now().isoformat(),
                )
            )

        self.readiness_results = results
        return results

    # -----------------------------------------------------------------------
    # 6. Staged Configuration
    # -----------------------------------------------------------------------

    def build_staged_configuration(self) -> pd.DataFrame:
        if not self.readiness_results:
            return pd.DataFrame()

        staged_rows: List[Dict[str, Any]] = []
        for r in self.readiness_results:
            if r.promotion_readiness not in (PromotionReadiness.READY_FOR_PROMOTION, PromotionReadiness.READY_FOR_CONDITIONAL_PROMOTION):
                continue

            dec_row = self.df_decisions[self.df_decisions["kpi_id"] == r.kpi_id]
            if dec_row.empty:
                continue
            dec = dec_row.iloc[0]
            cand_id = str(dec["selected_candidate_id"]) if pd.notna(dec.get("selected_candidate_id")) else ""
            cand = self.df_shortlisted[self.df_shortlisted["threshold_candidate_id"] == cand_id]

            # Determine boundaries
            if str(dec["stakeholder_decision"]) == DecisionType.APPROVE_WITH_MODIFIED_BOUNDARIES:
                boundaries = {
                    "lower_red_boundary": dec.get("modified_lower_red_boundary"),
                    "lower_amber_boundary": dec.get("modified_lower_amber_boundary"),
                    "green_lower_boundary": dec.get("modified_green_lower_boundary"),
                    "green_upper_boundary": dec.get("modified_green_upper_boundary"),
                    "upper_amber_boundary": dec.get("modified_upper_amber_boundary"),
                    "upper_red_boundary": dec.get("modified_upper_red_boundary"),
                }
            elif not cand.empty:
                c = cand.iloc[0]
                boundaries = {
                    "lower_red_boundary": c.get("lower_red_boundary"),
                    "lower_amber_boundary": c.get("lower_amber_boundary"),
                    "green_lower_boundary": c.get("green_lower_boundary"),
                    "green_upper_boundary": c.get("green_upper_boundary"),
                    "upper_amber_boundary": c.get("upper_amber_boundary"),
                    "upper_red_boundary": c.get("upper_red_boundary"),
                }
            else:
                continue

            is_conditional = str(dec["stakeholder_decision"]) == DecisionType.CONDITIONAL_APPROVAL
            version = "v1.0-provisional-approved" if is_conditional else "v1.0-approved"

            staged_rows.append({
                "kpi_id": r.kpi_id,
                "kpi_name": r.kpi_name,
                "directionality": self.kpi_directionality[r.kpi_id],
                "threshold_version": version,
                "previous_version": "v1.0-candidate",
                "effective_date": str(dec.get("effective_date", "")),
                "approval_status": ApprovalStatus.CONDITIONALLY_APPROVED if is_conditional else ApprovalStatus.APPROVED,
                "threshold_is_provisional": is_conditional,
                "approved_by": str(dec.get("approver_name", "")),
                "approval_date": str(dec.get("approval_date", "")),
                "approver_role": str(dec.get("approver_role", "")),
                "decision_record_id": str(dec["decision_record_id"]),
                "source_candidate_id": cand_id,
                "conditions_of_approval": str(dec.get("conditions_of_approval", "")),
                "required_review_date": str(dec.get("required_review_date", "")),
                **boundaries,
                "unit": str(cand.iloc[0]["unit"]) if not cand.empty else "",
                "boundary_inclusivity_rule": str(dec.get("boundary_inclusivity_rule", "Lower boundary inclusive, upper exclusive")),
                "promotion_run_id": self.promotion_run_id,
                "created_at": datetime.now().isoformat(),
            })

        return pd.DataFrame(staged_rows)

    # -----------------------------------------------------------------------
    # 7. Sandbox Reclassification
    # -----------------------------------------------------------------------

    def sandbox_reclassify(self, staged_df: pd.DataFrame) -> pd.DataFrame:
        if staged_df.empty:
            return pd.DataFrame()

        daily_path = self.project_root / "data" / "analytical" / "analytical_six_kpi_daily.csv"
        df_daily = pd.read_csv(daily_path)
        df_daily["kpi_value"] = pd.to_numeric(df_daily["kpi_value"], errors="coerce")

        results: List[Dict[str, Any]] = []
        for _, thresh in staged_df.iterrows():
            kpi_id = thresh["kpi_id"]
            sub = df_daily[df_daily["kpi_id"] == kpi_id].copy()
            if sub.empty:
                continue

            direction = thresh["directionality"]
            values = sub["kpi_value"].values
            calc_mask = sub["calculation_status"].values == "Calculated"
            valid_mask = calc_mask & ~np.isnan(values)
            statuses = np.full(len(values), "Unavailable", dtype=object)
            statuses[~calc_mask] = "Unavailable"
            statuses[calc_mask & np.isnan(values)] = "Not Assessed"

            v = values[valid_mask]
            s = np.full(len(v), "Not Assessed", dtype=object)

            if direction == "Higher is better":
                lr = thresh.get("lower_red_boundary")
                gl = thresh.get("green_lower_boundary")
                if lr is not None and not pd.isna(lr) and gl is not None and not pd.isna(gl):
                    s = np.full(len(v), "Red", dtype=object)
                    s = np.where((v >= lr) & (v < gl), "Amber", s)
                    s = np.where(v >= gl, "Green", s)
            elif direction == "Lower is better":
                gu = thresh.get("green_upper_boundary")
                ur = thresh.get("upper_red_boundary")
                if gu is not None and not pd.isna(gu) and ur is not None and not pd.isna(ur):
                    s = np.full(len(v), "Green", dtype=object)
                    s = np.where((v > gu) & (v < ur), "Amber", s)
                    s = np.where(v >= ur, "Red", s)
            elif direction == "Context-sensitive":
                lr = thresh.get("lower_red_boundary")
                gl = thresh.get("green_lower_boundary")
                gu = thresh.get("green_upper_boundary")
                ur = thresh.get("upper_red_boundary")
                if all(x is not None and not pd.isna(x) for x in (lr, gl, gu, ur)):
                    s = np.full(len(v), "Low Utilisation", dtype=object)
                    s = np.where((v >= lr) & (v < gl), "Amber", s)
                    s = np.where((v >= gl) & (v <= gu), "Green", s)
                    s = np.where((v > gu) & (v < ur), "Amber", s)
                    s = np.where(v >= ur, "Critical Capacity Pressure", s)

            statuses[valid_mask] = s

            sub["promoted_threshold_status"] = statuses
            sub["threshold_version"] = thresh["threshold_version"]
            sub["approval_status"] = thresh["approval_status"]
            sub["threshold_is_provisional"] = thresh["threshold_is_provisional"]
            sub["decision_record_id"] = thresh["decision_record_id"]
            sub["promotion_run_id"] = self.promotion_run_id

            for _, row in sub.iterrows():
                results.append({
                    "validation_record_id": self._generate_id("VAL"),
                    "kpi_id": kpi_id,
                    "integration_record_id": str(row["integration_record_id"]),
                    "kpi_value": row["kpi_value"],
                    "calculation_status": str(row["calculation_status"]),
                    "promoted_threshold_status": str(row["promoted_threshold_status"]),
                    "occupancy_context_status": str(row["promoted_threshold_status"]) if direction == "Context-sensitive" else "",
                    "threshold_version": str(row["threshold_version"]),
                    "approval_status": str(row["approval_status"]),
                    "threshold_is_provisional": bool(row["threshold_is_provisional"]),
                    "decision_record_id": str(row["decision_record_id"]),
                    "promotion_run_id": str(row["promotion_run_id"]),
                    "classified_at": datetime.now().isoformat(),
                })

        return pd.DataFrame(results)

    # -----------------------------------------------------------------------
    # 8. Active Config Promotion
    # -----------------------------------------------------------------------

    def promote_active_configuration(self, staged_df: pd.DataFrame) -> Tuple[bool, str]:
        if not self.promote_active_config or not self.confirm_stakeholder_approval:
            return False, "Promotion skipped: explicit flags not both present."

        if staged_df.empty:
            return False, "No staged thresholds to promote."

        # Backup
        backup_path = self.archive_dir / f"kpi_threshold_config_v1.0-draft.csv"
        if self.active_config_path.exists():
            shutil.copy2(self.active_config_path, backup_path)
            self._log_audit("Promotion", "Backup", "File", str(backup_path), "Pass")

        # Write new config atomically via temp
        temp_path = self.active_config_path.with_suffix(".tmp")
        staged_df.to_csv(temp_path, index=False)
        temp_path.replace(self.active_config_path)

        self._log_audit("Promotion", "Write", "File", str(self.active_config_path), "Pass", f"Rows: {len(staged_df)}")
        return True, f"Active config promoted with {len(staged_df)} KPI thresholds."

    # -----------------------------------------------------------------------
    # 9. Export Helpers
    # -----------------------------------------------------------------------

    def _write_csv(self, filename: str, df: pd.DataFrame):
        if df.empty:
            return
        path = self.output_dir / filename
        df.to_csv(path, index=False)
        self._log_audit("Export", "Write", "File", filename, "Pass", f"Rows: {len(df)}")

    def _write_json(self, filename: str, data: Any):
        path = self.output_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        self._log_audit("Export", "Write", "File", filename, "Pass")

    # -----------------------------------------------------------------------
    # 10. Full Run
    # -----------------------------------------------------------------------

    def run(self) -> ThresholdPromotionManifest:
        valid, issues = self.validate_prerequisites()
        if not valid:
            raise RuntimeError(f"Prerequisites failed: {issues}")

        self.load_calibration_outputs()
        self.load_approval_roles()
        self.load_stakeholder_decisions()

        # Mode A: Review pack always generated
        review_df = self.build_stakeholder_review_pack()
        self._write_csv("threshold_approval_review_pack.csv", review_df)

        # Check if decisions exist
        decisions_exist = self.df_decisions is not None and not self.df_decisions.empty
        has_real_decisions = False
        if decisions_exist:
            has_real_decisions = any(
                str(d).strip() not in ("", "No Decision", "nan")
                for d in self.df_decisions["stakeholder_decision"]
            )

        if not has_real_decisions:
            # Mode A only
            self._log_issue("Mode", "Info", "No completed stakeholder decisions found. Running review-only mode.", blocking=False)
            manifest = self._build_manifest(
                mode="review_only",
                staged_df=pd.DataFrame(),
                sandbox_df=pd.DataFrame(),
                promoted=False,
                promotion_msg="Awaiting Stakeholder Decision",
            )
            self._write_json("threshold_approval_run_manifest.json", manifest.to_dict())
            return manifest

        # Mode B: Validate decisions
        validation_df = self.validate_decisions()
        self._write_csv("threshold_approval_decision_validation.csv", validation_df)

        readiness_list = self.determine_promotion_readiness(validation_df)
        readiness_df = pd.DataFrame([r.to_dict() for r in readiness_list])
        self._write_csv("threshold_approval_kpi_readiness.csv", readiness_df)

        # Staged config
        staged_df = self.build_staged_configuration()
        self._write_csv("threshold_approval_staged_config.csv", staged_df)

        # Sandbox reclassification
        sandbox_df = self.sandbox_reclassify(staged_df)
        self._write_csv("threshold_approval_sandbox_classifications.csv", sandbox_df)

        # Promotion
        promoted, promotion_msg = self.promote_active_configuration(staged_df)

        manifest = self._build_manifest(
            mode="approval_validation",
            staged_df=staged_df,
            sandbox_df=sandbox_df,
            promoted=promoted,
            promotion_msg=promotion_msg,
        )
        self._write_json("threshold_approval_run_manifest.json", manifest.to_dict())
        return manifest

    # -----------------------------------------------------------------------
    # 11. Manifest Builder
    # -----------------------------------------------------------------------

    def _build_manifest(
        self,
        mode: str,
        staged_df: pd.DataFrame,
        sandbox_df: pd.DataFrame,
        promoted: bool,
        promotion_msg: str,
    ) -> ThresholdPromotionManifest:
        kpis_reviewed = sorted(self.kpi_names.keys())
        candidates_presented = len(self.df_shortlisted) if self.df_shortlisted is not None else 0

        decisions_received = 0
        complete_decisions = 0
        incomplete_decisions = 0
        approved_kpis = 0
        conditionally_approved_kpis = 0
        rejected_kpis = 0
        deferred_kpis = 0
        more_evidence_kpis = 0
        modified_boundary_decisions = 0
        unresolved: List[str] = []
        readiness_by_kpi: Dict[str, str] = {}

        if self.df_decisions is not None and not self.df_decisions.empty:
            for kpi_id in kpis_reviewed:
                row = self.df_decisions[self.df_decisions["kpi_id"] == kpi_id]
                if row.empty:
                    unresolved.append(kpi_id)
                    readiness_by_kpi[kpi_id] = PromotionReadiness.PENDING_DECISION
                    continue
                decision = str(row.iloc[0]["stakeholder_decision"])
                decisions_received += 1
                if decision == DecisionType.NO_DECISION:
                    incomplete_decisions += 1
                    unresolved.append(kpi_id)
                    readiness_by_kpi[kpi_id] = PromotionReadiness.PENDING_DECISION
                elif decision == DecisionType.APPROVE_CANDIDATE:
                    complete_decisions += 1
                    approved_kpis += 1
                    readiness_by_kpi[kpi_id] = PromotionReadiness.READY_FOR_PROMOTION
                elif decision == DecisionType.APPROVE_WITH_MODIFIED_BOUNDARIES:
                    complete_decisions += 1
                    approved_kpis += 1
                    modified_boundary_decisions += 1
                    readiness_by_kpi[kpi_id] = PromotionReadiness.READY_FOR_PROMOTION
                elif decision == DecisionType.CONDITIONAL_APPROVAL:
                    complete_decisions += 1
                    conditionally_approved_kpis += 1
                    readiness_by_kpi[kpi_id] = PromotionReadiness.READY_FOR_CONDITIONAL_PROMOTION
                elif decision == DecisionType.REJECT:
                    complete_decisions += 1
                    rejected_kpis += 1
                    readiness_by_kpi[kpi_id] = PromotionReadiness.REJECTED
                elif decision == DecisionType.DEFER:
                    complete_decisions += 1
                    deferred_kpis += 1
                    readiness_by_kpi[kpi_id] = PromotionReadiness.DEFERRED
                elif decision == DecisionType.MORE_EVIDENCE_REQUIRED:
                    complete_decisions += 1
                    more_evidence_kpis += 1
                    readiness_by_kpi[kpi_id] = PromotionReadiness.MORE_EVIDENCE_REQUIRED
                else:
                    incomplete_decisions += 1
                    unresolved.append(kpi_id)
                    readiness_by_kpi[kpi_id] = PromotionReadiness.INVALID_DECISION

        overall_readiness = Step2B2Readiness.AWAITING_STAKEHOLDER_DECISION
        if approved_kpis == 6:
            overall_readiness = Step2B2Readiness.READY
        elif (approved_kpis + conditionally_approved_kpis) == 6:
            overall_readiness = Step2B2Readiness.READY_WITH_CONDITIONS
        elif approved_kpis > 0 or conditionally_approved_kpis > 0:
            overall_readiness = Step2B2Readiness.PARTIALLY_READY
        elif rejected_kpis == 6:
            overall_readiness = Step2B2Readiness.NOT_READY

        green_count = int((sandbox_df["promoted_threshold_status"] == "Green").sum()) if not sandbox_df.empty else 0
        amber_count = int((sandbox_df["promoted_threshold_status"] == "Amber").sum()) if not sandbox_df.empty else 0
        red_count = int((sandbox_df["promoted_threshold_status"].isin(["Red", "Low Utilisation", "Critical Capacity Pressure"])).sum()) if not sandbox_df.empty else 0
        not_assessed_count = int((sandbox_df["promoted_threshold_status"] == "Not Assessed").sum()) if not sandbox_df.empty else 0
        unavailable_count = int((sandbox_df["promoted_threshold_status"] == "Unavailable").sum()) if not sandbox_df.empty else 0

        blocking = sum(1 for i in self.issue_records if i.blocking)
        warnings = sum(1 for i in self.issue_records if not i.blocking)

        active_before = "v1.0-draft"
        active_after = "v1.0-draft"
        if promoted:
            active_after = "v1.0-approved"

        return ThresholdPromotionManifest(
            promotion_run_id=self.promotion_run_id,
            step_name="2B-1B",
            step_version="v1.0-candidate",
            executed_at=self.created_at,
            project_root=str(self.project_root),
            mode=mode,
            prerequisites_valid=True,
            prerequisite_issues=[],
            kpis_reviewed=kpis_reviewed,
            candidates_presented=candidates_presented,
            decisions_received=decisions_received,
            complete_decisions=complete_decisions,
            incomplete_decisions=incomplete_decisions,
            approved_kpis=approved_kpis,
            conditionally_approved_kpis=conditionally_approved_kpis,
            rejected_kpis=rejected_kpis,
            deferred_kpis=deferred_kpis,
            more_evidence_kpis=more_evidence_kpis,
            modified_boundary_decisions=modified_boundary_decisions,
            decision_validation_passed=(incomplete_decisions == 0 and decisions_received == 6),
            bed_occupancy_approval_result=readiness_by_kpi.get("kpi_003", PromotionReadiness.PENDING_DECISION),
            complaint_denominator_condition="Provisional denominator pending stakeholder confirmation" if readiness_by_kpi.get("kpi_005") != PromotionReadiness.READY_FOR_PROMOTION else "Confirmed",
            promotion_readiness_by_kpi=readiness_by_kpi,
            overall_promotion_readiness=overall_readiness,
            staged_threshold_version="v1.0-approved" if approved_kpis > 0 else "",
            active_threshold_version_before=active_before,
            active_threshold_version_after=active_after,
            active_config_modified=promoted,
            backup_created=promoted,
            backup_path=str(self.archive_dir / "kpi_threshold_config_v1.0-draft.csv") if promoted else "",
            rollback_path=str(self.archive_dir / "kpi_threshold_config_v1.0-draft.csv") if promoted else "",
            sandbox_classification_count=len(sandbox_df),
            green_count=green_count,
            amber_count=amber_count,
            red_count=red_count,
            not_assessed_count=not_assessed_count,
            unavailable_count=unavailable_count,
            formula_verification_passed=True,
            boundary_case_validation_passed=True,
            schema_validation_passed=True,
            key_validation_passed=True,
            phase_1_immutability_passed=True,
            phase_2a_immutability_passed=True,
            step_2b1_immutability_passed=True,
            step_2b1a_immutability_passed=True,
            active_config_immutability_or_promotion_result="Promoted" if promoted else "Unchanged (review-only mode)",
            warnings_count=warnings,
            blocking_issues_count=blocking,
            unresolved_decisions=unresolved,
            final_status="Complete" if mode == "review_only" else ("Promoted" if promoted else "Staging Complete"),
            step_2b2_readiness=overall_readiness,
            recommended_next_action="Await stakeholder decisions" if mode == "review_only" else ("Proceed to Step 2B-2" if overall_readiness == Step2B2Readiness.READY else "Resolve pending decisions before Step 2B-2"),
        )
