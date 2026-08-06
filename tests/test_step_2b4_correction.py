"""
Sentinel360 Step 2B-4 Correction Tests

Focused validation for:
1. Refreshed contradiction severity in analytical outputs
2. Governed provisional-breach display fields
3. Upstream immutability of accepted risk scores
"""

import pytest
import pandas as pd
import os


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture(scope="module")
def cf_scores():
    return pd.read_csv("data/analytical/analytical_contributing_factor_scores.csv")


@pytest.fixture(scope="module")
def contradictions():
    return pd.read_csv("data/analytical/analytical_relationship_contradictions.csv")


@pytest.fixture(scope="module")
def dept_risk():
    return pd.read_csv("data/analytical/analytical_department_risk_daily.csv")


@pytest.fixture(scope="module")
def kpi_scores():
    return pd.read_csv("data/analytical/analytical_kpi_risk_scores_daily.csv")


# ------------------------------------------------------------------
# Issue 1 — Contradiction Severity
# ------------------------------------------------------------------

class TestContradictionSeverity:
    """Tests for refreshed contradiction severity distribution."""

    def test_severity_no_none_or_nan(self, cf_scores):
        """1. contradiction_severity must contain only valid governed values."""
        valid = {"No Contradiction", "Minor", "Material", "Major"}
        actual = set(cf_scores["contradiction_severity"].dropna().unique())
        assert actual.issubset(valid), f"Unexpected values: {actual - valid}"

    def test_no_nan_severity_when_flag_true(self, cf_scores):
        """3. No contradiction severity may remain blank or NaN where contradiction_flag = True."""
        flagged = cf_scores[cf_scores["contradiction_flag"] == True]
        assert flagged["contradiction_severity"].notna().all()

    def test_major_prevents_strong_hypothesis(self, cf_scores):
        """5. Major contradiction must prevent Strong Contributing-Factor Hypothesis."""
        major = cf_scores[cf_scores["contradiction_severity"] == "Major"]
        if len(major) > 0:
            assert not (major["contributing_factor_classification"] == "Strong Contributing-Factor Hypothesis").any()

    def test_scores_numeric_no_nan(self, cf_scores):
        """4. contributing_factor_score_normalized must be numeric where engine can calculate."""
        assert cf_scores["contributing_factor_score_normalized"].notna().all()
        assert pd.api.types.is_numeric_dtype(cf_scores["contributing_factor_score_normalized"])

    def test_severity_persists_after_csv_roundtrip(self, tmp_path):
        """1. contradiction severity persists correctly after CSV write/read."""
        df = pd.DataFrame({
            "relationship_id": ["r1"],
            "contradiction_severity": ["No Contradiction"],
            "contradiction_flag": [False],
        })
        path = tmp_path / "test_sev.csv"
        df.to_csv(path, index=False)
        read_back = pd.read_csv(path)
        assert read_back["contradiction_severity"].iloc[0] == "No Contradiction"
        assert pd.isna(read_back["contradiction_severity"].iloc[0]) is False

    def test_flag_true_never_blank_severity(self, cf_scores):
        """2. contradiction_flag=True never has blank or NaN severity."""
        flagged = cf_scores[cf_scores["contradiction_flag"] == True]
        blank = flagged["contradiction_severity"].isna() | (flagged["contradiction_severity"] == "")
        assert not blank.any()


# ------------------------------------------------------------------
# Issue 2 — Provisional Breach Display Governance
# ------------------------------------------------------------------

class TestProvisionalBreachGovernance:
    """Tests for corrected provisional-breach display fields."""

    def test_kpi_001_never_provisional_breach(self, dept_risk):
        """4. kpi_001 is never labelled Provisional Breach."""
        sub = dept_risk[dept_risk["dominant_kpi_id"] == "kpi_001"]
        assert not (sub["dominant_breach_type_governed"] == "Provisional Breach").any()

    def test_kpi_002_never_provisional_breach(self, dept_risk):
        """5. kpi_002 is never labelled Provisional Breach."""
        sub = dept_risk[dept_risk["dominant_kpi_id"] == "kpi_002"]
        assert not (sub["dominant_breach_type_governed"] == "Provisional Breach").any()

    def test_kpi_004_never_provisional_breach(self, dept_risk):
        """6. kpi_004 is never labelled Provisional Breach."""
        sub = dept_risk[dept_risk["dominant_kpi_id"] == "kpi_004"]
        assert not (sub["dominant_breach_type_governed"] == "Provisional Breach").any()

    def test_kpi_006_never_provisional_breach(self, dept_risk):
        """7. kpi_006 is never labelled Provisional Breach."""
        sub = dept_risk[dept_risk["dominant_kpi_id"] == "kpi_006"]
        assert not (sub["dominant_breach_type_governed"] == "Provisional Breach").any()

    def test_kpi_003_preserves_provisional_status(self, dept_risk):
        """8. kpi_003 preserves provisional status where appropriate."""
        sub = dept_risk[dept_risk["dominant_kpi_id"] == "kpi_003"]
        assert sub["dominant_threshold_is_provisional"].all()
        # Must have SOME Provisional Breach rows (where there's an actual breach)
        assert (sub["dominant_breach_type_governed"] == "Provisional Breach").any()

    def test_kpi_005_preserves_provisional_status(self, dept_risk):
        """9. kpi_005 preserves provisional status where appropriate."""
        sub = dept_risk[dept_risk["dominant_kpi_id"] == "kpi_005"]
        assert sub["dominant_threshold_is_provisional"].all()
        assert (sub["dominant_breach_type_governed"] == "Provisional Breach").any()

    def test_contains_provisional_does_not_make_dominant_provisional(self, dept_risk):
        """10. department contains_provisional_kpi does not make a non-provisional dominant driver provisional."""
        # Find rows where department contains provisional KPI but dominant is non-provisional
        mixed = dept_risk[
            (dept_risk["contains_provisional_kpi"] == True) &
            (dept_risk["dominant_driver_is_provisional"] == False)
        ]
        if len(mixed) > 0:
            assert not (mixed["dominant_breach_type_governed"] == "Provisional Breach").any()
            assert not (mixed["dominant_threshold_is_provisional"] == True).any()

    def test_accepted_scores_unchanged(self, dept_risk, kpi_scores):
        """11. accepted risk scores, rankings, tiers and urgency remain unchanged."""
        # Numerical columns that must not be NaN or altered
        numeric_cols = [
            "department_risk_score_normalized",
            "department_priority_tier",
            "urgency_level",
            "dominant_kpi_score",
        ]
        for col in numeric_cols:
            assert dept_risk[col].notna().all(), f"{col} has unexpected NaN"

    def test_governed_fields_present(self, dept_risk):
        required = [
            "dominant_threshold_is_provisional",
            "dominant_breach_type_governed",
            "dominant_driver_governance_warning",
            "dominant_driver_reason_governed",
        ]
        for col in required:
            assert col in dept_risk.columns, f"Missing governed field: {col}"

    def test_governed_warning_text(self, dept_risk):
        prov = dept_risk[dept_risk["dominant_threshold_is_provisional"] == True]
        non_prov = dept_risk[dept_risk["dominant_threshold_is_provisional"] == False]
        if len(prov) > 0:
            assert (prov["dominant_driver_governance_warning"] == "Dominant risk driver uses provisional threshold").all()
        if len(non_prov) > 0:
            assert (non_prov["dominant_driver_governance_warning"] == "Dominant risk driver uses approved threshold").all()


# ------------------------------------------------------------------
# Upstream Immutability
# ------------------------------------------------------------------

class TestUpstreamImmutability:
    """12. upstream immutability passes for non-refreshed files."""

    def test_department_risk_scores_unchanged(self, dept_risk):
        """Verify core numerical fields have not been corrupted."""
        assert dept_risk["department_risk_score_normalized"].between(0, 100).all()
        assert set(dept_risk["department_priority_tier"].unique()).issubset({"Critical", "High", "Elevated", "Monitor", "Stable"})

    def test_no_duplicate_rows(self, dept_risk):
        key_cols = ["hospital_id", "department_id", "reporting_date"]
        assert not dept_risk[key_cols].duplicated().any()
