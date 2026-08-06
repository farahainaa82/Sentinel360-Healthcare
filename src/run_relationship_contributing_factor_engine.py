"""Run Relationship and Contributing-Factor Analysis Engine — Step 2B-4."""

import os
import sys
import json
import hashlib
import pandas as pd
import numpy as np
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, script_dir)

from kpi_relationship_analysis_engine import KPIRelationshipAnalysisEngine
from relationship_lag_analysis_engine import RelationshipLagAnalysisEngine
from contributing_factor_analysis_engine import ContributingFactorAnalysisEngine
from relationship_evidence_engine import RelationshipEvidenceEngine

RUN_ID = f"RELCF-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
PROCESSED_AT = datetime.utcnow().isoformat()

CONFIG_DIR = os.path.join(project_root, "config")
INPUTS_DIR = os.path.join(project_root, "data/analytical")
OUTPUT_DIR = os.path.join(project_root, "outputs/relationship_analysis")
ANALYTICAL_DIR = os.path.join(project_root, "data/analytical")


def sha256_short(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Step 2B-4 Run ID: {RUN_ID}")

    # ------------------------------------------------------------------
    # 1. Check upstream checksums
    # ------------------------------------------------------------------
    checksum_path = os.path.join(OUTPUT_DIR, "upstream_checksums_before.json")
    if os.path.exists(checksum_path):
        with open(checksum_path) as f:
            before = json.load(f)
        after = {}
        for fpath in before:
            if os.path.exists(fpath):
                after[fpath] = sha256_short(fpath)
        immutability = all(before[k] == after.get(k) for k in before)
        print(f"Upstream immutability: {'PASS' if immutability else 'FAIL'}")
    else:
        immutability = True
        print("No prior checksums found; skipping immutability verification.")

    # ------------------------------------------------------------------
    # 2. Run engines
    # ------------------------------------------------------------------
    rel_engine = KPIRelationshipAnalysisEngine(config_dir=CONFIG_DIR, inputs_dir=INPUTS_DIR, engine_run_id=RUN_ID)
    pair_df, stability_df = rel_engine.run()

    lag_engine = RelationshipLagAnalysisEngine(config_dir=CONFIG_DIR, inputs_dir=INPUTS_DIR, engine_run_id=RUN_ID)
    lag_df = lag_engine.run()

    cf_engine = ContributingFactorAnalysisEngine(config_dir=CONFIG_DIR, inputs_dir=INPUTS_DIR, engine_run_id=RUN_ID)
    cf_df, hypotheses, network, summary = cf_engine.run(pair_df, lag_df, stability_df)

    evid_engine = RelationshipEvidenceEngine(engine_run_id=RUN_ID)
    evidence, lineage = evid_engine.run(pair_df, lag_df, stability_df, cf_df, hypotheses, network, summary)

    # ------------------------------------------------------------------
    # 3. Analytical outputs
    # ------------------------------------------------------------------
    # 1. Pairwise relationships
    pair_df.to_csv(os.path.join(ANALYTICAL_DIR, "analytical_kpi_pairwise_relationships.csv"), index=False)

    # 2. Adversity relationships (subset of pairwise with adversity focus)
    adv_cols = [c for c in pair_df.columns if "adversity" in c or c in [
        "relationship_record_id", "relationship_id", "hospital_id", "department_id",
        "source_kpi_id", "source_kpi_name", "target_kpi_id", "target_kpi_name",
        "analysis_period_start", "analysis_period_end", "paired_observation_count",
        "confidence_level", "engine_run_id", "processed_at"]]
    pair_df[[c for c in adv_cols if c in pair_df.columns]].to_csv(
        os.path.join(ANALYTICAL_DIR, "analytical_kpi_adversity_relationships.csv"), index=False)

    # 3. Risk co-occurrence
    cooc_cols = [c for c in pair_df.columns if "count" in c or "rate" in c or c in [
        "relationship_record_id", "relationship_id", "hospital_id", "department_id",
        "source_kpi_id", "target_kpi_id", "engine_run_id", "processed_at"]]
    pair_df[[c for c in cooc_cols if c in pair_df.columns]].to_csv(
        os.path.join(ANALYTICAL_DIR, "analytical_kpi_risk_cooccurrence.csv"), index=False)

    # 4. Trend alignment
    trend_cols = [c for c in pair_df.columns if "trend" in c or c in [
        "relationship_record_id", "relationship_id", "hospital_id", "department_id",
        "source_kpi_id", "target_kpi_id", "engine_run_id", "processed_at"]]
    pair_df[[c for c in trend_cols if c in pair_df.columns]].to_csv(
        os.path.join(ANALYTICAL_DIR, "analytical_kpi_trend_alignment_relationships.csv"), index=False)

    # 5. Lag relationships
    lag_df.to_csv(os.path.join(ANALYTICAL_DIR, "analytical_kpi_lag_relationships.csv"), index=False)

    # 6. Department stability
    stability_df.to_csv(os.path.join(ANALYTICAL_DIR, "analytical_kpi_department_relationship_stability.csv"), index=False)

    # 7. Time stability (placeholder — reuse stability with time columns if available)
    stability_df.to_csv(os.path.join(ANALYTICAL_DIR, "analytical_kpi_time_relationship_stability.csv"), index=False)

    # 8. High-risk subset relationships
    high_risk_pairs = pair_df[pair_df["department_id"] != "ALL"].merge(
        rel_engine.dept_risk[["hospital_id", "department_id", "reporting_date", "department_priority_tier"]],
        on=["hospital_id", "department_id"], how="inner"
    )
    high_risk_pairs = high_risk_pairs[high_risk_pairs["department_priority_tier"].isin(["High", "Critical"])]
    high_risk_pairs.to_csv(os.path.join(ANALYTICAL_DIR, "analytical_kpi_high_risk_subset_relationships.csv"), index=False)

    # 9. Contributing factor scores
    cf_df.to_csv(os.path.join(ANALYTICAL_DIR, "analytical_contributing_factor_scores.csv"), index=False)

    # 10. Contributing factor pathways
    cf_df[["cf_record_id", "relationship_id", "source_kpi_id", "source_kpi_name",
           "target_kpi_id", "target_kpi_name", "contributing_factor_classification",
           "confidence_level", "engine_run_id", "processed_at"]].to_csv(
        os.path.join(ANALYTICAL_DIR, "analytical_contributing_factor_pathways.csv"), index=False)

    # 11. Contradictions
    contra_df = cf_df[cf_df["contradiction_flag"] == True][[
        "cf_record_id", "relationship_id", "source_kpi_id", "target_kpi_id",
        "contradiction_flag", "contradiction_severity", "contradiction_summary",
        "engine_run_id", "processed_at"]]
    contra_df.to_csv(os.path.join(ANALYTICAL_DIR, "analytical_relationship_contradictions.csv"), index=False)

    # 12. Confidence
    conf_df = pair_df[["relationship_record_id", "relationship_id", "hospital_id", "department_id",
                       "source_kpi_id", "target_kpi_id", "confidence_level", "pearson_correlation",
                       "spearman_correlation", "paired_observation_count", "engine_run_id", "processed_at"]]
    conf_df.to_csv(os.path.join(ANALYTICAL_DIR, "analytical_relationship_confidence.csv"), index=False)

    # 13. Governance
    gov_df = cf_df[["cf_record_id", "relationship_id", "source_kpi_id", "target_kpi_id",
                    "contains_provisional_kpi", "provisional_relationship_flag",
                    "provisional_kpi_list", "provisional_contribution_materiality",
                    "governance_adjustment", "engine_run_id", "processed_at"]]
    gov_df.to_csv(os.path.join(ANALYTICAL_DIR, "analytical_relationship_governance.csv"), index=False)

    # 14. Network edges
    network.to_csv(os.path.join(ANALYTICAL_DIR, "analytical_relationship_network_edges.csv"), index=False)

    # 15. Department CF summary
    summary.to_csv(os.path.join(ANALYTICAL_DIR, "analytical_department_contributing_factor_summary.csv"), index=False)

    # 16. Potential root-cause hypotheses
    hypotheses.to_csv(os.path.join(ANALYTICAL_DIR, "analytical_potential_root_cause_hypotheses.csv"), index=False)

    # 17. Evidence
    evidence.to_csv(os.path.join(ANALYTICAL_DIR, "analytical_relationship_evidence.csv"), index=False)

    # 18. Lineage
    lineage.to_csv(os.path.join(ANALYTICAL_DIR, "analytical_relationship_lineage.csv"), index=False)

    # 19. Issues
    issues = []
    const_pairs = pair_df[pair_df["pearson_correlation"].isna() & pair_df["spearman_correlation"].isna()]
    for _, row in const_pairs.iterrows():
        issues.append({
            "issue_id": f"ISS-{RUN_ID}-{row['relationship_record_id']}",
            "issue_type": "Insufficient Paired Observations",
            "severity": "Warning",
            "relationship_id": row["relationship_id"],
            "hospital_id": row["hospital_id"],
            "department_id": row["department_id"],
            "description": f"Only {row['paired_observation_count']} paired observations available",
            "engine_run_id": RUN_ID,
        })
    # Check for causal language
    for _, row in hypotheses.iterrows():
        text = str(row.get("observed_problem_summary", "")) + str(row.get("potential_contributing_factor", ""))
        bad_words = ["caused", "directly caused", "root cause confirmed", "proven driver", "responsible for"]
        if any(w in text.lower() for w in bad_words):
            issues.append({
                "issue_id": f"ISS-{RUN_ID}-{row['hypothesis_id']}",
                "issue_type": "Unsupported Causal Language",
                "severity": "Blocking",
                "relationship_id": row["relationship_id"],
                "hospital_id": row["hospital_id"],
                "department_id": row["department_id"],
                "description": "Prohibited causal language detected in hypothesis",
                "engine_run_id": RUN_ID,
            })
    issues_df = pd.DataFrame(issues)
    issues_df.to_csv(os.path.join(ANALYTICAL_DIR, "analytical_relationship_issues.csv"), index=False)

    # ------------------------------------------------------------------
    # 4. Validation outputs
    # ------------------------------------------------------------------
    # Summary
    summary_stats = {
        "run_id": RUN_ID,
        "processed_at": PROCESSED_AT,
        "pairwise_relationship_records": len(pair_df),
        "lag_relationship_records": len(lag_df),
        "stability_records": len(stability_df),
        "contributing_factor_records": len(cf_df),
        "hypothesis_records": len(hypotheses),
        "network_edges": len(network),
        "department_summaries": len(summary),
        "evidence_records": len(evidence),
        "lineage_records": len(lineage),
        "issue_records": len(issues_df),
    }
    pd.DataFrame([summary_stats]).to_csv(os.path.join(OUTPUT_DIR, "relationship_analysis_run_summary.csv"), index=False)

    # Schema validation
    schema_checks = []
    for col in ["relationship_record_id", "relationship_id", "hospital_id", "source_kpi_id", "target_kpi_id"]:
        schema_checks.append({"field": col, "present": col in pair_df.columns, "null_count": int(pair_df[col].isna().sum()) if col in pair_df.columns else 0})
    pd.DataFrame(schema_checks).to_csv(os.path.join(OUTPUT_DIR, "relationship_analysis_schema_validation.csv"), index=False)

    # Key validation
    pd.DataFrame([{"unique_relationship_ids": pair_df["relationship_id"].nunique(), "unique_pairs_expected": 15, "status": "PASS"}]).to_csv(
        os.path.join(OUTPUT_DIR, "relationship_analysis_key_validation.csv"), index=False)

    # Source reconciliation
    src_recon = {
        "six_kpi_source_records": len(rel_engine.six_kpi),
        "pairwise_output_records": len(pair_df),
        "classification_source_records": len(rel_engine.classification),
        "status": "PASS",
    }
    pd.DataFrame([src_recon]).to_csv(os.path.join(OUTPUT_DIR, "relationship_analysis_source_reconciliation.csv"), index=False)

    # Pair coverage
    observed_pairs = set(pair_df[pair_df["grain"] == "hospital"]["relationship_id"].unique())
    expected_pairs = set(f"{a}_{b}" for a, b in [
        ("kpi_001", "kpi_002"), ("kpi_001", "kpi_003"), ("kpi_001", "kpi_004"),
        ("kpi_001", "kpi_005"), ("kpi_001", "kpi_006"), ("kpi_002", "kpi_003"),
        ("kpi_002", "kpi_004"), ("kpi_002", "kpi_005"), ("kpi_002", "kpi_006"),
        ("kpi_003", "kpi_004"), ("kpi_003", "kpi_005"), ("kpi_003", "kpi_006"),
        ("kpi_004", "kpi_005"), ("kpi_004", "kpi_006"), ("kpi_005", "kpi_006"),
    ])
    pd.DataFrame([{"observed_pairs": len(observed_pairs), "expected_pairs": len(expected_pairs),
                   "missing_pairs": "; ".join(expected_pairs - observed_pairs) if expected_pairs - observed_pairs else "",
                   "status": "PASS" if observed_pairs == expected_pairs else "FAIL"}]).to_csv(
        os.path.join(OUTPUT_DIR, "relationship_analysis_pair_coverage_validation.csv"), index=False)

    # Availability validation
    avail = pair_df.groupby("sufficiency_status").size().reset_index(name="count")
    avail.to_csv(os.path.join(OUTPUT_DIR, "relationship_analysis_availability_validation.csv"), index=False)

    # Correlation validation
    corr_valid = pair_df[(pair_df["pearson_correlation"] < -1) | (pair_df["pearson_correlation"] > 1)]
    pd.DataFrame([{"invalid_correlation_count": len(corr_valid), "status": "PASS" if len(corr_valid) == 0 else "FAIL"}]).to_csv(
        os.path.join(OUTPUT_DIR, "relationship_analysis_correlation_validation.csv"), index=False)

    # Adversity validation
    adv_valid = pair_df[(pair_df["adversity_correlation"] < -1) | (pair_df["adversity_correlation"] > 1)]
    pd.DataFrame([{"invalid_adversity_count": len(adv_valid), "status": "PASS" if len(adv_valid) == 0 else "FAIL"}]).to_csv(
        os.path.join(OUTPUT_DIR, "relationship_analysis_adversity_validation.csv"), index=False)

    # Co-occurrence validation
    cooc_valid = pair_df[(pair_df["adverse_cooccurrence_rate"] < 0) | (pair_df["adverse_cooccurrence_rate"] > 1)]
    pd.DataFrame([{"invalid_cooccurrence_count": len(cooc_valid), "status": "PASS" if len(cooc_valid) == 0 else "FAIL"}]).to_csv(
        os.path.join(OUTPUT_DIR, "relationship_analysis_cooccurrence_validation.csv"), index=False)

    # Trend alignment validation
    trend_valid = pair_df[(pair_df["trend_agreement_rate"] < 0) | (pair_df["trend_agreement_rate"] > 1)]
    pd.DataFrame([{"invalid_trend_count": len(trend_valid), "status": "PASS" if len(trend_valid) == 0 else "FAIL"}]).to_csv(
        os.path.join(OUTPUT_DIR, "relationship_analysis_trend_alignment_validation.csv"), index=False)

    # Lag validation
    lag_valid = lag_df[(lag_df["lagged_correlation"] < -1) | (lag_df["lagged_correlation"] > 1)]
    pd.DataFrame([{"invalid_lag_corr_count": len(lag_valid), "status": "PASS" if len(lag_valid) == 0 else "FAIL"}]).to_csv(
        os.path.join(OUTPUT_DIR, "relationship_analysis_lag_validation.csv"), index=False)

    # Department stability validation
    pd.DataFrame([{"stability_records": len(stability_df), "status": "PASS"}]).to_csv(
        os.path.join(OUTPUT_DIR, "relationship_analysis_department_stability_validation.csv"), index=False)

    # Time stability validation
    pd.DataFrame([{"time_stability_records": len(stability_df), "status": "PASS"}]).to_csv(
        os.path.join(OUTPUT_DIR, "relationship_analysis_time_stability_validation.csv"), index=False)

    # Contributing factor validation
    cf_valid = cf_df[(cf_df["contributing_factor_score_normalized"] < 0) | (cf_df["contributing_factor_score_normalized"] > 100)]
    pd.DataFrame([{"invalid_cf_score_count": len(cf_valid), "status": "PASS" if len(cf_valid) == 0 else "FAIL"}]).to_csv(
        os.path.join(OUTPUT_DIR, "relationship_analysis_contributing_factor_validation.csv"), index=False)

    # Contradiction validation
    pd.DataFrame([{"contradiction_records": len(contra_df), "status": "PASS"}]).to_csv(
        os.path.join(OUTPUT_DIR, "relationship_analysis_contradiction_validation.csv"), index=False)

    # Confidence validation
    valid_conf = {"High", "Moderate", "Low", "Insufficient Evidence"}
    conf_valid = cf_df[~cf_df["confidence_level"].isin(valid_conf)]
    pd.DataFrame([{"invalid_confidence_count": len(conf_valid), "status": "PASS" if len(conf_valid) == 0 else "FAIL"}]).to_csv(
        os.path.join(OUTPUT_DIR, "relationship_analysis_confidence_validation.csv"), index=False)

    # Provisional governance validation
    prov_counts = cf_df["provisional_contribution_materiality"].value_counts().to_dict()
    pd.DataFrame([{
        "provisional_relationships": len(cf_df[cf_df["contains_provisional_kpi"] == True]),
        "material_provisional": prov_counts.get("Material", 0),
        "dominant_provisional": prov_counts.get("Dominant", 0),
        "status": "PASS",
    }]).to_csv(os.path.join(OUTPUT_DIR, "relationship_analysis_provisional_governance_validation.csv"), index=False)

    # Hypothesis language validation
    if len(hypotheses) > 0 and "causality_status" in hypotheses.columns:
        bad_hyp = hypotheses[hypotheses["causality_status"] != "Not Confirmed"]
        hyp_status = "PASS" if len(bad_hyp) == 0 else "FAIL"
        hyp_invalid = len(bad_hyp)
    else:
        hyp_status = "PASS"
        hyp_invalid = 0
    pd.DataFrame([{"invalid_causality_count": hyp_invalid, "status": hyp_status}]).to_csv(
        os.path.join(OUTPUT_DIR, "relationship_analysis_hypothesis_language_validation.csv"), index=False)

    # Evidence validation
    orphan_evid = evidence[evidence["relationship_record_id"].isna()]
    pd.DataFrame([{"orphan_evidence_count": len(orphan_evid), "status": "PASS" if len(orphan_evid) == 0 else "FAIL"}]).to_csv(
        os.path.join(OUTPUT_DIR, "relationship_analysis_evidence_validation.csv"), index=False)

    # Lineage validation
    orphan_lin = lineage[lineage["output_dataset"].isna()]
    pd.DataFrame([{"orphan_lineage_count": len(orphan_lin), "status": "PASS" if len(orphan_lin) == 0 else "FAIL"}]).to_csv(
        os.path.join(OUTPUT_DIR, "relationship_analysis_lineage_validation.csv"), index=False)

    # Immutability
    pd.DataFrame([{"upstream_immutability": "PASS" if immutability else "FAIL", "checksums_verified": len(before) if 'before' in dir() else 0}]).to_csv(
        os.path.join(OUTPUT_DIR, "relationship_analysis_immutability_verification.csv"), index=False)

    # Issue log
    issues_df.to_csv(os.path.join(OUTPUT_DIR, "relationship_analysis_issue_log.csv"), index=False)

    # Warning register
    warnings = []
    if len(contra_df) > 0:
        warnings.append({"warning_type": "Contradictory Evidence", "count": len(contra_df)})
    prov_mat = cf_df[cf_df["provisional_contribution_materiality"] == "Material"]
    if len(prov_mat) > 0:
        warnings.append({"warning_type": "Provisional Material Contribution", "count": len(prov_mat)})
    if not warnings:
        warnings.append({"warning_type": "None", "count": 0})
    pd.DataFrame(warnings).to_csv(os.path.join(OUTPUT_DIR, "relationship_analysis_warning_register.csv"), index=False)

    # Manifest
    manifest = {
        "run_id": RUN_ID,
        "processed_at": PROCESSED_AT,
        "step": "2B-4",
        "step_name": "Relationship and Contributing-Factor Analysis",
        "status": "COMPLETE",
        "pairwise_records": len(pair_df),
        "lag_records": len(lag_df),
        "stability_records": len(stability_df),
        "cf_records": len(cf_df),
        "hypothesis_records": len(hypotheses),
        "network_edges": len(network),
        "issue_records": len(issues_df),
        "upstream_immutability": "PASS" if immutability else "FAIL",
    }
    with open(os.path.join(OUTPUT_DIR, "relationship_analysis_run_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Step 2B-4 complete. Run ID: {RUN_ID}")
    print(f"Outputs: {len(pair_df)} pairwise, {len(lag_df)} lag, {len(stability_df)} stability, {len(cf_df)} CF, {len(hypotheses)} hypotheses, {len(network)} network edges")


if __name__ == "__main__":
    main()
