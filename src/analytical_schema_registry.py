"""
Sentinel360 Healthcare — Analytical Schema Registry

Defines future output schemas for the analytical layer.
No output CSV files are generated in Step 2A-1.

Step: 2A-1
"""

from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# 1. Schema Builder
# ---------------------------------------------------------------------------

def _build_schema(
    required_fields: List[str],
    optional_fields: List[str],
    boolean_fields: List[str] = None,
    unique_constraints: List[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "required_fields": required_fields,
        "optional_fields": optional_fields,
        "boolean_fields": boolean_fields or [],
        "unique_constraints": unique_constraints or [],
    }


# ---------------------------------------------------------------------------
# 2. Analytical Output Schemas
# ---------------------------------------------------------------------------

ANALYTICAL_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "analytical_kpi_daily": _build_schema(
        required_fields=[
            "analytical_record_id",
            "hospital_id",
            "department_id",
            "reporting_date",
            "reporting_month",
            "reporting_year",
            "kpi_id",
            "kpi_name",
            "domain",
            "numerator_value",
            "denominator_value",
            "kpi_value",
            "unit",
            "calculation_status",
            "readiness_status",
            "threshold_version",
            "configuration_version",
            "data_confidence_level",
            "source_dataset",
            "calculation_run_id",
            "calculated_at",
        ],
        optional_fields=[
            "threshold_assignment",
            "exclusion_count",
            "confidence_score",
            "completeness_pct",
            "freshness_days",
        ],
        boolean_fields=[],
        unique_constraints=[["analytical_record_id"], ["hospital_id", "department_id", "reporting_date", "kpi_id"]],
    ),
    "analytical_kpi_monthly": _build_schema(
        required_fields=[
            "analytical_record_id",
            "hospital_id",
            "department_id",
            "reporting_month",
            "reporting_year",
            "kpi_id",
            "kpi_name",
            "domain",
            "numerator_value",
            "denominator_value",
            "kpi_value",
            "unit",
            "calculation_status",
            "readiness_status",
            "threshold_version",
            "configuration_version",
            "data_confidence_level",
            "source_dataset",
            "calculation_run_id",
            "calculated_at",
        ],
        optional_fields=[
            "days_in_month",
            "partial_month_flag",
        ],
        boolean_fields=["partial_month_flag"],
        unique_constraints=[["analytical_record_id"], ["hospital_id", "department_id", "reporting_month", "reporting_year", "kpi_id"]],
    ),
    "analytical_kpi_evidence": _build_schema(
        required_fields=[
            "evidence_id",
            "analytical_record_id",
            "kpi_id",
            "evidence_type",  # numerator, denominator
            "source_dataset",
            "source_field",
            "source_value",
            "source_record_count",
            "aggregation_method",
            "eligibility_applied",
            "calculation_run_id",
        ],
        optional_fields=[
            "source_record_ids",
            "exclusion_reason",
        ],
        boolean_fields=["eligibility_applied"],
        unique_constraints=[["evidence_id"]],
    ),
    "analytical_kpi_exclusions": _build_schema(
        required_fields=[
            "exclusion_id",
            "analytical_record_id",
            "kpi_id",
            "exclusion_reason",
            "source_dataset",
            "source_record_id",
            "field_name",
            "field_value",
            "calculation_run_id",
        ],
        optional_fields=[
            "exclusion_rule_reference",
        ],
        boolean_fields=[],
        unique_constraints=[["exclusion_id"]],
    ),
    "analytical_kpi_lineage": _build_schema(
        required_fields=[
            "lineage_record_id",
            "output_record_id",
            "output_dataset",
            "source_dataset",
            "source_record_id",
            "transformation_name",
            "transformation_version",
            "kpi_id",
            "calculation_run_id",
            "processed_datetime",
        ],
        optional_fields=[
            "source_field_mapping",
        ],
        boolean_fields=[],
        unique_constraints=[["lineage_record_id"]],
    ),
    "analytical_kpi_issues": _build_schema(
        required_fields=[
            "issue_id",
            "issue_type",
            "severity",
            "issue_description",
            "source_dataset",
            "kpi_id",
            "field_name",
            "resolution_status",
            "created_at",
        ],
        optional_fields=[
            "resolved_at",
            "resolved_by",
        ],
        boolean_fields=[],
        unique_constraints=[["issue_id"]],
    ),
    "analytical_kpi_audit": _build_schema(
        required_fields=[
            "audit_id",
            "operation",
            "dataset_name",
            "record_count",
            "calculation_run_id",
            "performed_by",
            "performed_at",
        ],
        optional_fields=[
            "notes",
        ],
        boolean_fields=[],
        unique_constraints=[["audit_id"]],
    ),
    "analytical_kpi_run_manifest": _build_schema(
        required_fields=[
            "calculation_run_id",
            "run_type",
            "start_time",
            "end_time",
            "status",
            "kpi_ids",
            "issue_count",
            "exclusion_count",
            "output_datasets",
            "phase1_immutability_verified",
            "phase1_checksums_match",
        ],
        optional_fields=[
            "configuration_versions",
            "threshold_versions",
        ],
        boolean_fields=["phase1_immutability_verified", "phase1_checksums_match"],
        unique_constraints=[["calculation_run_id"]],
    ),
    "analytical_kpi_readiness": _build_schema(
        required_fields=[
            "readiness_record_id",
            "kpi_id",
            "kpi_name",
            "readiness_status",
            "blocking_reason",
            "source_dataset_available",
            "required_fields_available",
            "threshold_config_available",
            "approval_status",
            "assessed_at",
            "calculation_run_id",
        ],
        optional_fields=[
            "unresolved_rules",
            "conditional_reason",
        ],
        boolean_fields=["source_dataset_available", "required_fields_available", "threshold_config_available"],
        unique_constraints=[["readiness_record_id"], ["kpi_id", "calculation_run_id"]],
    ),
}


# ---------------------------------------------------------------------------
# 3. Public API
# ---------------------------------------------------------------------------

def get_analytical_schema(schema_name: str) -> Dict[str, Any]:
    """Return the schema definition for an analytical output dataset."""
    return ANALYTICAL_SCHEMAS.get(schema_name, {})


def list_analytical_schemas() -> List[str]:
    """Return all registered analytical schema names."""
    return sorted(ANALYTICAL_SCHEMAS.keys())


def validate_schema_completeness() -> Dict[str, Any]:
    """Validate that all expected analytical schemas are defined."""
    expected = {
        "analytical_kpi_daily",
        "analytical_kpi_monthly",
        "analytical_kpi_evidence",
        "analytical_kpi_exclusions",
        "analytical_kpi_lineage",
        "analytical_kpi_issues",
        "analytical_kpi_audit",
        "analytical_kpi_run_manifest",
        "analytical_kpi_readiness",
    }
    registered = set(ANALYTICAL_SCHEMAS.keys())
    missing = expected - registered
    extra = registered - expected
    return {
        "expected_count": len(expected),
        "registered_count": len(registered),
        "missing": sorted(missing),
        "extra": sorted(extra),
        "valid": len(missing) == 0,
    }
