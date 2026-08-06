"""
Demo Generation Configuration — Sentinel360 Healthcare

This module defines structured Python configuration for the synthetic
operational-data generation mechanics. It is NOT a replacement for business-rule
CSV files in config/.

Categories of configuration held here:
    A. Generation mechanics — how records are created, dated, linked, and noised.
    B. Business configuration references — paths to official config/ CSVs.
    C. Future analytical rules — placeholders for engine-level logic not yet built.

All values are prototype demonstration settings. The default seed (360) is a
reproducibility setting, not a business assumption.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# A. Generation Mechanics
# ---------------------------------------------------------------------------

DEFAULT_SEED: int = 360
"""Deterministic random seed for reproducible synthetic datasets."""

DEFAULT_START_DATE: date = date(2026, 1, 1)
DEFAULT_END_DATE: date = date(2026, 12, 31)
"""Default 12-month demonstration period."""

# ---------------------------------------------------------------------------
# Shift Definitions
# ---------------------------------------------------------------------------

SHIFT_DEFINITIONS: List[Dict[str, object]] = [
    {
        "shift_code": "MORNING",
        "shift_name": "Morning Shift",
        "planned_start_time": time(7, 0),
        "planned_end_time": time(15, 0),
        "planned_hours": 8.0,
        "is_overnight": False,
    },
    {
        "shift_code": "EVENING",
        "shift_name": "Evening Shift",
        "planned_start_time": time(15, 0),
        "planned_end_time": time(23, 0),
        "planned_hours": 8.0,
        "is_overnight": False,
    },
    {
        "shift_code": "NIGHT",
        "shift_name": "Night Shift",
        "planned_start_time": time(23, 0),
        "planned_end_time": time(7, 0),
        "planned_hours": 8.0,
        "is_overnight": True,
    },
]

# ---------------------------------------------------------------------------
# Fictional Hospital
# ---------------------------------------------------------------------------

HOSPITAL_DEFINITION: Dict[str, object] = {
    "hospital_id": "HOSP-001",
    "hospital_name": "Sentinel Demo Hospital",
    "hospital_short_name": "Sentinel Demo",
    "hospital_type": "General Hospital",
    "region": "Central Region",
    "country": "Demo Country",
    "bed_licensed_total": 450,
    "status": "Active",
    "effective_from": date(2020, 1, 1),
    "effective_to": date(2099, 12, 31),
    "source_system": "SENTINEL_DEMO_MASTER",
    "record_version": 1,
}

# ---------------------------------------------------------------------------
# Department Catalogue
# ---------------------------------------------------------------------------

DEPARTMENT_DEFINITIONS: List[Dict[str, object]] = [
    {
        "department_id": "DEPT-ED",
        "department_name": "Emergency Department",
        "department_type": "Clinical",
        "department_subtype": "Emergency",
        "is_bed_based": False,
        "has_queue": True,
        "has_staffing": True,
        "has_capacity": False,
        "bed_licensed": 0,
    },
    {
        "department_id": "DEPT-OPC",
        "department_name": "Outpatient Clinic",
        "department_type": "Clinical",
        "department_subtype": "Outpatient",
        "is_bed_based": False,
        "has_queue": True,
        "has_staffing": True,
        "has_capacity": False,
        "bed_licensed": 0,
    },
    {
        "department_id": "DEPT-MED",
        "department_name": "Medical Ward",
        "department_type": "Clinical",
        "department_subtype": "Inpatient",
        "is_bed_based": True,
        "has_queue": False,
        "has_staffing": True,
        "has_capacity": True,
        "bed_licensed": 120,
    },
    {
        "department_id": "DEPT-SURG",
        "department_name": "Surgical Ward",
        "department_type": "Clinical",
        "department_subtype": "Inpatient",
        "is_bed_based": True,
        "has_queue": False,
        "has_staffing": True,
        "has_capacity": True,
        "bed_licensed": 100,
    },
    {
        "department_id": "DEPT-ICU",
        "department_name": "Intensive Care Unit",
        "department_type": "Clinical",
        "department_subtype": "Critical Care",
        "is_bed_based": True,
        "has_queue": False,
        "has_staffing": True,
        "has_capacity": True,
        "bed_licensed": 24,
    },
    {
        "department_id": "DEPT-DIAG",
        "department_name": "Diagnostic Services",
        "department_type": "Clinical",
        "department_subtype": "Diagnostic",
        "is_bed_based": False,
        "has_queue": True,
        "has_staffing": True,
        "has_capacity": False,
        "bed_licensed": 0,
    },
    {
        "department_id": "DEPT-PEX",
        "department_name": "Patient Experience",
        "department_type": "Administrative",
        "department_subtype": "Patient Experience",
        "is_bed_based": False,
        "has_queue": False,
        "has_staffing": True,
        "has_capacity": False,
        "bed_licensed": 0,
    },
    {
        "department_id": "DEPT-ADM",
        "department_name": "Administration",
        "department_type": "Administrative",
        "department_subtype": "Administration",
        "is_bed_based": False,
        "has_queue": False,
        "has_staffing": True,
        "has_capacity": False,
        "bed_licensed": 0,
    },
]

# ---------------------------------------------------------------------------
# Staff Role Catalogue
# ---------------------------------------------------------------------------

STAFF_ROLE_DEFINITIONS: List[Dict[str, object]] = [
    {
        "role_id": "ROLE-ED-PHY",
        "role_name": "Emergency Physician",
        "staff_category": "Doctor",
        "is_clinical": True,
        "effective_from": date(2020, 1, 1),
        "effective_to": date(2099, 12, 31),
    },
    {
        "role_id": "ROLE-MO",
        "role_name": "Medical Officer",
        "staff_category": "Doctor",
        "is_clinical": True,
        "effective_from": date(2020, 1, 1),
        "effective_to": date(2099, 12, 31),
    },
    {
        "role_id": "ROLE-RN",
        "role_name": "Registered Nurse",
        "staff_category": "Nurse",
        "is_clinical": True,
        "effective_from": date(2020, 1, 1),
        "effective_to": date(2099, 12, 31),
    },
    {
        "role_id": "ROLE-AMO",
        "role_name": "Assistant Medical Officer",
        "staff_category": "Doctor",
        "is_clinical": True,
        "effective_from": date(2020, 1, 1),
        "effective_to": date(2099, 12, 31),
    },
    {
        "role_id": "ROLE-PHARM",
        "role_name": "Pharmacist",
        "staff_category": "Allied Health",
        "is_clinical": True,
        "effective_from": date(2020, 1, 1),
        "effective_to": date(2099, 12, 31),
    },
    {
        "role_id": "ROLE-RAD",
        "role_name": "Radiographer",
        "staff_category": "Allied Health",
        "is_clinical": True,
        "effective_from": date(2020, 1, 1),
        "effective_to": date(2099, 12, 31),
    },
    {
        "role_id": "ROLE-HCA",
        "role_name": "Healthcare Assistant",
        "staff_category": "Support",
        "is_clinical": True,
        "effective_from": date(2020, 1, 1),
        "effective_to": date(2099, 12, 31),
    },
    {
        "role_id": "ROLE-REG",
        "role_name": "Registration Clerk",
        "staff_category": "Administrative",
        "is_clinical": False,
        "effective_from": date(2020, 1, 1),
        "effective_to": date(2099, 12, 31),
    },
    {
        "role_id": "ROLE-PEO",
        "role_name": "Patient Experience Officer",
        "staff_category": "Administrative",
        "is_clinical": False,
        "effective_from": date(2020, 1, 1),
        "effective_to": date(2099, 12, 31),
    },
]

# ---------------------------------------------------------------------------
# Storyline Phase Definitions
# ---------------------------------------------------------------------------

STORYLINE_PHASES: List[Dict[str, object]] = [
    {
        "phase_id": "P1",
        "phase_name": "Stable period",
        "phase_order": 1,
        "start_month": 1,
        "end_month": 2,
        "description": "Normal operations with low absenteeism and standard demand.",
        "absence_probability_factor": 1.0,
        "patient_volume_factor": 1.0,
        "wait_time_factor": 1.0,
        "complaint_probability_factor": 1.0,
        "satisfaction_mean_factor": 1.0,
        "bed_demand_factor": 1.0,
    },
    {
        "phase_id": "P2",
        "phase_name": "Early pressure period",
        "phase_order": 2,
        "start_month": 3,
        "end_month": 3,
        "description": "Slight rise in absence and minor demand increase.",
        "absence_probability_factor": 1.3,
        "patient_volume_factor": 1.1,
        "wait_time_factor": 1.15,
        "complaint_probability_factor": 1.2,
        "satisfaction_mean_factor": 0.98,
        "bed_demand_factor": 1.05,
    },
    {
        "phase_id": "P3",
        "phase_name": "Deterioration period",
        "phase_order": 3,
        "start_month": 4,
        "end_month": 5,
        "description": "Flu spike and multiple absences; service pressure builds.",
        "absence_probability_factor": 1.8,
        "patient_volume_factor": 1.25,
        "wait_time_factor": 1.4,
        "complaint_probability_factor": 1.6,
        "satisfaction_mean_factor": 0.92,
        "bed_demand_factor": 1.15,
    },
    {
        "phase_id": "P4",
        "phase_name": "Critical pressure period",
        "phase_order": 4,
        "start_month": 6,
        "end_month": 7,
        "description": "Peak absenteeism, long waits, high complaints, low satisfaction.",
        "absence_probability_factor": 2.2,
        "patient_volume_factor": 1.3,
        "wait_time_factor": 1.7,
        "complaint_probability_factor": 2.2,
        "satisfaction_mean_factor": 0.85,
        "bed_demand_factor": 1.25,
    },
    {
        "phase_id": "P5",
        "phase_name": "Intervention or recovery period",
        "phase_order": 5,
        "start_month": 8,
        "end_month": 12,
        "description": "Temporary staff, mitigation, gradual recovery.",
        "absence_probability_factor": 1.4,
        "patient_volume_factor": 1.15,
        "wait_time_factor": 1.25,
        "complaint_probability_factor": 1.4,
        "satisfaction_mean_factor": 0.94,
        "bed_demand_factor": 1.1,
    },
]

# ---------------------------------------------------------------------------
# Approximate Synthetic Record Volumes
# ---------------------------------------------------------------------------

VOLUME_CONFIG: Dict[str, int] = {
    "hospitals": 1,
    "departments": 8,
    "staff_roles": 9,
    "staff": 180,
    "staff_roster_days": 365,
    "patient_encounters_per_day": 220,
    "queue_records_per_day": 220,
    "bed_capacity_records_per_day": 244,  # bed-based depts only
    "complaints_per_day": 3,
    "surveys_per_day": 15,
    "service_schedule_records_per_week": 56,
    "staffing_requirement_records_per_day": 72,  # depts x shifts x roles
}

# ---------------------------------------------------------------------------
# Attendance Status Probabilities (Baseline, applied per storyline phase)
# ---------------------------------------------------------------------------

ATTENDANCE_STATUS_BASELINE: Dict[str, float] = {
    "Present": 0.88,
    "Absent": 0.04,
    "Late": 0.03,
    "Partial": 0.02,
    "Leave": 0.02,
    "Training": 0.01,
    "Reassigned": 0.00,
    "Not Scheduled": 0.00,
}

# ---------------------------------------------------------------------------
# Survey Scale Configuration
# ---------------------------------------------------------------------------

SURVEY_SCALE_CONFIG: List[Dict[str, object]] = [
    {
        "scale_id": "SCALE-5PT",
        "scale_name": "5-Point Likert",
        "min_score": 1,
        "max_score": 5,
        "neutral_point": 3,
    },
    {
        "scale_id": "SCALE-10PT",
        "scale_name": "10-Point Scale",
        "min_score": 1,
        "max_score": 10,
        "neutral_point": 5,
    },
]

# ---------------------------------------------------------------------------
# Defect Injection Switches
# ---------------------------------------------------------------------------

DEFECT_SWITCHES: Dict[str, bool] = {
    "missing_required_values": False,
    "duplicate_primary_keys": False,
    "unknown_hospital_reference": False,
    "unknown_department_reference": False,
    "invalid_staff_role_reference": False,
    "attendance_without_roster": False,
    "negative_values": False,
    "invalid_date_order": False,
    "occupied_above_operational_no_reason": False,
    "invalid_survey_scale": False,
    "invalid_complaint_status": False,
    "stale_source_data": False,
    "missing_configuration_reference": False,
}

# ---------------------------------------------------------------------------
# B. Business Configuration References
# ---------------------------------------------------------------------------

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
CONFIG_DIR: Path = PROJECT_ROOT / "config"
OUTPUT_DIR: Path = PROJECT_ROOT / "outputs"

BUSINESS_CONFIG_FILES: Dict[str, Path] = {
    "kpi_definition_config": CONFIG_DIR / "kpi_definition_config.csv",
    "kpi_threshold_config": CONFIG_DIR / "kpi_threshold_config.csv",
    "attendance_status_mapping": CONFIG_DIR / "attendance_status_mapping.csv",
    "absence_category_mapping": CONFIG_DIR / "absence_category_mapping.csv",
    "watch_rule_config": CONFIG_DIR / "watch_rule_config.csv",
    "trend_rule_config": CONFIG_DIR / "trend_rule_config.csv",
    "anomaly_detection_config": CONFIG_DIR / "anomaly_detection_config.csv",
    "data_confidence_config": CONFIG_DIR / "data_confidence_config.csv",
    "forecast_config": CONFIG_DIR / "forecast_config.csv",
    "intervention_catalogue": CONFIG_DIR / "intervention_catalogue.csv",
    "scenario_assumption_config": CONFIG_DIR / "scenario_assumption_config.csv",
    "financial_assumption_config": CONFIG_DIR / "financial_assumption_config.csv",
    "recommendation_rule_config": CONFIG_DIR / "recommendation_rule_config.csv",
    "outcome_review_config": CONFIG_DIR / "outcome_review_config.csv",
    "role_approval_config": CONFIG_DIR / "role_approval_config.csv",
}

# ---------------------------------------------------------------------------
# C. Future Analytical Rules (placeholders)
# ---------------------------------------------------------------------------

# These placeholders indicate where future engines will load rules from
# official business configuration. No KPI thresholds or analytical formulas
# are embedded here.

FUTURE_ENGINE_RULES: Dict[str, str] = {
    "kpi_engine": "Loaded from config/kpi_definition_config.csv and config/kpi_threshold_config.csv",
    "status_engine": "Loaded from config/kpi_threshold_config.csv and config/watch_rule_config.csv",
    "forecast_engine": "Loaded from config/forecast_config.csv",
    "anomaly_engine": "Loaded from config/anomaly_detection_config.csv",
    "recommendation_engine": "Loaded from config/recommendation_rule_config.csv and config/intervention_catalogue.csv",
    "financial_engine": "Loaded from config/financial_assumption_config.csv",
}

# ---------------------------------------------------------------------------
# Convenience Dataclass
# ---------------------------------------------------------------------------

@dataclass
class GeneratorConfig:
    """Runtime configuration bundle for SyntheticHospitalDataGenerator."""

    seed: int = DEFAULT_SEED
    start_date: date = DEFAULT_START_DATE
    end_date: date = DEFAULT_END_DATE
    hospital: Dict[str, object] = field(default_factory=lambda: HOSPITAL_DEFINITION.copy())
    departments: List[Dict[str, object]] = field(default_factory=lambda: [d.copy() for d in DEPARTMENT_DEFINITIONS])
    staff_roles: List[Dict[str, object]] = field(default_factory=lambda: [r.copy() for r in STAFF_ROLE_DEFINITIONS])
    shifts: List[Dict[str, object]] = field(default_factory=lambda: [s.copy() for s in SHIFT_DEFINITIONS])
    storyline_phases: List[Dict[str, object]] = field(default_factory=lambda: [p.copy() for p in STORYLINE_PHASES])
    volumes: Dict[str, int] = field(default_factory=lambda: VOLUME_CONFIG.copy())
    attendance_baseline: Dict[str, float] = field(default_factory=lambda: ATTENDANCE_STATUS_BASELINE.copy())
    survey_scales: List[Dict[str, object]] = field(default_factory=lambda: [s.copy() for s in SURVEY_SCALE_CONFIG])
    defects: Dict[str, bool] = field(default_factory=lambda: DEFECT_SWITCHES.copy())
    output_dir: Path = OUTPUT_DIR

    @property
    def date_range_days(self) -> int:
        """Return inclusive number of days in the configured period."""
        return (self.end_date - self.start_date).days + 1

    def get_phase_for_date(self, target_date: date) -> Dict[str, object]:
        """Return the storyline phase active for a given date."""
        month = target_date.month
        for phase in self.storyline_phases:
            if phase["start_month"] <= month <= phase["end_month"]:
                return phase
        # Default to first phase if no match
        return self.storyline_phases[0]


def get_default_config() -> GeneratorConfig:
    """Return a fresh default GeneratorConfig instance."""
    return GeneratorConfig()
