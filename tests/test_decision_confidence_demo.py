"""
Tests for the Demo Decision Confidence Lookup helper.

Validates the read-only lookup against
config/decision_confidence_demo_config.csv and the structured
result contract (status, OK / NOT_CONFIGURED / DUPLICATE_CONFIG /
INVALID_INPUT / CONFIG_NOT_FOUND / CONFIG_ERROR).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

# Ensure src/ is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from decision_confidence_demo import (  # noqa: E402
    DecisionConfidenceDemoLookup,
    DecisionConfidenceResult,
    STATUS_OK,
    STATUS_NOT_CONFIGURED,
    STATUS_DUPLICATE_CONFIG,
    STATUS_INVALID_INPUT,
    STATUS_CONFIG_NOT_FOUND,
    STATUS_CONFIG_ERROR,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

REAL_CONFIG_PATH = (
    PROJECT_ROOT / "config" / "decision_confidence_demo_config.csv"
)


@pytest.fixture
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture
def real_lookup(project_root: Path) -> DecisionConfidenceDemoLookup:
    return DecisionConfidenceDemoLookup(base_dir=project_root)


@pytest.fixture
def write_csv(tmp_path: Path):
    """Helper to write a minimal demo confidence CSV to a temp path."""
    def _write(name: str, df: pd.DataFrame) -> Path:
        path = tmp_path / name
        df.to_csv(path, index=False)
        return path
    return _write


# ---------------------------------------------------------------------------
# 1. valid Aug 2025 + kpi_001 returns MODERATE
# ---------------------------------------------------------------------------

def test_aug_2025_kpi_001_returns_moderate(real_lookup):
    res = real_lookup.get(2025, 8, "kpi_001")
    assert isinstance(res, DecisionConfidenceResult)
    assert res.status == STATUS_OK
    assert res.forecast_year == 2025
    assert res.forecast_month == 8
    assert res.kpi_id == "kpi_001"
    assert res.confidence_level == "MODERATE"


# ---------------------------------------------------------------------------
# 2. valid Aug 2025 + kpi_003 returns HIGH
# ---------------------------------------------------------------------------

def test_aug_2025_kpi_003_returns_high(real_lookup):
    res = real_lookup.get(2025, 8, "kpi_003")
    assert res.status == STATUS_OK
    assert res.confidence_level == "HIGH"


# ---------------------------------------------------------------------------
# 3. valid Dec 2025 + kpi_005 returns LOW
# ---------------------------------------------------------------------------

def test_dec_2025_kpi_005_returns_low(real_lookup):
    res = real_lookup.get(2025, 12, "kpi_005")
    assert res.status == STATUS_OK
    assert res.confidence_level == "LOW"


# ---------------------------------------------------------------------------
# 4. returned decision_posture matches config
# ---------------------------------------------------------------------------

def test_returned_decision_posture_matches_config(real_lookup):
    res = real_lookup.get(2025, 8, "kpi_003")
    assert res.status == STATUS_OK
    assert res.decision_posture == "PROCEED WITH REVIEW"


# ---------------------------------------------------------------------------
# 5. returned decision_implication matches config
# ---------------------------------------------------------------------------

def test_returned_decision_implication_matches_config(real_lookup):
    res = real_lookup.get(2025, 8, "kpi_003")
    assert res.status == STATUS_OK
    assert res.decision_implication == (
        "Evidence is sufficiently consistent to support management consideration"
    )


# ---------------------------------------------------------------------------
# 6. returned evidence_action matches config
# ---------------------------------------------------------------------------

def test_returned_evidence_action_matches_config(real_lookup):
    res = real_lookup.get(2025, 8, "kpi_003")
    assert res.status == STATUS_OK
    assert res.evidence_action == (
        "Proceed through normal management review and approval"
    )


# ---------------------------------------------------------------------------
# 7. source_type = DEMO_GOVERNANCE
# ---------------------------------------------------------------------------

def test_source_type_is_demo_governance(real_lookup):
    # Probe several rows to confirm consistency across the real config
    samples = [(2025, 8, "kpi_001"), (2025, 9, "kpi_002"), (2025, 12, "kpi_006")]
    for year, month, kpi in samples:
        res = real_lookup.get(year, month, kpi)
        assert res.status == STATUS_OK
        assert res.source_type == "DEMO_GOVERNANCE"


# ---------------------------------------------------------------------------
# 8. missing month/KPI combination returns NOT_CONFIGURED
# ---------------------------------------------------------------------------

def test_missing_combination_returns_not_configured(real_lookup):
    res = real_lookup.get(2025, 8, "kpi_999")
    assert res.status == STATUS_NOT_CONFIGURED
    assert res.confidence_level is None
    assert res.decision_posture is None
    assert res.decision_implication is None
    assert res.evidence_action is None
    # Context fields are preserved
    assert res.forecast_year == 2025
    assert res.forecast_month == 8
    assert res.kpi_id == "kpi_999"
    assert "configured" in (res.message or "").lower()


# ---------------------------------------------------------------------------
# 9. invalid month handled safely
# ---------------------------------------------------------------------------

def test_invalid_month_returns_invalid_input(real_lookup):
    # Month 13 is out of range
    res = real_lookup.get(2025, 13, "kpi_001")
    assert res.status == STATUS_INVALID_INPUT
    assert res.confidence_level is None

    # Non-integer month
    res2 = real_lookup.get(2025, "August", "kpi_001")
    assert res2.status == STATUS_INVALID_INPUT
    assert res2.confidence_level is None


# ---------------------------------------------------------------------------
# 10. missing KPI handled safely
# ---------------------------------------------------------------------------

def test_missing_kpi_returns_invalid_input(real_lookup):
    res = real_lookup.get(2025, 8, None)
    assert res.status == STATUS_INVALID_INPUT
    assert res.confidence_level is None

    res2 = real_lookup.get(2025, 8, "")
    assert res2.status == STATUS_INVALID_INPUT
    assert res2.confidence_level is None

    res3 = real_lookup.get(2025, 8, "   ")
    assert res3.status == STATUS_INVALID_INPUT
    assert res3.confidence_level is None


# ---------------------------------------------------------------------------
# 11. helper does not infer confidence from KPI values
# ---------------------------------------------------------------------------

def test_helper_does_not_infer_confidence_from_kpi_values(tmp_path, write_csv):
    """Inject a config where the only active row is MODERATE for kpi_010.

    The helper must return NOT_CONFIGURED for an unknown KPI, not a
    default or derived confidence level.
    """
    df = pd.DataFrame(
        [
            {
                "forecast_year": 2025,
                "forecast_month": 8,
                "kpi_id": "kpi_010",
                "confidence_level": "MODERATE",
                "decision_posture": "REVIEW ASSUMPTIONS",
                "decision_implication": "Evidence supports the proposed action",
                "evidence_action": "Review assumptions",
                "source_type": "DEMO_GOVERNANCE",
                "active_flag": "TRUE",
            }
        ]
    )
    path = write_csv("demo_only_mod.csv", df)
    lookup = DecisionConfidenceDemoLookup(config_path=path)

    # Unknown KPI must NOT be inferred; should be NOT_CONFIGURED, not MODERATE.
    res_unknown = lookup.get(2025, 8, "kpi_999")
    assert res_unknown.status == STATUS_NOT_CONFIGURED
    assert res_unknown.confidence_level is None
    assert res_unknown.decision_posture is None
    assert res_unknown.evidence_action is None

    # Known KPI returns the configured value.
    res_known = lookup.get(2025, 8, "kpi_010")
    assert res_known.status == STATUS_OK
    assert res_known.confidence_level == "MODERATE"


# ---------------------------------------------------------------------------
# 12. duplicate active config is rejected safely if injected
# ---------------------------------------------------------------------------

def test_duplicate_active_config_rejected_safely(tmp_path, write_csv):
    """Inject two active rows for the same (year, month, kpi).

    The helper must return DUPLICATE_CONFIG and not silently pick one.
    """
    df = pd.DataFrame(
        [
            {
                "forecast_year": 2025,
                "forecast_month": 8,
                "kpi_id": "kpi_001",
                "confidence_level": "MODERATE",
                "decision_posture": "REVIEW ASSUMPTIONS",
                "decision_implication": "First row",
                "evidence_action": "First action",
                "source_type": "DEMO_GOVERNANCE",
                "active_flag": "TRUE",
            },
            {
                "forecast_year": 2025,
                "forecast_month": 8,
                "kpi_id": "kpi_001",
                "confidence_level": "HIGH",
                "decision_posture": "PROCEED WITH REVIEW",
                "decision_implication": "Second row",
                "evidence_action": "Second action",
                "source_type": "DEMO_GOVERNANCE",
                "active_flag": "TRUE",
            },
        ]
    )
    path = write_csv("demo_duplicates.csv", df)
    lookup = DecisionConfidenceDemoLookup(config_path=path)

    res = lookup.get(2025, 8, "kpi_001")
    assert res.status == STATUS_DUPLICATE_CONFIG
    # No confidence may be returned in a duplicate-config situation.
    assert res.confidence_level is None
    assert res.decision_posture is None
    assert res.evidence_action is None
    # Context fields preserved.
    assert res.forecast_year == 2025
    assert res.forecast_month == 8
    assert res.kpi_id == "kpi_001"


# ---------------------------------------------------------------------------
# Additional governance coverage (still aligned with spec)
# ---------------------------------------------------------------------------

def test_missing_config_file_returns_config_not_found(tmp_path):
    lookup = DecisionConfidenceDemoLookup(
        config_path=tmp_path / "does_not_exist.csv"
    )
    res = lookup.get(2025, 8, "kpi_001")
    assert res.status == STATUS_CONFIG_NOT_FOUND
    assert res.confidence_level is None


def test_malformed_config_returns_config_error(tmp_path, write_csv):
    """Required columns missing -> CONFIG_ERROR."""
    df = pd.DataFrame(
        {
            "forecast_year": [2025],
            "forecast_month": [8],
            "kpi_id": ["kpi_001"],
            # Other required columns intentionally omitted.
        }
    )
    path = write_csv("malformed.csv", df)
    lookup = DecisionConfidenceDemoLookup(config_path=path)
    res = lookup.get(2025, 8, "kpi_001")
    assert res.status == STATUS_CONFIG_ERROR
    assert res.confidence_level is None


def test_inactive_row_is_not_returned(tmp_path, write_csv):
    """Rows with active_flag != TRUE must be ignored."""
    df = pd.DataFrame(
        [
            {
                "forecast_year": 2025,
                "forecast_month": 8,
                "kpi_id": "kpi_001",
                "confidence_level": "MODERATE",
                "decision_posture": "REVIEW ASSUMPTIONS",
                "decision_implication": "Inactive row",
                "evidence_action": "Ignore",
                "source_type": "DEMO_GOVERNANCE",
                "active_flag": "FALSE",
            }
        ]
    )
    path = write_csv("inactive.csv", df)
    lookup = DecisionConfidenceDemoLookup(config_path=path)
    res = lookup.get(2025, 8, "kpi_001")
    assert res.status == STATUS_NOT_CONFIGURED
    assert res.confidence_level is None
