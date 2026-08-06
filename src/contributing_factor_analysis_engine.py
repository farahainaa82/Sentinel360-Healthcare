"""Contributing Factor Analysis Engine — Step 2B-4."""

import os
import pandas as pd
import numpy as np
from datetime import datetime

from relationship_analysis_models import (
    ContributingFactorClassification, ContradictionSeverity, ConfidenceLevel,
    MaterialityLevel, KPI_NAMES, UNIQUE_PAIRS,
)


class ContributingFactorAnalysisEngine:
    """Score contributing factors, detect contradictions, classify relationships."""

    def __init__(self, config_dir=None, inputs_dir=None, engine_run_id=None):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        self.config_dir = config_dir or os.path.join(project_root, "config")
        self.inputs_dir = inputs_dir or os.path.join(project_root, "data/analytical")
        self.engine_run_id = engine_run_id or f"CF-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.processed_at = datetime.utcnow().isoformat()
        self._load_configs()
        self._load_inputs()

    def _load_configs(self):
        cf_cfg = pd.read_csv(os.path.join(self.config_dir, "contributing_factor_rule_config.csv"))
        contra_cfg = pd.read_csv(os.path.join(self.config_dir, "relationship_contradiction_rule_config.csv"))
        gov_cfg = pd.read_csv(os.path.join(self.config_dir, "relationship_governance_config.csv"))
        hyp_cfg = pd.read_csv(os.path.join(self.config_dir, "root_cause_hypothesis_config.csv"))

        def get_param(df, name, default):
            mask = df["parameter_name"] == name
            return float(df.loc[mask, "parameter_value"].iloc[0]) if mask.any() else default

        self.cf_weights = {
            "association": get_param(cf_cfg, "association_weight", 0.20),
            "cooccurrence": get_param(cf_cfg, "cooccurrence_weight", 0.15),
            "temporal": get_param(cf_cfg, "temporal_weight", 0.15),
            "trend": get_param(cf_cfg, "trend_weight", 0.10),
            "dept_stability": get_param(cf_cfg, "dept_stability_weight", 0.10),
            "time_stability": get_param(cf_cfg, "time_stability_weight", 0.10),
            "plausibility": get_param(cf_cfg, "plausibility_weight", 0.10),
            "evidence": get_param(cf_cfg, "evidence_quality_weight", 0.10),
        }
        self.cf_plausible_min = get_param(cf_cfg, "plausible_contributing_min_score", 40.0)
        self.cf_strong_min = get_param(cf_cfg, "strong_hypothesis_min_score", 65.0)

        self.opp_dir_thr = get_param(contra_cfg, "opposite_direction_threshold", -0.30)
        self.pool_dept_thr = get_param(contra_cfg, "pooled_vs_dept_threshold", 0.40)
        self.precede_thr = get_param(contra_cfg, "target_precedes_source_threshold", 0.60)
        self.trend_contra_thr = get_param(contra_cfg, "opposing_trend_rate_threshold", 0.50)

        self.prov_mul = get_param(gov_cfg, "provisional_relationship_multiplier", 0.92)

        self.hyp_min_tier = "High"
        self.hyp_min_cf = get_param(hyp_cfg, "hypothesis_min_cf_score", 50.0)
        self.hyp_min_conf = "Moderate"
        self.hyp_no_major = True

    def _load_inputs(self):
        self.threshold_cfg = pd.read_csv(os.path.join(self.config_dir, "kpi_threshold_config.csv"))
        self.dept_risk = pd.read_csv(os.path.join(self.inputs_dir, "analytical_department_risk_daily.csv"))
        self.dept_risk["reporting_date"] = pd.to_datetime(self.dept_risk["reporting_date"])
        self.governance = pd.read_csv(os.path.join(self.inputs_dir, "analytical_department_risk_governance.csv"))
        self.governance["reporting_date"] = pd.to_datetime(self.governance["reporting_date"])

    # ------------------------------------------------------------------
    # Contributing factor scoring
    # ------------------------------------------------------------------
    def score_contributing_factors(self, pair_df, lag_df, stability_df):
        """Compute contributing-factor scores for each directed relationship."""
        records = []
        for _, row in pair_df.iterrows():
            rel_id = row["relationship_id"]
            src = row["source_kpi_id"]
            tgt = row["target_kpi_id"]
            hid = row["hospital_id"]
            did = row["department_id"]

            def _to_float(val, default=0.0):
                return default if pd.isna(val) else float(val)

            # Components (0-100 each)
            assoc = min(abs(_to_float(row.get("adversity_correlation"), 0.0)) * 100, 100)
            cooc = min(_to_float(row.get("adverse_cooccurrence_rate"), 0.0) * 200, 100)
            trend = min(_to_float(row.get("trend_agreement_rate"), 0.0) * 100, 100)

            # Temporal from lag
            lag_row = lag_df[(lag_df["relationship_id"] == rel_id) & (lag_df["hospital_id"] == hid) & (lag_df["department_id"] == did)]
            temporal = 0
            if not lag_row.empty:
                lag_corr = abs(_to_float(lag_row.iloc[0].get("lagged_correlation"), 0.0))
                prec = _to_float(lag_row.iloc[0].get("temporal_precedence_rate"), 0.0)
                temporal = min((lag_corr * 50) + (prec * 50), 100)

            # Stability
            stab_row = stability_df[stability_df["relationship_id"] == rel_id]
            dept_stab = 50
            if not stab_row.empty:
                consistency = _to_float(stab_row.iloc[0].get("direction_consistency_rate"), 0.0)
                dept_stab = min(consistency * 100, 100)

            time_stab = 50  # placeholder — time stability not fully computed in this scope
            plaus = self._plausibility_score(src, tgt)
            evidence = min(_to_float(row.get("paired_observation_count"), 0.0) / 30 * 100, 100)

            raw_score = (
                assoc * self.cf_weights["association"] +
                cooc * self.cf_weights["cooccurrence"] +
                temporal * self.cf_weights["temporal"] +
                trend * self.cf_weights["trend"] +
                dept_stab * self.cf_weights["dept_stability"] +
                time_stab * self.cf_weights["time_stability"] +
                plaus * self.cf_weights["plausibility"] +
                evidence * self.cf_weights["evidence"]
            )

            # Contradiction penalty
            contra_flag, contra_sev, contra_summary = self._detect_contradictions(row, lag_row, stab_row)
            penalty = {"No Contradiction": 0, "Minor": 5, "Material": 15, "Major": 35}.get(contra_sev, 0)

            # Provisional governance
            prov_flag, prov_mat, prov_list = self._provisional_governance(src, tgt)
            gov_adj = self.prov_mul if prov_flag else 1.0

            score_raw = raw_score - penalty
            score_norm = max(min(score_raw * gov_adj, 100), 0)

            classification = self._classify_cf(score_norm, contra_sev)

            records.append({
                "cf_record_id": f"{self.engine_run_id}-{hid}-{did}-{src}-{tgt}",
                "relationship_id": rel_id,
                "hospital_id": hid,
                "department_id": did,
                "source_kpi_id": src,
                "source_kpi_name": KPI_NAMES.get(src, src),
                "target_kpi_id": tgt,
                "target_kpi_name": KPI_NAMES.get(tgt, tgt),
                "association_component": round(assoc, 2),
                "cooccurrence_component": round(cooc, 2),
                "temporal_component": round(temporal, 2),
                "trend_component": round(trend, 2),
                "department_stability_component": round(dept_stab, 2),
                "time_stability_component": round(time_stab, 2),
                "plausibility_component": round(plaus, 2),
                "evidence_quality_component": round(evidence, 2),
                "contradiction_penalty": penalty,
                "governance_adjustment": round(gov_adj, 4),
                "contributing_factor_score_raw": round(score_raw, 2),
                "contributing_factor_score_normalized": round(score_norm, 2),
                "contributing_factor_classification": classification.value,
                "contradiction_flag": contra_flag,
                "contradiction_severity": contra_sev,
                "contradiction_summary": contra_summary,
                "contains_provisional_kpi": prov_flag,
                "provisional_relationship_flag": prov_flag and prov_mat in ["Material", "Dominant"],
                "provisional_kpi_list": prov_list,
                "provisional_contribution_materiality": prov_mat,
                "confidence_level": row.get("confidence_level", "Insufficient Evidence"),
                "engine_run_id": self.engine_run_id,
                "processed_at": self.processed_at,
            })
        return pd.DataFrame(records)

    def _plausibility_score(self, src, tgt):
        """Return a plausibility score based on operational knowledge."""
        plausible_pairs = {
            ("kpi_002", "kpi_001"), ("kpi_001", "kpi_004"), ("kpi_002", "kpi_004"),
            ("kpi_003", "kpi_004"), ("kpi_004", "kpi_005"), ("kpi_004", "kpi_006"),
            ("kpi_005", "kpi_006"), ("kpi_003", "kpi_005"), ("kpi_001", "kpi_005"),
            ("kpi_001", "kpi_006"),
        }
        if (src, tgt) in plausible_pairs or (tgt, src) in plausible_pairs:
            return 75.0
        return 50.0

    _SEVERITY_RANK = {
        ContradictionSeverity.NONE: 0,
        ContradictionSeverity.MINOR: 1,
        ContradictionSeverity.MATERIAL: 2,
        ContradictionSeverity.MAJOR: 3,
    }

    def _detect_contradictions(self, row, lag_row, stab_row):
        contradictions = []
        severity = ContradictionSeverity.NONE

        pearson = row.get("pearson_correlation", np.nan)
        if not pd.isna(pearson) and pearson < self.opp_dir_thr:
            contradictions.append("Opposite direction correlation")
            severity = max(severity, ContradictionSeverity.MATERIAL, key=lambda s: self._SEVERITY_RANK[s])

        if stab_row is not None and not stab_row.empty:
            consistency = stab_row.iloc[0].get("direction_consistency_rate", 1.0)
            if pd.isna(consistency):
                consistency = 1.0
            if consistency < self.pool_dept_thr:
                contradictions.append("Pooled direction differs from most departments")
                severity = max(severity, ContradictionSeverity.MATERIAL, key=lambda s: self._SEVERITY_RANK[s])

        if lag_row is not None and not lag_row.empty:
            rev_prec = lag_row.iloc[0].get("reverse_temporal_precedence_rate", 0)
            if not pd.isna(rev_prec) and rev_prec > self.precede_thr:
                contradictions.append("Target frequently precedes source")
                severity = max(severity, ContradictionSeverity.MINOR, key=lambda s: self._SEVERITY_RANK[s])

        trend_rate = row.get("trend_agreement_rate", 1.0)
        if pd.isna(trend_rate):
            trend_rate = 1.0
        if trend_rate < self.trend_contra_thr:
            contradictions.append("Trends frequently move in opposite directions")
            severity = max(severity, ContradictionSeverity.MINOR, key=lambda s: self._SEVERITY_RANK[s])

        if row.get("paired_observation_count", 0) < 10:
            contradictions.append("Very limited observation count")
            severity = max(severity, ContradictionSeverity.MINOR, key=lambda s: self._SEVERITY_RANK[s])

        flag = len(contradictions) > 0
        summary = "; ".join(contradictions) if contradictions else ""
        return flag, severity.value, summary

    def _provisional_governance(self, src, tgt):
        prov_kpis = self.threshold_cfg[self.threshold_cfg["threshold_is_provisional"] == True]["kpi_id"].tolist()
        prov_list = [k for k in [src, tgt] if k in prov_kpis]
        contains = len(prov_list) > 0
        # Materiality: simplified to Material if any provisional KPI involved
        mat = "Material" if contains else "No Contradiction"
        return contains, mat, "; ".join(prov_list)

    def _classify_cf(self, score, contra_sev):
        if contra_sev == "Major":
            if score < 20:
                return ContributingFactorClassification.NO_SUPPORTED_RELATIONSHIP
            return ContributingFactorClassification.WEAK_ASSOCIATION
        if score < 20:
            return ContributingFactorClassification.NO_SUPPORTED_RELATIONSHIP
        if score < 35:
            return ContributingFactorClassification.WEAK_ASSOCIATION
        if score < self.cf_plausible_min:
            return ContributingFactorClassification.SUPPORTED_ASSOCIATION
        if score < self.cf_strong_min:
            return ContributingFactorClassification.PLAUSIBLE_CONTRIBUTING_FACTOR
        return ContributingFactorClassification.STRONG_CONTRIBUTING_FACTOR_HYPOTHESIS

    # ------------------------------------------------------------------
    # Root-cause hypotheses
    # ------------------------------------------------------------------
    def generate_hypotheses(self, cf_df):
        """Generate potential root-cause hypotheses for eligible High/Critical departments."""
        eligible_tiers = ["High", "Critical"]
        eligible_depts = self.dept_risk[self.dept_risk["department_priority_tier"].isin(eligible_tiers)]

        records = []
        for _, drow in eligible_depts.iterrows():
            hid, did, rdate = drow["hospital_id"], drow["department_id"], drow["reporting_date"]
            dominant_kpi = drow.get("dominant_kpi_id", "")

            # Find supported contributing relationships where dominant is source or target
            cf_subset = cf_df[
                (cf_df["hospital_id"] == hid) &
                (cf_df["department_id"] == did) &
                (cf_df["contributing_factor_score_normalized"] >= self.hyp_min_cf) &
                (cf_df["contradiction_severity"] != "Major")
            ]
            if cf_subset.empty:
                continue

            for _, cf_row in cf_subset.iterrows():
                src = cf_row["source_kpi_id"]
                tgt = cf_row["target_kpi_id"]
                if dominant_kpi not in (src, tgt):
                    continue

                observed = f"{KPI_NAMES.get(dominant_kpi, dominant_kpi)} elevated"
                potential = f"{KPI_NAMES.get(src if dominant_kpi == tgt else tgt, '')} may contribute"
                pathway = f"{KPI_NAMES.get(src, src)} → {KPI_NAMES.get(tgt, tgt)}"

                records.append({
                    "hypothesis_id": f"HYP-{self.engine_run_id}-{hid}-{did}-{rdate.strftime('%Y%m%d')}-{src}-{tgt}",
                    "hospital_id": hid,
                    "department_id": did,
                    "reporting_date": rdate.strftime("%Y-%m-%d"),
                    "department_priority_tier": drow.get("department_priority_tier", ""),
                    "urgency_level": drow.get("urgency_level", ""),
                    "observed_problem_kpi_id": dominant_kpi,
                    "observed_problem_summary": observed,
                    "potential_contributing_kpi_id": src if dominant_kpi == tgt else tgt,
                    "potential_contributing_factor": potential,
                    "potential_pathway": pathway,
                    "relationship_id": cf_row["relationship_id"],
                    "relationship_strength": cf_row.get("confidence_level", ""),
                    "contributing_factor_score": cf_row["contributing_factor_score_normalized"],
                    "temporal_evidence": cf_row["temporal_component"],
                    "trend_evidence": cf_row["trend_component"],
                    "cooccurrence_evidence": cf_row["cooccurrence_component"],
                    "department_stability": cf_row["department_stability_component"],
                    "evidence_for": f"Association {cf_row['association_component']}; Co-occurrence {cf_row['cooccurrence_component']}",
                    "evidence_against": cf_row["contradiction_summary"],
                    "contradiction_severity": cf_row["contradiction_severity"],
                    "confidence_level": cf_row["confidence_level"],
                    "provisional_hypothesis_flag": cf_row["provisional_relationship_flag"],
                    "governance_warning": "Potential Root-Cause Hypothesis — Not Confirmed" if cf_row["provisional_relationship_flag"] else "",
                    "stakeholder_validation_required": True,
                    "causality_status": "Not Confirmed",
                    "evidence_pack_id": f"EVID-{self.engine_run_id}-{hid}-{did}-{rdate.strftime('%Y%m%d')}",
                    "engine_run_id": self.engine_run_id,
                })
        return pd.DataFrame(records)

    # ------------------------------------------------------------------
    # Network edges
    # ------------------------------------------------------------------
    def build_network_edges(self, cf_df):
        """Create relationship network edges from contributing-factor results."""
        edges = []
        for rel_id, group in cf_df.groupby("relationship_id"):
            # Use pooled/hospital grain if available, otherwise average departments
            pooled = group[group["department_id"] == "ALL"]
            if not pooled.empty:
                row = pooled.iloc[0]
            else:
                row = group.iloc[0]

            edges.append({
                "relationship_edge_id": f"EDGE-{self.engine_run_id}-{rel_id}",
                "source_kpi_id": row["source_kpi_id"],
                "source_kpi_name": row["source_kpi_name"],
                "target_kpi_id": row["target_kpi_id"],
                "target_kpi_name": row["target_kpi_name"],
                "relationship_direction": "Positive" if row["association_component"] > 0 else "Negative",
                "relationship_strength": row["contributing_factor_classification"],
                "adversity_correlation": row["association_component"] / 100,
                "best_supported_lag": 0,
                "contributing_factor_score": row["contributing_factor_score_normalized"],
                "contributing_factor_classification": row["contributing_factor_classification"],
                "confidence_level": row["confidence_level"],
                "provisional_relationship_flag": row["provisional_relationship_flag"],
                "contradiction_flag": row["contradiction_flag"],
                "active_edge_flag": row["contributing_factor_score_normalized"] > 20,
                "engine_run_id": self.engine_run_id,
                "processed_at": self.processed_at,
            })
        return pd.DataFrame(edges)

    # ------------------------------------------------------------------
    # Department contributing-factor summary
    # ------------------------------------------------------------------
    def department_cf_summary(self, cf_df):
        """Summarise contributing factors per department-date for Elevated+ tiers."""
        eligible = self.dept_risk[self.dept_risk["department_priority_tier"].isin(["Elevated", "High", "Critical"])]
        records = []
        for _, drow in eligible.iterrows():
            hid, did, rdate = drow["hospital_id"], drow["department_id"], drow["reporting_date"]
            cf_sub = cf_df[(cf_df["hospital_id"] == hid) & (cf_df["department_id"] == did)]
            if cf_sub.empty:
                continue
            best = cf_sub.loc[cf_sub["contributing_factor_score_normalized"].idxmax()]
            supp = cf_sub[cf_sub["contributing_factor_score_normalized"] >= 40]
            contra = cf_sub[cf_sub["contradiction_flag"] == True]

            records.append({
                "summary_id": f"SUM-{self.engine_run_id}-{hid}-{did}-{rdate.strftime('%Y%m%d')}",
                "hospital_id": hid,
                "department_id": did,
                "reporting_date": rdate.strftime("%Y-%m-%d"),
                "department_risk_score": drow.get("department_risk_score_normalized", np.nan),
                "priority_tier": drow.get("department_priority_tier", ""),
                "urgency_level": drow.get("urgency_level", ""),
                "dominant_kpi_id": drow.get("dominant_kpi_id", ""),
                "strongest_associated_kpi_id": best["target_kpi_id"] if best["source_kpi_id"] == drow.get("dominant_kpi_id", "") else best["source_kpi_id"],
                "strongest_cf_hypothesis": best["contributing_factor_classification"],
                "contributing_factor_score": best["contributing_factor_score_normalized"],
                "supporting_relationship_count": len(supp),
                "contradictory_relationship_count": len(contra),
                "relationship_confidence": best["confidence_level"],
                "provisional_relationship_flag": best["provisional_relationship_flag"],
                "evidence_pack_id": f"EVID-{self.engine_run_id}-{hid}-{did}-{rdate.strftime('%Y%m%d')}",
                "human_validation_required": True,
                "engine_run_id": self.engine_run_id,
                "processed_at": self.processed_at,
            })
        return pd.DataFrame(records)

    def run(self, pair_df, lag_df, stability_df):
        cf_df = self.score_contributing_factors(pair_df, lag_df, stability_df)
        hypotheses = self.generate_hypotheses(cf_df)
        network = self.build_network_edges(cf_df)
        summary = self.department_cf_summary(cf_df)
        return cf_df, hypotheses, network, summary
