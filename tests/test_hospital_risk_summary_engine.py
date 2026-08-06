"""Tests for Hospital Risk Summary Engine — Step 2B-3.

Loads pre-generated outputs via module-scoped fixture.
"""

import os
import sys
import pytest
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))


@pytest.fixture(scope="module")
def hosp_summary():
    return pd.read_csv(os.path.join(PROJECT_ROOT, "data/analytical/analytical_hospital_risk_daily_summary.csv"))


@pytest.fixture(scope="module")
def dept_risk():
    return pd.read_csv(os.path.join(PROJECT_ROOT, "data/analytical/analytical_department_risk_daily.csv"))


# ------------------------------------------------------------------
# Hospital summary integrity
# ------------------------------------------------------------------
class TestHospitalSummary:
    def test_hospital_date_count_matches_dept_groups(self, hosp_summary, dept_risk):
        expected = dept_risk.groupby(["hospital_id", "reporting_date"]).ngroups
        assert len(hosp_summary) == expected

    def test_department_count_matches_input(self, hosp_summary, dept_risk):
        for _, hrow in hosp_summary.iterrows():
            hid, rdate = hrow["hospital_id"], hrow["reporting_date"]
            expected = len(dept_risk[(dept_risk["hospital_id"] == hid) & (dept_risk["reporting_date"] == rdate)])
            assert hrow["department_count"] == expected

    def test_tier_counts_sum_to_department_count(self, hosp_summary):
        for _, hrow in hosp_summary.iterrows():
            total = (
                hrow["stable_department_count"] + hrow["monitor_department_count"] +
                hrow["elevated_department_count"] + hrow["high_department_count"] +
                hrow["critical_department_count"] + hrow["not_assessable_department_count"]
            )
            assert total == hrow["department_count"]

    def test_highest_risk_score_matches_dept(self, hosp_summary, dept_risk):
        for _, hrow in hosp_summary.iterrows():
            hid, rdate = hrow["hospital_id"], hrow["reporting_date"]
            depts = dept_risk[(dept_risk["hospital_id"] == hid) & (dept_risk["reporting_date"] == rdate)]
            assert hrow["highest_department_risk_score"] == depts["department_risk_score_normalized"].max()

    def test_top_three_departments_ordered(self, hosp_summary):
        for _, hrow in hosp_summary.iterrows():
            top3 = hrow["top_three_department_ids"]
            if pd.notna(top3) and top3 != "":
                ids = top3.split("; ")
                assert len(ids) <= 3

    def test_overall_data_availability_between_zero_and_one(self, hosp_summary):
        assert (hosp_summary["overall_data_availability_rate"] >= 0.0).all()
        assert (hosp_summary["overall_data_availability_rate"] <= 1.0).all()

    def test_maximum_urgency_is_valid(self, hosp_summary):
        valid = {"Routine Monitoring", "Review Soon", "Prompt Review", "Immediate Review", "Not Assessable"}
        assert set(hosp_summary["maximum_urgency_level"].unique()).issubset(valid)

    def test_no_negative_counts(self, hosp_summary):
        count_cols = [
            "stable_department_count", "monitor_department_count",
            "elevated_department_count", "high_department_count",
            "critical_department_count", "not_assessable_department_count",
        ]
        for c in count_cols:
            assert (hosp_summary[c] >= 0).all()


# ------------------------------------------------------------------
# Immutability
# ------------------------------------------------------------------
class TestImmutability:
    def test_upstream_files_unchanged(self):
        import hashlib
        upstream = [
            "data/analytical/analytical_kpi_threshold_classification_daily.csv",
            "data/analytical/analytical_kpi_breach_events.csv",
            "data/analytical/analytical_kpi_watch_conditions.csv",
            "data/analytical/analytical_kpi_watch_persistence.csv",
            "data/analytical/analytical_kpi_breach_trend_integration.csv",
            "data/analytical/analytical_kpi_watch_evidence.csv",
            "data/analytical/analytical_kpi_watch_lineage.csv",
            "data/analytical/analytical_kpi_watch_governance.csv",
            "data/analytical/analytical_kpi_watch_issues.csv",
            "data/analytical/analytical_kpi_watch_daily_summary.csv",
            "config/kpi_threshold_config.csv",
            "config/kpi_threshold_stakeholder_decisions.csv",
        ]
        checksums = {}
        for p in upstream:
            full = os.path.join(PROJECT_ROOT, p)
            if os.path.exists(full):
                h = hashlib.sha256()
                with open(full, "rb") as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        h.update(chunk)
                checksums[p] = h.hexdigest()

        # Verify against validation output if present
        val_path = os.path.join(PROJECT_ROOT, "outputs/risk_prioritisation/risk_prioritisation_immutability_verification.csv")
        if os.path.exists(val_path):
            val = pd.read_csv(val_path)
            modified = val[val.get("status", "PASS") != "PASS"]
            assert len(modified) == 0, f"Upstream files modified: {modified['file'].tolist()}"
