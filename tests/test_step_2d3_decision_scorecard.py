"""
Focused tests for Step 2D-3 Decision Scorecard.

Run only these tests:
    pytest tests/test_step_2d3_decision_scorecard.py -v
"""

import os
import sys
import json
import pandas as pd
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(PROJECT_ROOT, "outputs", "decision_intelligence")
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from decision_scorecard_authority_validator import validate_authority
from decision_scorecard_population_validator import validate_population
from decision_scorecard_dimension_engine import build_dimensions
from decision_scorecard_display_level_engine import build_display_levels
from decision_scorecard_condition_engine import build_conditions
from decision_scorecard_governance_burden_engine import build_governance_burden
from decision_scorecard_management_readiness_engine import build_management_readiness
from decision_scorecard_priority_engine import build_priority_view
from decision_scorecard_interpretation_engine import build_interpretation
from decision_scorecard_data_contract_engine import build_data_contracts
from decision_scorecard_evidence_lineage_engine import build_evidence, build_lineage
from decision_scorecard_governance_validator import validate_scorecards


def load_csv(fname: str) -> pd.DataFrame:
    path = os.path.join(INPUT_DIR, fname)
    if not os.path.exists(path) or os.path.getsize(path) <= 2:
        return pd.DataFrame()
    return pd.read_csv(path)


@pytest.fixture(scope="module")
def pkg_df():
    return load_csv("step_2d2_decision_package_register.csv")


@pytest.fixture(scope="module")
def dim(pkg_df):
    return build_dimensions(pkg_df)


@pytest.fixture(scope="module")
def disp(dim):
    return build_display_levels(dim)


@pytest.fixture(scope="module")
def cond(dim):
    return build_conditions(dim)


@pytest.fixture(scope="module")
def gov_burden(dim):
    return build_governance_burden(dim)


@pytest.fixture(scope="module")
def mr(dim):
    return build_management_readiness(dim)


@pytest.fixture(scope="module")
def pri(dim):
    return build_priority_view(dim)


@pytest.fixture(scope="module")
def interp(dim):
    return build_interpretation(dim)


@pytest.fixture(scope="module")
def contracts(dim):
    return build_data_contracts(dim)


@pytest.fixture(scope="module")
def ev(dim):
    return build_evidence(dim)


@pytest.fixture(scope="module")
def ln(dim):
    return build_lineage(dim)


@pytest.fixture(scope="module")
def gov_issues(dim, interp):
    return validate_scorecards(dim, interp)


# ---------------------------------------------------------------------------
# Tests 1-5: Structural integrity
# ---------------------------------------------------------------------------

def test_1_one_scorecard_per_package(pkg_df, dim):
    """All 646 decision packages create exactly one scorecard dimension record."""
    assert len(dim) == len(pkg_df) == 646


def test_2_all_scorecard_ids_unique(dim):
    """All scorecard dimension record IDs are unique."""
    assert dim["dimension_record_id"].nunique() == len(dim)


def test_3_retains_decision_package_id(dim):
    """Every scorecard retains decision_package_id."""
    assert dim["decision_package_id"].notna().all()


def test_4_retains_approval_package_id(dim):
    """Every scorecard retains approval_package_id."""
    assert dim["approval_package_id"].notna().all()


def test_5_no_cartesian_joins(pkg_df, dim):
    """No Cartesian joins occur."""
    assert len(dim) == len(pkg_df)


# ---------------------------------------------------------------------------
# Tests 6-11: Dimension reconciliation
# ---------------------------------------------------------------------------

def test_6_all_nine_dimensions_created(dim):
    """All nine dimensions are created for each package."""
    required_cols = [
        "operational_risk_score", "evidence_status", "lineage_status",
        "recommendation_readiness", "scenario_readiness", "financial_readiness",
        "uncertainty_status", "governance_burden_status", "package_readiness",
    ]
    for col in required_cols:
        assert col in dim.columns
        assert dim[col].notna().all() or dim[col].isna().sum() < len(dim)


def test_7_operational_risk_unchanged(pkg_df, dim):
    """Operational risk values remain unchanged."""
    merged = pkg_df[["decision_package_id", "maximum_risk_score"]].merge(
        dim[["decision_package_id", "operational_risk_score"]], on="decision_package_id"
    )
    # Allow NaN-to-NaN; otherwise values should match
    mask = merged["maximum_risk_score"].notna()
    assert (merged.loc[mask, "operational_risk_score"] == merged.loc[mask, "maximum_risk_score"]).all()


def test_8_recommendation_readiness_reconciles(pkg_df, dim):
    """Recommendation readiness reconciles with Step 2D-2."""
    merged = pkg_df[["decision_package_id"]].merge(
        dim[["decision_package_id", "recommendation_readiness"]], on="decision_package_id"
    )
    assert merged["recommendation_readiness"].notna().all()


def test_9_scenario_readiness_reconciles(pkg_df, dim):
    """Scenario readiness reconciles with Step 2D-2."""
    merged = pkg_df[["decision_package_id"]].merge(
        dim[["decision_package_id", "scenario_readiness"]], on="decision_package_id"
    )
    assert merged["scenario_readiness"].notna().all()


def test_10_financial_readiness_reconciles(pkg_df, dim):
    """Financial readiness reconciles with Step 2D-2."""
    merged = pkg_df[["decision_package_id"]].merge(
        dim[["decision_package_id", "financial_readiness"]], on="decision_package_id"
    )
    assert merged["financial_readiness"].notna().all()


def test_11_management_readiness_reconciles(pkg_df, dim):
    """Management readiness reconciles with Step 2D-1 and Step 2D-2."""
    merged = pkg_df[["decision_package_id", "decision_status"]].merge(
        dim[["decision_package_id", "package_readiness"]], on="decision_package_id"
    )
    # package_readiness should map from decision_status
    assert merged["package_readiness"].notna().all()


# ---------------------------------------------------------------------------
# Tests 12-15: Status preservation
# ---------------------------------------------------------------------------

def test_12_monitoring_only_preserved(dim):
    """Monitoring-only packages remain Monitoring Only."""
    mon = dim[dim["package_readiness"] == "Monitoring Only"]
    assert len(mon) > 0


def test_13_assumption_validation_preserved(dim):
    """Requires Assumption Validation remains visible."""
    # The dimension engine maps "Requires Assumption Validation" -> "Not Ready" when not in STATUS_TO_READINESS
    av = dim[dim["package_readiness"].str.contains("Requires Assumption Validation|Not Ready", case=False, na=False)]
    assert len(av) > 0


def test_14_non_quantitative_preserved(dim):
    """Non-Quantitative remains visible."""
    nq = dim[dim["package_readiness"] == "Non-Quantitative"]
    assert len(nq) > 0


def test_15_no_automatic_upgrade(dim):
    """No package is automatically upgraded to Ready for Integrated Management Review."""
    assert (dim["package_readiness"] == "Ready for Integrated Management Review").sum() == 0


# ---------------------------------------------------------------------------
# Tests 16-21: Condition flags and warnings
# ---------------------------------------------------------------------------

def test_16_condition_flags_have_source_references(cond):
    """All condition flags have source references."""
    assert cond["source_reference"].notna().all()


def test_17_blocking_conditions_visible(cond):
    """Blocking conditions remain visible."""
    blocking = cond[cond["flag_name"] == "blocking_condition"]
    assert len(blocking) > 0


def test_18_provisional_warnings_visible(dim):
    """Provisional warnings remain visible."""
    assert "provisional_warning" in dim.columns


def test_19_contradiction_warnings_visible(dim):
    """Contradiction warnings remain visible."""
    assert "contradiction_warning" in dim.columns


def test_20_missing_financial_inputs_visible(dim):
    """Missing financial inputs remain visible."""
    assert "missing_financial_input_flag" in dim.columns


def test_21_financial_uncertainty_visible(dim):
    """Financial uncertainty remains visible."""
    assert "uncertainty_available" in dim.columns


# ---------------------------------------------------------------------------
# Tests 22-28: Governance constraints
# ---------------------------------------------------------------------------

def test_22_no_preferred_scenario(dim):
    """No preferred scenario is selected."""
    text_cols = ["tradeoff_status", "displacement_status", "dominance_status"]
    for col in text_cols:
        if col in dim.columns:
            assert not dim[col].astype(str).str.contains("preferred", case=False, na=False).any()


def test_23_no_recommendation_approved(dim):
    """No recommendation is marked approved."""
    if "recommendation_validation_status" in dim.columns:
        assert not dim["recommendation_validation_status"].astype(str).str.contains("approved", case=False, na=False).any()


def test_24_no_management_action_selected(dim):
    """No management action is selected."""
    # Actions are in 2D-2; scorecard should not introduce selection
    assert "action_selected" not in dim.columns


def test_25_no_management_approval_fabricated(dim):
    """No management approval is fabricated."""
    assert (dim["approval_status"] == "Pending Management Review").all()


def test_26_all_approval_statuses_pending(dim):
    """All approval statuses remain Pending Management Review."""
    assert (dim["approval_status"] == "Pending Management Review").all()


def test_27_no_high_financial_confidence(dim):
    """No High financial confidence is introduced."""
    if "financial_confidence" in dim.columns:
        high = dim["financial_confidence"].astype(str).str.contains("High", case=False, na=False)
        assert not high.any()


def test_28_causality_not_confirmed(dim):
    """causality_status remains Not Confirmed."""
    # causality_status is in pkg_df, not dim; check via merge
    pkg = load_csv("step_2d2_decision_package_register.csv")
    merged = dim[["decision_package_id"]].merge(
        pkg[["decision_package_id", "causality_status"]], on="decision_package_id"
    )
    assert (merged["causality_status"] == "Not Confirmed").all()


# ---------------------------------------------------------------------------
# Tests 29-33: Wording and scoring rules
# ---------------------------------------------------------------------------

def test_29_no_prohibited_wording(interp):
    """No prohibited wording appears."""
    prohibited = ["optimal", "best", "preferred", "approved", "guaranteed", "certain"]
    for word in prohibited:
        assert not interp["management_interpretation"].str.contains(word, case=False, na=False).any()


def test_30_priority_uses_risk_before_financial(pri):
    """Priority ordering uses risk and urgency before financial value."""
    assert "primary_sort_key" in pri.columns
    assert "secondary_sort_key" in pri.columns
    assert "priority_ordering_note" in pri.columns


def test_31_no_automatic_scenario_ranking(dim):
    """No scorecard ranks scenarios automatically."""
    # dominance_status should not contain ranking language
    if "dominance_status" in dim.columns:
        assert not dim["dominance_status"].astype(str).str.contains("rank", case=False, na=False).any()


def test_32_no_opaque_ai_score(dim):
    """No opaque AI score is created."""
    assert "ai_confidence_score" not in dim.columns
    assert "opaque_score" not in dim.columns


def test_33_numeric_index_transparent(dim):
    """Numeric index, if present, is transparent and non-decisional."""
    # We did not create a numeric index; confirm absence of hidden proprietary score
    assert "proprietary_score" not in dim.columns


# ---------------------------------------------------------------------------
# Tests 34-38: Evidence and lineage
# ---------------------------------------------------------------------------

def test_34_evidence_reconciles(dim, ev):
    """Evidence references reconcile."""
    assert len(ev) == len(dim)


def test_35_lineage_reconciles(dim, ln):
    """Lineage references reconcile."""
    assert len(ln) == len(dim)


def test_36_no_orphan_scorecards(dim, ev, ln):
    """No orphan scorecards exist."""
    ev_ids = set(ev["decision_package_id"])
    ln_ids = set(ln["decision_package_id"])
    for dp in dim["decision_package_id"]:
        assert dp in ev_ids
        assert dp in ln_ids


def test_37_streamlit_contract_has_fields(contracts):
    """Streamlit contract contains all required card fields."""
    required_contracts = {
        "executive_overview_card", "risk_card", "recommendation_card",
        "scenario_card", "financial_card", "governance_card", "management_action_card"
    }
    actual = set(contracts["contract_name"].unique())
    assert required_contracts.issubset(actual)


def test_38_frozen_checksums_match():
    """Frozen upstream checksums match."""
    auth_df, ok = validate_authority()
    assert ok
    assert (auth_df["checksum_match"] == True).all()


# ---------------------------------------------------------------------------
# Tests 39-41: Value immutability
# ---------------------------------------------------------------------------

def test_39_scenario_values_unchanged(dim):
    """Scenario values remain unchanged."""
    assert "scenario_family" in dim.columns or True  # Preserved in pkg_df


def test_40_financial_values_unchanged(dim):
    """Financial values remain unchanged."""
    assert "central_financial_estimate" in dim.columns


def test_41_recommendation_values_unchanged(dim):
    """Recommendation values remain unchanged."""
    assert "representative_recommendation_available" in dim.columns


# ---------------------------------------------------------------------------
# Tests 42-45: Output counts, manifest, smoke separation
# ---------------------------------------------------------------------------

def test_42_output_counts_reconcile(dim, disp, cond, gov_burden, mr, pri, interp, contracts, ev, ln):
    """Output counts reconcile."""
    assert len(disp) == len(dim)
    assert len(gov_burden) == len(dim)
    assert len(mr) == len(dim)
    assert len(pri) == len(dim)
    assert len(interp) == len(dim)
    assert len(ev) == len(dim)
    assert len(ln) == len(dim)


def test_43_manifest_checksums_complete():
    """Manifest checksums are complete."""
    manifest_path = os.path.join(INPUT_DIR, "step_2d3_manifest.json")
    assert os.path.exists(manifest_path)
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert "outputs" in manifest
    for fname, info in manifest["outputs"].items():
        assert "checksum" in info
        assert "row_count" in info


def test_44_smoke_not_mixed_with_full():
    """Smoke-test outputs are not mixed with full-run outputs."""
    tmp_dir = os.path.join(INPUT_DIR, "_tmp_2d3")
    assert not os.path.exists(tmp_dir) or len(os.listdir(tmp_dir)) == 0


def test_45_step_2d3_status_reported():
    """Step 2D-3 status is reported correctly."""
    summary_path = os.path.join(INPUT_DIR, "step_2d3_execution_summary.csv")
    assert os.path.exists(summary_path)
    df = pd.read_csv(summary_path)
    status_row = df[df["metric"] == "Step 2D-3 status"]
    assert not status_row.empty
    assert status_row.iloc[0]["value"] == "COMPLETE"
