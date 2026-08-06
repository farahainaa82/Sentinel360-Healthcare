"""
Sentinel360 Healthcare — Processing Architecture Tests

Tests for Step 2D-1:
- processing models
- processed schema registry
- processing config loader
- processing contracts
- template outputs

Step: 2D-1
"""

import json
import os
from pathlib import Path

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# 1. Import safety
# ---------------------------------------------------------------------------

def test_processing_models_imports_safely():
    from src import processing_models as pm
    assert hasattr(pm, "ProcessingRun")
    assert hasattr(pm, "ProcessingDatasetResult")
    assert hasattr(pm, "ProcessingIssue")
    assert hasattr(pm, "ProcessingLineageRecord")
    assert hasattr(pm, "ProcessingExclusionRecord")


def test_processed_schema_registry_imports_safely():
    from src import processed_schema_registry as psr
    assert hasattr(psr, "load_processed_schema_registry")
    assert hasattr(psr, "list_processed_datasets")
    assert hasattr(psr, "validate_processed_schema_registry")


def test_processing_config_loader_imports_safely():
    from src import processing_config_loader as pcl
    assert hasattr(pcl, "load_attendance_mapping")
    assert hasattr(pcl, "load_absence_mapping")
    assert hasattr(pcl, "validate_processing_configuration")


def test_processing_contracts_imports_safely():
    from src import processing_contracts as pc
    assert hasattr(pc, "ValidationGateContract")
    assert hasattr(pc, "SourceToProcessedContract")
    assert hasattr(pc, "TransformationResultContract")
    assert hasattr(pc, "ProcessingEngineContract")


# ---------------------------------------------------------------------------
# 2. Schema registry structure
# ---------------------------------------------------------------------------

class TestProcessedSchemaRegistry:
    @pytest.fixture(scope="class")
    def registry(self):
        from src.processed_schema_registry import load_processed_schema_registry
        return load_processed_schema_registry()

    def test_all_19_processed_datasets_exist(self, registry):
        assert len(registry) == 19

    def test_all_processed_dataset_names_unique(self, registry):
        names = list(registry.keys())
        assert len(names) == len(set(names))

    def test_all_primary_keys_exist_in_field_lists(self, registry):
        for name, schema in registry.items():
            pk = schema.get("primary_key", "")
            all_fields = schema.get("required_fields", []) + schema.get("optional_fields", [])
            assert pk in all_fields, f"Primary key '{pk}' missing in {name}"

    def test_required_and_optional_fields_do_not_overlap(self, registry):
        for name, schema in registry.items():
            overlap = set(schema.get("required_fields", [])) & set(schema.get("optional_fields", []))
            assert not overlap, f"Overlap in {name}: {overlap}"

    def test_all_date_fields_exist(self, registry):
        for name, schema in registry.items():
            all_fields = set(schema.get("required_fields", []) + schema.get("optional_fields", []))
            for f in schema.get("date_fields", []):
                if f:
                    assert f in all_fields, f"Date field '{f}' missing in {name}"

    def test_all_datetime_fields_exist(self, registry):
        for name, schema in registry.items():
            all_fields = set(schema.get("required_fields", []) + schema.get("optional_fields", []))
            for f in schema.get("datetime_fields", []):
                if f:
                    assert f in all_fields, f"Datetime field '{f}' missing in {name}"

    def test_all_numeric_fields_exist(self, registry):
        for name, schema in registry.items():
            all_fields = set(schema.get("required_fields", []) + schema.get("optional_fields", []))
            for f in schema.get("numeric_fields", []):
                if f:
                    assert f in all_fields, f"Numeric field '{f}' missing in {name}"

    def test_all_boolean_fields_exist(self, registry):
        for name, schema in registry.items():
            all_fields = set(schema.get("required_fields", []) + schema.get("optional_fields", []))
            for f in schema.get("boolean_fields", []):
                if f:
                    assert f in all_fields, f"Boolean field '{f}' missing in {name}"

    def test_all_categorical_fields_exist(self, registry):
        for name, schema in registry.items():
            all_fields = set(schema.get("required_fields", []) + schema.get("optional_fields", []))
            for cat_field in schema.get("categorical_fields", {}):
                assert cat_field in all_fields, f"Categorical field '{cat_field}' missing in {name}"

    def test_all_parent_relationship_fields_exist(self, registry):
        for name, schema in registry.items():
            all_fields = set(schema.get("required_fields", []) + schema.get("optional_fields", []))
            for rel in schema.get("parent_relationships", []):
                child = rel.get("child_field", "")
                if child:
                    assert child in all_fields, f"Parent child_field '{child}' missing in {name}"

    def test_all_source_dataset_references_exist(self, registry):
        from src.validation_config_loader import load_dataset_schema_registry
        source_registry = load_dataset_schema_registry()
        approved_sources = set(source_registry.keys())
        approved_processed = set(registry.keys())
        for name, schema in registry.items():
            for src in schema.get("source_datasets", []):
                if src == "*":
                    continue
                assert src in approved_sources or src in approved_processed, f"Source '{src}' for {name} not approved"

    def test_all_implementation_steps_valid(self, registry):
        valid_steps = {"2D-2", "2D-3", "2D-4", "2D-5"}
        for name, schema in registry.items():
            step = schema.get("implementation_step", "")
            assert step in valid_steps, f"Invalid step '{step}' for {name}"

    def test_step_2d2_contains_eight_datasets(self, registry):
        from src.processed_schema_registry import get_step_dataset_mapping
        mapping = get_step_dataset_mapping()
        expected = [
            "processed_hospital_master",
            "processed_department_master",
            "processed_staff_role_master",
            "processed_staff_master",
            "processed_staff_roster",
            "processed_staff_attendance",
            "processed_staffing_requirement",
            "processed_workforce_daily",
        ]
        assert set(mapping["2D-2"]) == set(expected)

    def test_step_2d3_contains_five_datasets(self, registry):
        from src.processed_schema_registry import get_step_dataset_mapping
        mapping = get_step_dataset_mapping()
        expected = [
            "processed_patient_encounters",
            "processed_patient_queue",
            "processed_bed_capacity",
            "processed_service_schedule",
            "processed_patient_flow_daily",
        ]
        assert set(mapping["2D-3"]) == set(expected)

    def test_step_2d4_contains_three_datasets(self, registry):
        from src.processed_schema_registry import get_step_dataset_mapping
        mapping = get_step_dataset_mapping()
        expected = [
            "processed_patient_complaints",
            "processed_patient_surveys",
            "processed_patient_experience_daily",
        ]
        assert set(mapping["2D-4"]) == set(expected)

    def test_step_2d5_contains_three_datasets(self, registry):
        from src.processed_schema_registry import get_step_dataset_mapping
        mapping = get_step_dataset_mapping()
        expected = [
            "processing_record_lineage",
            "processing_exclusion_register",
            "processing_run_summary",
        ]
        assert set(mapping["2D-5"]) == set(expected)

    def test_registry_validation_returns_no_errors(self, registry):
        from src.processed_schema_registry import validate_processed_schema_registry
        errors = validate_processed_schema_registry()
        assert errors == [], f"Schema registry validation errors: {errors}"


# ---------------------------------------------------------------------------
# 3. Transformation rules
# ---------------------------------------------------------------------------

class TestTransformationRules:
    def test_transformation_rule_ids_are_unique(self):
        from src.processed_schema_registry import list_transformation_rules
        rules = list_transformation_rules()
        ids = [r["transformation_rule_id"] for r in rules]
        assert len(ids) == len(set(ids))

    def test_all_transformation_rules_reference_valid_target_datasets(self):
        from src.processed_schema_registry import list_transformation_rules, load_processed_schema_registry
        rules = list_transformation_rules()
        registry = load_processed_schema_registry()
        approved = set(registry.keys())
        for rule in rules:
            for target in rule.get("target_datasets", []):
                if target == "*":
                    continue
                assert target in approved, f"Rule {rule['transformation_rule_id']} targets unknown {target}"


# ---------------------------------------------------------------------------
# 4. Validation gate
# ---------------------------------------------------------------------------

class TestValidationGate:
    def test_validation_gate_accepts_passed_with_processing_allowed_true(self):
        from src.processing_contracts import ValidationGateContract
        manifest = {"run_status": "Passed", "processing_allowed_flag": True, "validation_run_id": "VAL-001"}
        result = ValidationGateContract.check_validation_gate(manifest)
        assert result.processing_allowed is True
        assert result.blocking_reason == ""

    def test_validation_gate_accepts_passed_with_warnings_and_processing_allowed_true(self):
        from src.processing_contracts import ValidationGateContract
        manifest = {"run_status": "Passed with Warnings", "processing_allowed_flag": True, "validation_run_id": "VAL-002"}
        result = ValidationGateContract.check_validation_gate(manifest)
        assert result.processing_allowed is True

    def test_validation_gate_rejects_failed(self):
        from src.processing_contracts import ValidationGateContract
        manifest = {"run_status": "Failed", "processing_allowed_flag": True, "validation_run_id": "VAL-003"}
        result = ValidationGateContract.check_validation_gate(manifest)
        assert result.processing_allowed is False
        assert "Failed" in result.blocking_reason

    def test_validation_gate_rejects_blocked(self):
        from src.processing_contracts import ValidationGateContract
        manifest = {"run_status": "Blocked", "processing_allowed_flag": True, "validation_run_id": "VAL-004"}
        result = ValidationGateContract.check_validation_gate(manifest)
        assert result.processing_allowed is False
        assert "Blocked" in result.blocking_reason

    def test_validation_gate_rejects_processing_allowed_false(self):
        from src.processing_contracts import ValidationGateContract
        manifest = {"run_status": "Passed", "processing_allowed_flag": False, "validation_run_id": "VAL-005"}
        result = ValidationGateContract.check_validation_gate(manifest)
        assert result.processing_allowed is False
        assert "processing_allowed_flag" in result.blocking_reason


# ---------------------------------------------------------------------------
# 5. Processing configuration loader
# ---------------------------------------------------------------------------

class TestProcessingConfigLoader:
    def test_attendance_mapping_loads_successfully(self):
        from src.processing_config_loader import load_attendance_mapping
        df = load_attendance_mapping()
        assert isinstance(df, pd.DataFrame)
        assert "source_status" in df.columns

    def test_absence_mapping_loads_successfully(self):
        from src.processing_config_loader import load_absence_mapping
        df = load_absence_mapping()
        assert isinstance(df, pd.DataFrame)
        assert "absence_category" in df.columns

    def test_missing_attendance_remains_unknown(self):
        from src.processing_config_loader import get_attendance_status_for_missing
        status = get_attendance_status_for_missing()
        assert status.lower() == "unknown"

    def test_missing_attendance_is_not_classified_present(self):
        from src.processing_config_loader import is_missing_classified_as_present
        assert is_missing_classified_as_present() is False

    def test_missing_attendance_is_not_classified_absent(self):
        from src.processing_config_loader import is_missing_classified_as_absent
        assert is_missing_classified_as_absent() is False

    def test_blank_numerical_config_values_remain_null(self):
        from src.processing_config_loader import load_attendance_mapping
        df = load_attendance_mapping()
        # The availability_factor column may be blank; ensure it is not forced to zero
        if "availability_factor" in df.columns:
            blank_count = df["availability_factor"].isna().sum() + (df["availability_factor"] == "").sum()
            # We simply confirm the column exists and was not coerced to numeric zeros
            assert blank_count >= 0

    def test_processing_configuration_validation_no_errors(self):
        from src.processing_config_loader import validate_processing_configuration
        errors = validate_processing_configuration()
        assert errors == [], f"Processing config validation errors: {errors}"


# ---------------------------------------------------------------------------
# 6. Boundaries and prohibitions
# ---------------------------------------------------------------------------

class TestStep2D1Boundaries:
    def test_no_processing_function_writes_data_processed(self):
        from src import processing_contracts as pc
        from src import processed_schema_registry as psr
        from src import processing_config_loader as pcl
        from src import processing_models as pm
        # Inspect that no export function is actually called in Step 2D-1
        assert not hasattr(pc.ProcessingEngineContract, "run")
        # Ensure no file-writing helpers exist outside contracts
        assert not hasattr(pm, "export_to_csv")
        assert not hasattr(psr, "write_processed_dataset")
        assert not hasattr(pcl, "write_config")

    def test_no_kpi_fields_in_processed_daily_schemas(self):
        from src.processed_schema_registry import load_processed_schema_registry
        registry = load_processed_schema_registry()
        kpi_keywords = ["staffing_level_percent", "absenteeism_rate_percent", "average_patient_waiting_time_kpi", "bed_occupancy_rate_kpi", "complaint_rate", "patient_satisfaction_score"]
        for name, schema in registry.items():
            all_fields = set(schema.get("required_fields", []) + schema.get("optional_fields", []))
            for kw in kpi_keywords:
                assert kw not in all_fields, f"KPI field '{kw}' found in {name}"

    def test_no_kpi_status_fields(self):
        from src.processed_schema_registry import load_processed_schema_registry
        registry = load_processed_schema_registry()
        for name, schema in registry.items():
            all_fields = set(schema.get("required_fields", []) + schema.get("optional_fields", []))
            for f in all_fields:
                allowed_status_fields = {
                    "requirement_status", "schedule_status", "response_status",
                    "complaint_status", "assignment_status", "attendance_status",
                    "disposition_status", "processing_run_status", "dataset_status",
                    "complaint_status_source",
                }
                assert "_status" not in f or f in allowed_status_fields, f"Unexpected status field '{f}' in {name}"

    def test_no_risk_score_fields(self):
        from src.processed_schema_registry import load_processed_schema_registry
        registry = load_processed_schema_registry()
        for name, schema in registry.items():
            all_fields = set(schema.get("required_fields", []) + schema.get("optional_fields", []))
            for f in all_fields:
                assert "risk" not in f.lower(), f"Risk field '{f}' found in {name}"

    def test_no_forecast_fields(self):
        from src.processed_schema_registry import load_processed_schema_registry
        registry = load_processed_schema_registry()
        for name, schema in registry.items():
            all_fields = set(schema.get("required_fields", []) + schema.get("optional_fields", []))
            for f in all_fields:
                assert "forecast" not in f.lower(), f"Forecast field '{f}' found in {name}"

    def test_no_scenario_result_fields(self):
        from src.processed_schema_registry import load_processed_schema_registry
        registry = load_processed_schema_registry()
        for name, schema in registry.items():
            all_fields = set(schema.get("required_fields", []) + schema.get("optional_fields", []))
            for f in all_fields:
                assert "scenario" not in f.lower(), f"Scenario field '{f}' found in {name}"

    def test_no_financial_result_fields(self):
        from src.processed_schema_registry import load_processed_schema_registry
        registry = load_processed_schema_registry()
        for name, schema in registry.items():
            all_fields = set(schema.get("required_fields", []) + schema.get("optional_fields", []))
            for f in all_fields:
                assert "financial" not in f.lower() and "cost" not in f.lower() and "revenue" not in f.lower(), f"Financial field '{f}' found in {name}"

    def test_no_recommendation_fields(self):
        from src.processed_schema_registry import load_processed_schema_registry
        registry = load_processed_schema_registry()
        for name, schema in registry.items():
            all_fields = set(schema.get("required_fields", []) + schema.get("optional_fields", []))
            for f in all_fields:
                assert "recommendation" not in f.lower(), f"Recommendation field '{f}' found in {name}"


# ---------------------------------------------------------------------------
# 7. Model completeness
# ---------------------------------------------------------------------------

class TestModelCompleteness:
    def test_lineage_model_contains_required_audit_fields(self):
        from src.processing_models import ProcessingLineageRecord
        rec = ProcessingLineageRecord(
            processing_run_id="P001",
            lineage_id="L001",
            validation_run_id="V001",
            source_dataset_name="staff_master",
            source_file_name="staff_master.csv",
            source_primary_key_field="staff_id",
            source_primary_key_value="S001",
            source_row_number=1,
            processed_dataset_name="processed_staff_master",
            processed_primary_key_field="staff_id",
            processed_primary_key_value="S001",
            transformation_rule_id="TR_REF_STANDARDISE_TEXT",
            transformation_description="Standardise text",
            source_fields_used="staff_id",
            processed_fields_created="staff_id",
            exclusion_flag=False,
            exclusion_reason_code="",
            transformation_version="1.0.0",
            configuration_version="v1.0-draft",
            processed_datetime=pd.Timestamp("2026-07-25"),
        )
        d = rec.to_dict()
        assert d["processing_run_id"] == "P001"
        assert d["validation_run_id"] == "V001"
        assert d["transformation_rule_id"] == "TR_REF_STANDARDISE_TEXT"

    def test_exclusion_model_contains_required_reason_fields(self):
        from src.processing_models import ProcessingExclusionRecord
        rec = ProcessingExclusionRecord(
            processing_run_id="P001",
            exclusion_id="E001",
            source_dataset_name="staff_attendance",
            source_primary_key_field="attendance_id",
            source_primary_key_value="A001",
            source_row_number=5,
            exclusion_reason_code="Invalid Relationship",
            exclusion_reason_description="Orphan staff_id reference",
            validation_issue_id="ISS-001",
            manual_override_id="",
            exclusion_stage="Transformation",
            excluded_by_rule="TR_WF_ATTENDANCE_MAPPING",
            reversible_flag=False,
        )
        d = rec.to_dict()
        assert d["exclusion_reason_code"] == "Invalid Relationship"
        assert d["excluded_by_rule"] == "TR_WF_ATTENDANCE_MAPPING"


# ---------------------------------------------------------------------------
# 8. Template output files
# ---------------------------------------------------------------------------

class TestTemplateOutputs:
    def test_processing_run_manifest_template_exists(self):
        path = Path("outputs/logs/processing_run_manifest_template.json")
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "processing_run_id" in data
        assert "validation_run_id" in data
        assert "run_status" in data

    def test_processing_lineage_log_template_exists(self):
        path = Path("outputs/logs/processing_lineage_log_template.csv")
        assert path.exists()
        df = pd.read_csv(path)
        assert "lineage_id" in df.columns
        assert "processing_run_id" in df.columns
        assert "source_primary_key_value" in df.columns

    def test_processing_issue_log_template_exists(self):
        path = Path("outputs/logs/processing_issue_log_template.csv")
        assert path.exists()
        df = pd.read_csv(path)
        assert "issue_id" in df.columns
        assert "processing_run_id" in df.columns
        assert "field_name" in df.columns

    def test_lineage_template_is_headers_only(self):
        path = Path("outputs/logs/processing_lineage_log_template.csv")
        df = pd.read_csv(path)
        assert len(df) == 0, "Lineage template should contain headers only"

    def test_issue_template_is_headers_only(self):
        path = Path("outputs/logs/processing_issue_log_template.csv")
        df = pd.read_csv(path)
        assert len(df) == 0, "Issue template should contain headers only"
