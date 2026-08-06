"""Risk prioritisation domain models and enums for Step 2B-3."""

from enum import Enum


class ConfidenceLevel(str, Enum):
    HIGH = "High"
    MODERATE = "Moderate"
    LOW = "Low"
    INSUFFICIENT_EVIDENCE = "Insufficient Evidence"


class PriorityTier(str, Enum):
    NO_CURRENT_RISK = "No Current Risk"
    MONITOR = "Monitor"
    ATTENTION_REQUIRED = "Attention Required"
    HIGH_PRIORITY = "High Priority"
    CRITICAL_PRIORITY = "Critical Priority"
    NOT_ASSESSABLE = "Not Assessable"


class UrgencyLevel(str, Enum):
    ROUTINE_MONITORING = "Routine Monitoring"
    REVIEW_SOON = "Review Soon"
    PROMPT_REVIEW = "Prompt Review"
    IMMEDIATE_REVIEW = "Immediate Review"
    NOT_ASSESSABLE = "Not Assessable"


class DataAvailabilityStatus(str, Enum):
    COMPLETE = "Complete"
    SUFFICIENT = "Sufficient"
    LIMITED = "Limited"
    INSUFFICIENT = "Insufficient"


class IssueCategory(str, Enum):
    MISSING_STEP_2B2_RECORD = "Missing Step 2B-2 Record"
    MISSING_KPI_RISK_WEIGHT = "Missing KPI Risk Weight"
    INVALID_RISK_WEIGHT = "Invalid Risk Weight"
    MISSING_SEVERITY_MAPPING = "Missing Severity Mapping"
    MISSING_CONFIDENCE_MAPPING = "Missing Confidence Mapping"
    DUPLICATE_KPI_RISK_RECORD = "Duplicate KPI Risk Record"
    DUPLICATE_DEPARTMENT_RISK_RECORD = "Duplicate Department Risk Record"
    INVALID_SCORE_RANGE = "Invalid Score Range"
    MISSING_DOMINANT_DRIVER = "Missing Dominant Driver"
    BROKEN_EVIDENCE_LINK = "Broken Evidence Link"
    BROKEN_LINEAGE_LINK = "Broken Lineage Link"
    INCONSISTENT_PROVISIONAL_FLAG = "Inconsistent Provisional Flag"
    INSUFFICIENT_ASSESSABLE_KPIS = "Insufficient Assessable KPIs"
    RANKING_TIE_BREAK_FAILURE = "Ranking Tie-Break Failure"
    MISSING_DEPARTMENT_IDENTIFIER = "Missing Department Identifier"
    SOURCE_COUNT_MISMATCH = "Source Count Mismatch"


class IssueSeverity(str, Enum):
    WARNING = "Warning"
    BLOCKING = "Blocking"
