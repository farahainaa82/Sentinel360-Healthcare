"""Dataset-type detection engine with filename and column-signature matching."""

from typing import Tuple, Optional


# Filename patterns mapping to dataset types
FILENAME_PATTERNS = {
    "Staff Roster": ["staff_roster", "roster", "staff_roster.csv"],
    "Staff Attendance": ["staff_attendance", "attendance", "staff_attendance.csv"],
    "Patient Encounters": ["patient_encounters", "encounters", "patient_encounters.csv"],
    "Bed Occupancy": ["bed_capacity", "bed_capacity_records", "bed_occupancy", "bed_occupancy_records"],
    "Patient Queue": ["patient_queue", "patient_queue_records", "queue_records"],
    "Patient Complaints": ["patient_complaints", "complaint_records", "complaints"],
    "Patient Survey": ["patient_surveys", "patient_survey", "surveys"],
}

# Column signatures for synthetic demo files
DATASET_SIGNATURES = {
    "Staff Roster": {
        "required": ["roster_id", "staff_id", "hospital_id", "department_id", "role_id", "roster_date", "shift_code"],
        "preferred": ["planned_start_datetime", "planned_end_datetime", "planned_hours", "status"],
    },
    "Staff Attendance": {
        "required": ["attendance_id", "staff_id", "hospital_id", "department_id", "role_id", "roster_id", "attendance_date", "shift_code", "status"],
        "preferred": ["actual_start_datetime", "actual_end_datetime", "actual_hours"],
    },
    "Patient Encounters": {
        "required": ["encounter_id", "hospital_id", "department_id", "patient_id", "encounter_date", "encounter_type", "arrival_datetime", "status"],
        "preferred": ["service_start_datetime", "service_end_datetime", "triage_category"],
    },
    "Bed Occupancy": {
        "required": ["record_id", "hospital_id", "department_id", "record_date", "bed_licensed", "bed_staffed", "bed_operational", "bed_occupied", "occupancy_rate", "exception_flag"],
        "preferred": ["bed_unavailable", "bed_reserved", "exception_reason"],
    },
    "Patient Queue": {
        "required": ["queue_id", "hospital_id", "department_id", "queue_date", "queue_type", "period_start", "period_end"],
        "preferred": ["arrivals_count", "served_count", "waiting_count", "avg_wait_minutes"],
    },
    "Patient Complaints": {
        "required": ["complaint_id", "hospital_id", "department_id", "complaint_received_date", "complaint_category", "severity", "description", "status"],
        "preferred": ["resolution_date", "outcome_category", "duplicate_flag"],
    },
    "Patient Survey": {
        "required": ["survey_id", "hospital_id", "department_id", "survey_date", "score_value"],
        "preferred": ["survey_type", "scale_id", "encounter_id"],
    },
}


def _filename_match(filename: str) -> Optional[str]:
    """Match filename against known patterns. Returns dataset_type or None."""
    lowered = filename.lower()
    for dataset_type, patterns in FILENAME_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in lowered:
                return dataset_type
    return None


def _signature_match(columns: list) -> Tuple[Optional[str], str, str]:
    """Match column list against dataset signatures. Returns (dataset_type, confidence, reason)."""
    cols_lower = [c.lower() for c in columns]
    best_match = None
    best_score = 0
    best_reason = ""

    for dataset_type, sig in DATASET_SIGNATURES.items():
        required = sig.get("required", [])
        preferred = sig.get("preferred", [])
        req_hits = sum(1 for r in required if r.lower() in cols_lower)
        pref_hits = sum(1 for p in preferred if p.lower() in cols_lower)
        req_total = len(required)
        pref_total = len(preferred)

        # Require at least 50% of required columns
        if req_total > 0 and req_hits < req_total * 0.5:
            continue

        score = (req_hits / max(req_total, 1)) * 2.0 + (pref_hits / max(pref_total, 1)) * 1.0

        if score > best_score:
            best_score = score
            best_match = dataset_type
            best_reason = f"matched {req_hits}/{req_total} required + {pref_hits}/{pref_total} preferred columns"

    if best_match:
        if best_score >= 2.0:
            confidence = "High"
        elif best_score >= 1.0:
            confidence = "Moderate"
        else:
            confidence = "Low"
        return best_match, confidence, best_reason

    return None, "Not Detected", "no signature match"


def detect_dataset_type(filename: str, columns: list) -> Tuple[str, str, str]:
    """Detect dataset type from filename and column signatures.

    Returns:
        (dataset_type, confidence, reason)
    """
    # Filename match takes precedence for known demo files
    filename_match = _filename_match(filename)
    if filename_match:
        # Verify with column signature if available
        sig_match, sig_conf, sig_reason = _signature_match(columns)
        if sig_match == filename_match:
            return filename_match, "High", f"filename + column signature: {sig_reason}"
        # If filename matches but columns don't strongly contradict, trust filename
        if sig_match is None or sig_conf in ("Low", "Not Detected"):
            return filename_match, "High", "filename pattern match"
        # If column signature strongly matches a different type, prefer columns
        if sig_conf == "High" and sig_match != filename_match:
            return sig_match, sig_conf, f"column signature override: {sig_reason}"
        return filename_match, "High", "filename pattern match"

    # Fallback to column signature only
    sig_match, sig_conf, sig_reason = _signature_match(columns)
    if sig_match:
        return sig_match, sig_conf, sig_reason

    return "Unknown", "Not Detected", "no filename or column signature match"
