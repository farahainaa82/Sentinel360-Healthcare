"""Relationship Analysis Models — enums and constants for Step 2B-4."""

from enum import Enum


class RelationshipDirection(str, Enum):
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    MIXED = "Mixed"
    NONE_DETECTED = "None Detected"
    INSUFFICIENT_EVIDENCE = "Insufficient Evidence"


class RelationshipStrength(str, Enum):
    NONE = "No Relationship"
    WEAK = "Weak"
    MODERATE = "Moderate"
    STRONG = "Strong"
    VERY_STRONG = "Very Strong"
    INSUFFICIENT_EVIDENCE = "Insufficient Evidence"


class TemporalInterpretation(str, Enum):
    NO_TEMPORAL_PATTERN = "No Temporal Pattern"
    SAME_PERIOD_ASSOCIATION = "Same-Period Association"
    SOURCE_FREQUENTLY_PRECEDES_TARGET = "Source Frequently Precedes Target"
    TARGET_FREQUENTLY_PRECEDES_SOURCE = "Target Frequently Precedes Source"
    BIDIRECTIONAL_OR_MIXED = "Bidirectional or Mixed"
    INSUFFICIENT_EVIDENCE = "Insufficient Evidence"


class StabilityClassification(str, Enum):
    STABLE_ACROSS_DEPARTMENTS = "Stable Across Departments"
    MODERATELY_STABLE = "Moderately Stable"
    DEPARTMENT_SPECIFIC = "Department-Specific"
    UNSTABLE = "Unstable"
    INSUFFICIENT_EVIDENCE = "Insufficient Evidence"


class TemporalStability(str, Enum):
    STABLE_OVER_TIME = "Stable Over Time"
    VARIES_BY_PERIOD = "Varies by Period"
    EMERGING_RELATIONSHIP = "Emerging Relationship"
    WEAKENING_RELATIONSHIP = "Weakening Relationship"
    UNSTABLE = "Unstable"
    INSUFFICIENT_EVIDENCE = "Insufficient Evidence"


class ContributingFactorClassification(str, Enum):
    NO_SUPPORTED_RELATIONSHIP = "No Supported Relationship"
    WEAK_ASSOCIATION = "Weak Association"
    SUPPORTED_ASSOCIATION = "Supported Association"
    PLAUSIBLE_CONTRIBUTING_FACTOR = "Plausible Contributing Factor"
    STRONG_CONTRIBUTING_FACTOR_HYPOTHESIS = "Strong Contributing-Factor Hypothesis"
    INSUFFICIENT_EVIDENCE = "Insufficient Evidence"


class ContradictionSeverity(str, Enum):
    NONE = "No Contradiction"
    MINOR = "Minor"
    MATERIAL = "Material"
    MAJOR = "Major"


class ConfidenceLevel(str, Enum):
    HIGH = "High"
    MODERATE = "Moderate"
    LOW = "Low"
    INSUFFICIENT_EVIDENCE = "Insufficient Evidence"


class MaterialityLevel(str, Enum):
    NONE = "None"
    MINOR = "Minor"
    MATERIAL = "Material"
    DOMINANT = "Dominant"


class DataSufficiency(str, Enum):
    SUFFICIENT = "Sufficient"
    LIMITED = "Limited"
    INSUFFICIENT = "Insufficient"
    NOT_ASSESSABLE = "Not Assessable"


class HighRiskSubset(str, Enum):
    GENERAL = "General"
    STRONGER_DURING_STRESS = "Stronger During Operational Stress"
    ONLY_VISIBLE_DURING_SEVERE = "Only Visible During Severe Periods"
    ABSENT_DURING_SEVERE = "Absent During Severe Periods"
    INCONSISTENT = "Inconsistent"


# KPI adversity direction mapping: higher adversity score = worse condition
KPI_ADVERSITY_DIRECTION = {
    "kpi_001": "higher_is_better",   # Staffing Level
    "kpi_002": "lower_is_better",    # Staff Absenteeism Rate
    "kpi_003": "dual_sided",         # Bed Occupancy Rate
    "kpi_004": "lower_is_better",    # Average Patient Waiting Time
    "kpi_005": "lower_is_better",    # Patient Complaint Rate
    "kpi_006": "higher_is_better",   # Patient Satisfaction Score
}

KPI_NAMES = {
    "kpi_001": "Staffing Level",
    "kpi_002": "Staff Absenteeism Rate",
    "kpi_003": "Bed Occupancy Rate",
    "kpi_004": "Average Patient Waiting Time",
    "kpi_005": "Patient Complaint Rate",
    "kpi_006": "Patient Satisfaction Score",
}

ALL_KPI_IDS = ["kpi_001", "kpi_002", "kpi_003", "kpi_004", "kpi_005", "kpi_006"]

# 15 unique undirected pairs
UNIQUE_PAIRS = [
    ("kpi_001", "kpi_002"), ("kpi_001", "kpi_003"), ("kpi_001", "kpi_004"),
    ("kpi_001", "kpi_005"), ("kpi_001", "kpi_006"), ("kpi_002", "kpi_003"),
    ("kpi_002", "kpi_004"), ("kpi_002", "kpi_005"), ("kpi_002", "kpi_006"),
    ("kpi_003", "kpi_004"), ("kpi_003", "kpi_005"), ("kpi_003", "kpi_006"),
    ("kpi_004", "kpi_005"), ("kpi_004", "kpi_006"), ("kpi_005", "kpi_006"),
]
