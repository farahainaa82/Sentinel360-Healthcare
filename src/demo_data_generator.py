"""
Synthetic Hospital Data Generator — Sentinel360 Healthcare

Generates reproducible, record-level synthetic operational source data for
the Sentinel360 Healthcare prototype. This module does NOT calculate KPI
values, statuses, forecasts, recommendations, or any analytical outputs.

All analytical results must be produced by separate future engines.

Usage:
    from demo_data_generator import SyntheticHospitalDataGenerator
    gen = SyntheticHospitalDataGenerator(seed=360)
    data = gen.generate_all()
"""

from __future__ import annotations

import warnings
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from demo_generation_config import GeneratorConfig, get_default_config


# ---------------------------------------------------------------------------
# Schema Constants — exact field names from docs/data_dictionary_source.md
# ---------------------------------------------------------------------------

HOSPITAL_MASTER_COLS = [
    "hospital_id", "hospital_name", "hospital_short_name", "hospital_type",
    "bed_licensed_total", "region", "country", "status",
    "effective_from", "effective_to", "source_system", "record_version",
    "record_created_datetime", "record_updated_datetime",
]

DEPARTMENT_MASTER_COLS = [
    "department_id", "hospital_id", "department_name", "department_type",
    "parent_department_id", "bed_licensed", "bed_staffed", "bed_operational",
    "is_active", "effective_from", "effective_to", "source_system",
    "record_version", "record_created_datetime", "record_updated_datetime",
]

STAFF_ROLE_MASTER_COLS = [
    "role_id", "role_name", "staff_category", "is_clinical", "is_active",
    "effective_from", "effective_to", "source_system", "record_version",
    "record_created_datetime", "record_updated_datetime",
]

STAFF_MASTER_COLS = [
    "staff_id", "hospital_id", "department_id", "role_id", "staff_name",
    "email", "phone_number", "ic_number", "address", "employment_type",
    "fte_value", "is_active", "employment_start_date", "employment_end_date",
    "source_system", "record_version", "record_created_datetime", "record_updated_datetime",
]

STAFF_ROSTER_COLS = [
    "roster_id", "staff_id", "hospital_id", "department_id", "role_id",
    "roster_date", "shift_code", "planned_start_datetime", "planned_end_datetime",
    "planned_hours", "status", "version", "source_system",
    "record_created_datetime", "record_updated_datetime",
]

STAFF_ATTENDANCE_COLS = [
    "attendance_id", "staff_id", "hospital_id", "department_id", "role_id",
    "roster_id", "attendance_date", "shift_code", "status",
    "actual_start_datetime", "actual_end_datetime", "actual_hours",
    "replacement_staff_id", "notes", "source_system", "created_at",
]

STAFFING_REQUIREMENT_COLS = [
    "requirement_id", "hospital_id", "department_id", "role_id",
    "requirement_date", "shift_code", "required_staff_count", "required_hours",
    "source_system", "created_at",
]

PATIENT_ENCOUNTER_COLS = [
    "encounter_id", "hospital_id", "department_id", "patient_id",
    "encounter_date", "encounter_type", "arrival_datetime", "service_start_datetime",
    "service_end_datetime", "status", "cancellation_reason", "triage_category",
    "source_system", "record_created_datetime",
]

PATIENT_QUEUE_RECORD_COLS = [
    "queue_id", "hospital_id", "department_id", "queue_date", "queue_type",
    "period_start", "period_end", "arrivals_count", "served_count",
    "waiting_count", "avg_wait_minutes", "median_wait_minutes", "max_wait_minutes",
    "source_system", "created_at",
]

BED_CAPACITY_RECORD_COLS = [
    "record_id", "hospital_id", "department_id", "record_date",
    "bed_licensed", "bed_staffed", "bed_operational", "bed_occupied",
    "bed_unavailable", "bed_reserved", "occupancy_rate",
    "exception_flag", "exception_reason", "source_system", "created_at",
]

PATIENT_COMPLAINT_COLS = [
    "complaint_id", "hospital_id", "department_id", "encounter_id",
    "complaint_received_date", "complaint_channel", "complaint_category",
    "severity", "description", "status", "resolution_date", "outcome_category",
    "duplicate_flag", "duplicate_of_complaint_id", "source_system", "created_at",
]

PATIENT_SURVEY_COLS = [
    "survey_id", "hospital_id", "department_id", "encounter_id",
    "survey_date", "survey_type", "scale_id", "score_value",
    "response_weight", "is_complete", "source_system", "created_at",
]

SERVICE_SCHEDULE_COLS = [
    "schedule_id", "hospital_id", "department_id", "service_date",
    "planned_start_time", "planned_end_time", "planned_hours",
    "planned_capacity", "schedule_status", "shift_code",
    "source_system", "created_at",
]

# Valid domains
VALID_ATTENDANCE_STATUSES = ["Present", "Absent", "Late", "Partial", "Leave", "Training", "Reassigned", "Not Scheduled"]
VALID_COMPLAINT_CHANNELS = ["Walk-In", "Phone", "Email", "Formal Letter", "Online Portal", "Social Media", "Third Party"]
VALID_COMPLAINT_CATEGORIES = ["Waiting Time", "Staff Behaviour", "Facilities", "Billing", "Clinical Care", "Communication", "Safety", "Other"]
VALID_COMPLAINT_STATUSES = ["Received", "Under Review", "Investigating", "Resolved", "Closed", "Escalated"]
VALID_COMPLAINT_SEVERITIES = ["Low", "Medium", "High", "Critical"]
VALID_ENCOUNTER_TYPES = ["Scheduled Visit", "Walk-In", "Emergency", "Follow-up", "Referral"]
VALID_ENCOUNTER_STATUSES = ["Completed", "Cancelled", "Left Before Service", "In Progress"]
VALID_EMPLOYMENT_TYPES = ["Full-Time", "Part-Time", "Contract"]
VALID_TRIAGE_CATEGORIES = ["Critical", "Urgent", "Semi-Urgent", "Non-Urgent"]
VALID_QUEUE_TYPES = ["Registration", "Triage", "Consultation", "Pharmacy", "Radiology", "Billing"]
VALID_SCHEDULE_STATUSES = ["Planned", "Active", "Reduced", "Cancelled", "Extended"]


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class SyntheticHospitalDataGenerator:
    """
    Reproducible generator for synthetic hospital operational source data.

    Parameters
    ----------
    config : GeneratorConfig, optional
        Runtime generation configuration. Uses defaults if omitted.
    seed : int, optional
        Deterministic random seed. Default is taken from config if not supplied.
    """

    def __init__(self, config: Optional[GeneratorConfig] = None, seed: Optional[int] = None) -> None:
        self.config = config or get_default_config()
        self.seed = seed if seed is not None else self.config.seed
        self.rng = np.random.default_rng(self.seed)
        self._data: Dict[str, pd.DataFrame] = {}
        self._refs: Dict[str, Any] = {}
        # Deterministic reference timestamp for all record_created / updated fields
        self._reference_datetime = datetime(2025, 1, 1, 0, 0, 0)

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def generate_all(self) -> Dict[str, pd.DataFrame]:
        """
        Generate all 13 source datasets and return them as a dictionary.

        Does NOT write CSV files automatically.
        """
        self._reset_state()
        self._data["hospital_master"] = self.generate_hospital_master()
        self._data["department_master"] = self.generate_department_master()
        self._data["staff_role_master"] = self.generate_staff_role_master()
        self._data["staff_master"] = self.generate_staff_master()
        self._data["staffing_requirement"] = self.generate_staffing_requirement()
        self._data["service_schedule"] = self.generate_service_schedule()
        self._data["staff_roster"] = self.generate_staff_roster()
        self._data["staff_attendance"] = self.generate_staff_attendance()
        self._data["patient_encounters"] = self.generate_patient_encounters()
        self._data["patient_queue_records"] = self.generate_patient_queue_records()
        self._data["bed_capacity_records"] = self.generate_bed_capacity_records()
        self._data["patient_complaints"] = self.generate_patient_complaints()
        self._data["patient_surveys"] = self.generate_patient_surveys()
        self._run_self_checks()
        return self._data.copy()

    def export_to_csv(self, output_dir: Optional[Path] = None) -> None:
        """
        Export generated datasets to CSV files.

        Not called automatically by generate_all().
        """
        out = output_dir or self.config.output_dir
        out.mkdir(parents=True, exist_ok=True)
        for name, df in self._data.items():
            filepath = out / f"{name}.csv"
            df.to_csv(filepath, index=False)

    # -----------------------------------------------------------------------
    # Dataset Generators
    # -----------------------------------------------------------------------

    def generate_hospital_master(self) -> pd.DataFrame:
        """Generate hospital_master."""
        hosp = self.config.hospital.copy()
        now = self._reference_datetime
        records = [{
            **hosp,
            "record_created_datetime": now,
            "record_updated_datetime": now,
        }]
        df = pd.DataFrame(records, columns=HOSPITAL_MASTER_COLS)
        self._inject_defects(df, "hospital_master")
        return df

    def generate_department_master(self) -> pd.DataFrame:
        """Generate department_master."""
        hospital_id = self.config.hospital["hospital_id"]
        now = self._reference_datetime
        records = []
        for dept in self.config.departments:
            record = {
                "department_id": dept["department_id"],
                "hospital_id": hospital_id,
                "department_name": dept["department_name"],
                "department_type": dept["department_type"],
                "parent_department_id": None,
                "bed_licensed": dept.get("bed_licensed", 0),
                "bed_staffed": dept.get("bed_licensed", 0),
                "bed_operational": dept.get("bed_licensed", 0),
                "is_active": True,
                "effective_from": date(2020, 1, 1),
                "effective_to": date(2099, 12, 31),
                "source_system": "SENTINEL_DEMO_DEPT",
                "record_version": 1,
                "record_created_datetime": now,
                "record_updated_datetime": now,
            }
            records.append(record)
        df = pd.DataFrame(records, columns=DEPARTMENT_MASTER_COLS)
        self._inject_defects(df, "department_master")
        return df

    def generate_staff_role_master(self) -> pd.DataFrame:
        """Generate staff_role_master."""
        now = self._reference_datetime
        records = []
        for role in self.config.staff_roles:
            record = {
                "role_id": role["role_id"],
                "role_name": role["role_name"],
                "staff_category": role["staff_category"],
                "is_clinical": role["is_clinical"],
                "is_active": True,
                "effective_from": role["effective_from"],
                "effective_to": role["effective_to"],
                "source_system": "SENTINEL_DEMO_ROLE",
                "record_version": 1,
                "record_created_datetime": now,
                "record_updated_datetime": now,
            }
            records.append(record)
        df = pd.DataFrame(records, columns=STAFF_ROLE_MASTER_COLS)
        self._inject_defects(df, "staff_role_master")
        return df

    def generate_staff_master(self) -> pd.DataFrame:
        """Generate staff_master with anonymised staff."""
        hospital_id = self.config.hospital["hospital_id"]
        depts = self.config.departments
        roles = self.config.staff_roles
        now = self._reference_datetime
        n_staff = self.config.volumes["staff"]

        records = []
        for i in range(1, n_staff + 1):
            dept = self.rng.choice(depts)
            role = self.rng.choice(roles)
            emp_type = self.rng.choice(VALID_EMPLOYMENT_TYPES, p=[0.6, 0.25, 0.15])
            fte = {"Full-Time": 1.0, "Part-Time": self.rng.choice([0.5, 0.6]), "Contract": self.rng.choice([0.5, 0.75, 1.0])}[emp_type]
            start_offset = self.rng.integers(0, 730)
            emp_start = self.config.start_date - timedelta(days=int(start_offset))
            record = {
                "staff_id": f"STAFF-{i:04d}",
                "hospital_id": hospital_id,
                "department_id": dept["department_id"],
                "role_id": role["role_id"],
                "staff_name": None,
                "email": None,
                "phone_number": None,
                "ic_number": None,
                "address": None,
                "employment_type": emp_type,
                "fte_value": fte,
                "is_active": True,
                "employment_start_date": emp_start,
                "employment_end_date": None,
                "source_system": "SENTINEL_DEMO_HR",
                "record_version": 1,
                "record_created_datetime": now,
                "record_updated_datetime": now,
            }
            records.append(record)
        df = pd.DataFrame(records, columns=STAFF_MASTER_COLS)
        self._inject_defects(df, "staff_master")
        return df

    def generate_staffing_requirement(self) -> pd.DataFrame:
        """Generate approved staffing requirements by date, dept, shift, role."""
        hospital_id = self.config.hospital["hospital_id"]
        depts = [d for d in self.config.departments if d.get("has_staffing", True)]
        roles = self.config.staff_roles
        shifts = self.config.shifts
        dates = self._date_range()
        records = []
        req_counter = 1
        for d in dates:
            for dept in depts:
                for role in roles:
                    for shift in shifts:
                        base_count = self._base_required_count(dept, role)
                        record = {
                            "requirement_id": f"REQ-{req_counter:07d}",
                            "hospital_id": hospital_id,
                            "department_id": dept["department_id"],
                            "role_id": role["role_id"],
                            "requirement_date": d,
                            "shift_code": shift["shift_code"],
                            "required_staff_count": max(0, base_count),
                            "required_hours": shift["planned_hours"] * max(0, base_count),
                            "source_system": "SENTINEL_DEMO_PLAN",
                            "created_at": self._reference_datetime,
                        }
                        records.append(record)
                        req_counter += 1
        df = pd.DataFrame(records, columns=STAFFING_REQUIREMENT_COLS)
        self._inject_defects(df, "staffing_requirement")
        return df

    def generate_service_schedule(self) -> pd.DataFrame:
        """Generate planned service sessions."""
        hospital_id = self.config.hospital["hospital_id"]
        depts = [d for d in self.config.departments if d.get("has_staffing", True)]
        shifts = self.config.shifts
        dates = self._date_range()
        records = []
        sched_counter = 1
        for d in dates:
            phase = self.config.get_phase_for_date(d)
            for dept in depts:
                for shift in shifts:
                    status = "Planned"
                    capacity_factor = 1.0
                    if phase["phase_id"] in ("P4",):
                        if self.rng.random() < 0.05:
                            status = self.rng.choice(["Reduced", "Cancelled"])
                            capacity_factor = 0.5 if status == "Reduced" else 0.0
                    base_capacity = self._base_service_capacity(dept)
                    record = {
                        "schedule_id": f"SCH-{sched_counter:08d}",
                        "hospital_id": hospital_id,
                        "department_id": dept["department_id"],
                        "service_date": d,
                        "planned_start_time": shift["planned_start_time"],
                        "planned_end_time": shift["planned_end_time"],
                        "planned_hours": shift["planned_hours"],
                        "planned_capacity": int(base_capacity * capacity_factor),
                        "schedule_status": status,
                        "shift_code": shift["shift_code"],
                        "source_system": "SENTINEL_DEMO_SCHED",
                        "created_at": self._reference_datetime,
                    }
                    records.append(record)
                    sched_counter += 1
        df = pd.DataFrame(records, columns=SERVICE_SCHEDULE_COLS)
        self._inject_defects(df, "service_schedule")
        return df

    def generate_staff_roster(self) -> pd.DataFrame:
        """Generate planned staff assignments by date and shift."""
        hospital_id = self.config.hospital["hospital_id"]
        staff_df = self._data.get("staff_master")
        if staff_df is None:
            raise RuntimeError("staff_master must be generated before staff_roster")
        shifts = self.config.shifts
        dates = self._date_range()
        now = self._reference_datetime
        records = []
        roster_counter = 1
        work_prob_map = {"Full-Time": 5 / 7, "Part-Time": 3 / 7, "Contract": 4 / 7}
        for _, staff in staff_df.iterrows():
            emp_type = staff["employment_type"]
            if pd.isna(emp_type):
                continue
            work_prob = work_prob_map.get(str(emp_type), 4 / 7)
            for d in dates:
                if d < staff["employment_start_date"]:
                    continue
                if staff["employment_end_date"] is not None and d > staff["employment_end_date"]:
                    continue
                if self.rng.random() > work_prob:
                    continue
                shift = self.rng.choice(shifts)
                start_dt = datetime.combine(d, shift["planned_start_time"])
                end_dt = self._shift_end_datetime(d, shift)
                record = {
                    "roster_id": f"ROSTER-{roster_counter:08d}",
                    "staff_id": staff["staff_id"],
                    "hospital_id": hospital_id,
                    "department_id": staff["department_id"],
                    "role_id": staff["role_id"],
                    "roster_date": d,
                    "shift_code": shift["shift_code"],
                    "planned_start_datetime": start_dt,
                    "planned_end_datetime": end_dt,
                    "planned_hours": shift["planned_hours"],
                    "status": "Active",
                    "version": 1,
                    "source_system": "SENTINEL_DEMO_ROSTER",
                    "record_created_datetime": now,
                    "record_updated_datetime": now,
                }
                records.append(record)
                roster_counter += 1
        df = pd.DataFrame(records, columns=STAFF_ROSTER_COLS)
        self._inject_defects(df, "staff_roster")
        return df

    def generate_staff_attendance(self) -> pd.DataFrame:
        """Generate actual attendance aligned with roster."""
        roster_df = self._data.get("staff_roster")
        if roster_df is None:
            raise RuntimeError("staff_roster must be generated before staff_attendance")
        now = self._reference_datetime
        records = []
        attendance_counter = 1
        for _, roster in roster_df.iterrows():
            d = roster["roster_date"]
            phase = self.config.get_phase_for_date(d)
            base_probs = self.config.attendance_baseline.copy()
            absence_boost = phase["absence_probability_factor"]
            # Adjust: increase Absent/Late/Partial, decrease Present
            base_probs["Absent"] = min(0.35, base_probs["Absent"] * absence_boost)
            base_probs["Late"] = min(0.15, base_probs["Late"] * (1 + (absence_boost - 1) * 0.5))
            base_probs["Partial"] = min(0.10, base_probs["Partial"] * (1 + (absence_boost - 1) * 0.5))
            base_probs["Present"] = max(0.0, 1.0 - sum(v for k, v in base_probs.items() if k != "Present"))
            statuses = list(base_probs.keys())
            probs = np.array([base_probs[s] for s in statuses], dtype=float)
            probs = probs / probs.sum()
            status = self.rng.choice(statuses, p=probs)
            planned_hours = roster["planned_hours"]
            actual_hours = self._actual_hours_for_status(status, planned_hours)
            start_dt = roster["planned_start_datetime"]
            end_dt = start_dt + timedelta(hours=actual_hours) if actual_hours > 0 else None
            replacement = None
            if status == "Reassigned":
                # Pick a random other staff as replacement reference
                staff_pool = self._data["staff_master"]["staff_id"].tolist()
                if len(staff_pool) > 1:
                    replacement = self.rng.choice([s for s in staff_pool if s != roster["staff_id"]])
            record = {
                "attendance_id": f"ATT-{attendance_counter:08d}",
                "staff_id": roster["staff_id"],
                "hospital_id": roster["hospital_id"],
                "department_id": roster["department_id"],
                "role_id": roster["role_id"],
                "roster_id": roster["roster_id"],
                "attendance_date": d,
                "shift_code": roster["shift_code"],
                "status": status,
                "actual_start_datetime": start_dt if status not in ("Absent", "Not Scheduled") else None,
                "actual_end_datetime": end_dt if status not in ("Absent", "Not Scheduled") else None,
                "actual_hours": actual_hours,
                "replacement_staff_id": replacement,
                "notes": None,
                "source_system": "SENTINEL_DEMO_ATT",
                "created_at": now,
            }
            records.append(record)
            attendance_counter += 1
        df = pd.DataFrame(records, columns=STAFF_ATTENDANCE_COLS)
        self._inject_defects(df, "staff_attendance")
        return df

    def generate_patient_encounters(self) -> pd.DataFrame:
        """Generate anonymised patient encounters with timestamps."""
        hospital_id = self.config.hospital["hospital_id"]
        depts = [d for d in self.config.departments if d.get("has_queue", False)]
        dates = self._date_range()
        now = self._reference_datetime
        records = []
        encounter_counter = 1
        base_encounters = self.config.volumes["patient_encounters_per_day"]
        for d in dates:
            phase = self.config.get_phase_for_date(d)
            n_encounters = int(base_encounters * phase["patient_volume_factor"] * self.rng.uniform(0.85, 1.15))
            # Distribute across departments
            dept_weights = np.array([self._dept_encounter_weight(d) for d in depts], dtype=float)
            dept_weights = dept_weights / dept_weights.sum()
            dept_counts = self.rng.multinomial(n_encounters, dept_weights)
            for dept, count in zip(depts, dept_counts):
                for _ in range(count):
                    arrival_hour = self._sample_arrival_hour()
                    arrival_dt = datetime.combine(d, time(arrival_hour, self.rng.integers(0, 60)))
                    triage = self.rng.choice(VALID_TRIAGE_CATEGORIES, p=[0.05, 0.25, 0.40, 0.30])
                    enc_type = self._encounter_type_for_dept(dept)
                    status = "Completed"
                    cancel_reason = None
                    if self.rng.random() < 0.03:
                        status = self.rng.choice(["Cancelled", "Left Before Service"])
                        cancel_reason = "Patient request" if status == "Cancelled" else "Long wait"
                    # Wait time depends on phase
                    wait_base = {"Critical": 5, "Urgent": 15, "Semi-Urgent": 30, "Non-Urgent": 45}[triage]
                    wait_minutes = int(wait_base * phase["wait_time_factor"] * self.rng.uniform(0.8, 1.4))
                    service_start = arrival_dt + timedelta(minutes=wait_minutes)
                    service_duration = int(self.rng.exponential(20) + 10)
                    service_end = service_start + timedelta(minutes=service_duration) if status == "Completed" else None
                    record = {
                        "encounter_id": f"ENC-{encounter_counter:09d}",
                        "hospital_id": hospital_id,
                        "department_id": dept["department_id"],
                        "patient_id": f"PAT-{encounter_counter:010d}",
                        "encounter_date": d,
                        "encounter_type": enc_type,
                        "arrival_datetime": arrival_dt,
                        "service_start_datetime": service_start if status == "Completed" else None,
                        "service_end_datetime": service_end,
                        "status": status,
                        "cancellation_reason": cancel_reason,
                        "triage_category": triage,
                        "source_system": "SENTINEL_DEMO_ENC",
                        "record_created_datetime": now,
                    }
                    records.append(record)
                    encounter_counter += 1
        df = pd.DataFrame(records, columns=PATIENT_ENCOUNTER_COLS)
        self._inject_defects(df, "patient_encounters")
        return df

    def generate_patient_queue_records(self) -> pd.DataFrame:
        """Generate queue summaries derived from encounter records."""
        enc_df = self._data.get("patient_encounters")
        if enc_df is None:
            raise RuntimeError("patient_encounters must be generated before patient_queue_records")
        hospital_id = self.config.hospital["hospital_id"]
        now = self._reference_datetime
        records = []
        queue_counter = 1
        # Derive by department and date
        for (dept_id, d), group in enc_df.groupby(["department_id", "encounter_date"]):
            arrivals = len(group)
            served = (group["status"] == "Completed").sum()
            waiting = arrivals - served
            valid_waits = group[group["status"] == "Completed"].copy()
            if len(valid_waits) > 0:
                wait_minutes = (valid_waits["service_start_datetime"] - valid_waits["arrival_datetime"]).dt.total_seconds() / 60.0
                avg_wait = round(wait_minutes.mean(), 1)
                median_wait = round(wait_minutes.median(), 1)
                max_wait = round(wait_minutes.max(), 1)
            else:
                avg_wait = median_wait = max_wait = 0.0
            # Morning / Evening / Night split (simplified: daily summary)
            queue_type = self.rng.choice(VALID_QUEUE_TYPES)
            record = {
                "queue_id": f"QUEUE-{queue_counter:09d}",
                "hospital_id": hospital_id,
                "department_id": dept_id,
                "queue_date": d,
                "queue_type": queue_type,
                "period_start": datetime.combine(d, time(0, 0)),
                "period_end": datetime.combine(d, time(23, 59)),
                "arrivals_count": arrivals,
                "served_count": int(served),
                "waiting_count": int(waiting),
                "avg_wait_minutes": avg_wait,
                "median_wait_minutes": median_wait,
                "max_wait_minutes": max_wait,
                "source_system": "SENTINEL_DEMO_QUEUE",
                "created_at": now,
            }
            records.append(record)
            queue_counter += 1
        df = pd.DataFrame(records, columns=PATIENT_QUEUE_RECORD_COLS)
        self._inject_defects(df, "patient_queue_records")
        return df

    def generate_bed_capacity_records(self) -> pd.DataFrame:
        """Generate daily bed capacity for bed-based departments."""
        hospital_id = self.config.hospital["hospital_id"]
        depts = [d for d in self.config.departments if d.get("is_bed_based", False)]
        dates = self._date_range()
        now = self._reference_datetime
        records = []
        record_counter = 1
        for d in dates:
            phase = self.config.get_phase_for_date(d)
            for dept in depts:
                licensed = dept["bed_licensed"]
                staffed = int(licensed * self.rng.uniform(0.90, 1.0))
                operational = int(staffed * self.rng.uniform(0.92, 1.0))
                demand_factor = phase["bed_demand_factor"]
                occupied = int(operational * self.rng.uniform(0.75, 0.95) * demand_factor)
                unavailable = licensed - operational
                reserved = int(operational * self.rng.uniform(0.0, 0.05))
                occupancy_rate = (occupied / operational * 100.0) if operational > 0 else 0.0
                exception_flag = False
                exception_reason = None
                if occupied > operational:
                    exception_flag = True
                    exception_reason = "Occupied exceeds operational capacity"
                record = {
                    "record_id": f"BED-{record_counter:09d}",
                    "hospital_id": hospital_id,
                    "department_id": dept["department_id"],
                    "record_date": d,
                    "bed_licensed": licensed,
                    "bed_staffed": staffed,
                    "bed_operational": operational,
                    "bed_occupied": occupied,
                    "bed_unavailable": unavailable,
                    "bed_reserved": reserved,
                    "occupancy_rate": round(occupancy_rate, 2),
                    "exception_flag": exception_flag,
                    "exception_reason": exception_reason,
                    "source_system": "SENTINEL_DEMO_BED",
                    "created_at": now,
                }
                records.append(record)
                record_counter += 1
        df = pd.DataFrame(records, columns=BED_CAPACITY_RECORD_COLS)
        self._inject_defects(df, "bed_capacity_records")
        return df

    def generate_patient_complaints(self) -> pd.DataFrame:
        """Generate complaint events with phase-linked probability."""
        hospital_id = self.config.hospital["hospital_id"]
        enc_df = self._data.get("patient_encounters")
        depts = self.config.departments
        dates = self._date_range()
        now = self._reference_datetime
        records = []
        complaint_counter = 1
        base_complaints = self.config.volumes["complaints_per_day"]
        for d in dates:
            phase = self.config.get_phase_for_date(d)
            n_complaints = int(base_complaints * phase["complaint_probability_factor"] * self.rng.uniform(0.5, 1.5))
            for _ in range(n_complaints):
                dept = self.rng.choice(depts)
                enc_id = None
                if enc_df is not None and self.rng.random() < 0.4:
                    day_encs = enc_df[enc_df["encounter_date"] == d]
                    if len(day_encs) > 0:
                        enc_id = self.rng.choice(day_encs["encounter_id"].tolist())
                severity = self.rng.choice(VALID_COMPLAINT_SEVERITIES, p=[0.35, 0.40, 0.20, 0.05])
                status = self.rng.choice(VALID_COMPLAINT_STATUSES, p=[0.30, 0.25, 0.20, 0.15, 0.08, 0.02])
                record = {
                    "complaint_id": f"COMP-{complaint_counter:08d}",
                    "hospital_id": hospital_id,
                    "department_id": dept["department_id"],
                    "encounter_id": enc_id,
                    "complaint_received_date": d,
                    "complaint_channel": self.rng.choice(VALID_COMPLAINT_CHANNELS),
                    "complaint_category": self.rng.choice(VALID_COMPLAINT_CATEGORIES),
                    "severity": severity,
                    "description": None,
                    "status": status,
                    "resolution_date": d + timedelta(days=int(self.rng.integers(1, 15))) if status in ("Resolved", "Closed") else None,
                    "outcome_category": None,
                    "duplicate_flag": False,
                    "duplicate_of_complaint_id": None,
                    "source_system": "SENTINEL_DEMO_PEX",
                    "created_at": now,
                }
                records.append(record)
                complaint_counter += 1
        df = pd.DataFrame(records, columns=PATIENT_COMPLAINT_COLS)
        self._inject_defects(df, "patient_complaints")
        return df

    def generate_patient_surveys(self) -> pd.DataFrame:
        """Generate anonymised survey responses with phase-linked satisfaction."""
        hospital_id = self.config.hospital["hospital_id"]
        depts = self.config.departments
        dates = self._date_range()
        now = self._reference_datetime
        records = []
        survey_counter = 1
        base_surveys = self.config.volumes["surveys_per_day"]
        scale = self.config.survey_scales[0]  # 5-point default
        for d in dates:
            phase = self.config.get_phase_for_date(d)
            n_surveys = int(base_surveys * self.rng.uniform(0.7, 1.3))
            for _ in range(n_surveys):
                dept = self.rng.choice(depts)
                # Satisfaction mean shifts by phase
                sat_mean = 3.8 * phase["satisfaction_mean_factor"]
                score = float(np.clip(self.rng.normal(sat_mean, 0.7), scale["min_score"], scale["max_score"]))
                is_complete = self.rng.random() < 0.92
                if not is_complete:
                    score = None
                record = {
                    "survey_id": f"SURV-{survey_counter:08d}",
                    "hospital_id": hospital_id,
                    "department_id": dept["department_id"],
                    "encounter_id": None,
                    "survey_date": d,
                    "survey_type": "Outpatient Satisfaction",
                    "scale_id": scale["scale_id"],
                    "score_value": score,
                    "response_weight": 1.0,
                    "is_complete": is_complete,
                    "source_system": "SENTINEL_DEMO_SURV",
                    "created_at": now,
                }
                records.append(record)
                survey_counter += 1
        df = pd.DataFrame(records, columns=PATIENT_SURVEY_COLS)
        self._inject_defects(df, "patient_surveys")
        return df

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _reset_state(self) -> None:
        """Clear internal data and rebuild reference lookups."""
        self._data = {}
        self._refs = {
            "hospital_ids": [],
            "department_ids": [],
            "staff_role_ids": [],
            "staff_ids": [],
            "shift_codes": [],
            "bed_based_dept_ids": [],
            "queue_dept_ids": [],
            "dates": [],
        }

    def _date_range(self) -> List[date]:
        """Return list of dates from start_date to end_date inclusive."""
        start = self.config.start_date
        end = self.config.end_date
        return [start + timedelta(days=i) for i in range((end - start).days + 1)]

    def _shift_end_datetime(self, d: date, shift: Dict[str, Any]) -> datetime:
        """Return shift end datetime, handling overnight."""
        start_dt = datetime.combine(d, shift["planned_start_time"])
        if shift["is_overnight"]:
            end_dt = datetime.combine(d + timedelta(days=1), shift["planned_end_time"])
        else:
            end_dt = datetime.combine(d, shift["planned_end_time"])
        return end_dt

    def _base_required_count(self, dept: Dict[str, Any], role: Dict[str, Any]) -> int:
        """Return a synthetic required staff count for a dept+role combination."""
        # Simple heuristic based on department size and role category
        category_multipliers = {
            "Doctor": 0.15,
            "Nurse": 0.40,
            "Allied Health": 0.15,
            "Support": 0.20,
            "Administrative": 0.25,
        }
        base = 2 if dept.get("has_staffing", True) else 0
        if dept.get("is_bed_based", False):
            base = max(1, int(dept.get("bed_licensed", 0) / 20))
        return max(0, int(base * category_multipliers.get(role["staff_category"], 0.1)))

    def _base_service_capacity(self, dept: Dict[str, Any]) -> int:
        """Return synthetic planned capacity for a department."""
        if dept.get("is_bed_based", False):
            return dept.get("bed_licensed", 0)
        if dept["department_id"] in ("DEPT-ED",):
            return 80
        if dept["department_id"] in ("DEPT-OPC",):
            return 120
        if dept["department_id"] in ("DEPT-DIAG",):
            return 60
        return 20

    def _actual_hours_for_status(self, status: str, planned_hours: float) -> float:
        """Return actual hours worked given attendance status."""
        if status == "Present":
            return planned_hours
        if status == "Absent":
            return 0.0
        if status == "Late":
            return planned_hours * self.rng.uniform(0.75, 0.95)
        if status == "Partial":
            return planned_hours * self.rng.uniform(0.25, 0.60)
        if status == "Leave":
            return 0.0
        if status == "Training":
            return planned_hours
        if status == "Reassigned":
            return planned_hours
        if status == "Not Scheduled":
            return 0.0
        return 0.0

    def _sample_arrival_hour(self) -> int:
        """Sample realistic patient arrival hour."""
        # Higher probability during morning and afternoon
        probs = np.array([1, 1, 1, 1, 2, 3, 5, 8, 10, 9, 8, 7, 7, 6, 5, 4, 3, 2, 2, 1, 1, 1, 1, 1], dtype=float)
        probs = probs / probs.sum()
        return int(self.rng.choice(np.arange(24), p=probs))

    def _dept_encounter_weight(self, dept: Dict[str, Any]) -> float:
        """Return relative encounter weight for a department."""
        weights = {
            "DEPT-ED": 3.0,
            "DEPT-OPC": 2.5,
            "DEPT-DIAG": 1.5,
            "DEPT-MED": 1.0,
            "DEPT-SURG": 0.8,
            "DEPT-ICU": 0.3,
        }
        return weights.get(dept["department_id"], 0.5)

    def _encounter_type_for_dept(self, dept: Dict[str, Any]) -> str:
        """Return a plausible encounter type for a department."""
        mapping = {
            "DEPT-ED": ["Emergency", "Walk-In"],
            "DEPT-OPC": ["Scheduled Visit", "Follow-up", "Walk-In"],
            "DEPT-DIAG": ["Scheduled Visit", "Referral"],
            "DEPT-MED": ["Scheduled Visit", "Emergency", "Referral"],
            "DEPT-SURG": ["Scheduled Visit", "Referral"],
            "DEPT-ICU": ["Emergency", "Referral"],
        }
        choices = mapping.get(dept["department_id"], VALID_ENCOUNTER_TYPES)
        return self.rng.choice(choices)

    # -----------------------------------------------------------------------
    # Defect Injection
    # -----------------------------------------------------------------------

    def _inject_defects(self, df: pd.DataFrame, dataset_name: str) -> None:
        """Apply enabled defect-injection switches to a generated DataFrame."""
        defects = self.config.defects
        if not any(defects.values()):
            return
        rng = self.rng

        if dataset_name == "hospital_master" and defects.get("duplicate_primary_keys"):
            if len(df) > 0:
                df.loc[0, "hospital_id"] = df.loc[0, "hospital_id"]
                # Actually duplicate by appending first row
                df.loc[len(df)] = df.iloc[0].copy()

        if dataset_name == "department_master" and defects.get("unknown_hospital_reference"):
            if len(df) > 0:
                df.loc[0, "hospital_id"] = "HOSP-UNKNOWN"

        if dataset_name == "staff_master" and defects.get("missing_required_values"):
            if len(df) > 0:
                df.loc[0, "employment_type"] = None

        if dataset_name == "staff_master" and defects.get("invalid_staff_role_reference"):
            if len(df) > 0:
                df.loc[0, "role_id"] = "ROLE-INVALID"

        if dataset_name == "staff_roster" and defects.get("invalid_date_order"):
            if len(df) > 0:
                df.loc[0, "planned_end_datetime"] = df.loc[0, "planned_start_datetime"] - timedelta(hours=2)

        if dataset_name == "staff_attendance" and defects.get("attendance_without_roster"):
            if len(df) > 0:
                df.loc[0, "roster_id"] = "ROSTER-NONEXISTENT"

        if dataset_name == "staffing_requirement" and defects.get("negative_values"):
            if len(df) > 0:
                df.loc[0, "required_staff_count"] = -1

        if dataset_name == "patient_encounters" and defects.get("invalid_date_order"):
            if len(df) > 0:
                df.loc[0, "service_start_datetime"] = df.loc[0, "arrival_datetime"] - timedelta(minutes=5)

        if dataset_name == "bed_capacity_records" and defects.get("occupied_above_operational_no_reason"):
            mask = df["bed_occupied"] > df["bed_operational"]
            if mask.any():
                idx = df[mask].index[0]
                df.loc[idx, "exception_flag"] = False
                df.loc[idx, "exception_reason"] = None

        if dataset_name == "patient_surveys" and defects.get("invalid_survey_scale"):
            if len(df) > 0:
                df.loc[0, "score_value"] = 99

        if dataset_name == "patient_complaints" and defects.get("invalid_complaint_status"):
            if len(df) > 0:
                df.loc[0, "status"] = "Unknown Status"

        if dataset_name == "patient_complaints" and defects.get("duplicate_primary_keys"):
            if len(df) > 1:
                df.loc[1, "complaint_id"] = df.loc[0, "complaint_id"]

    # -----------------------------------------------------------------------
    # Self-Checks
    # -----------------------------------------------------------------------

    def _run_self_checks(self) -> None:
        """Lightweight internal validation after generation."""
        expected = {
            "hospital_master", "department_master", "staff_role_master", "staff_master",
            "staff_roster", "staff_attendance", "staffing_requirement", "patient_encounters",
            "patient_queue_records", "bed_capacity_records", "patient_complaints",
            "patient_surveys", "service_schedule",
        }
        missing = expected - set(self._data.keys())
        if missing:
            raise RuntimeError(f"Self-check failed: missing datasets {missing}")

        for name, df in self._data.items():
            if df is None or df.empty:
                warnings.warn(f"Self-check warning: dataset '{name}' is empty", stacklevel=2)

        # Primary-key uniqueness (lightweight)
        pk_map = {
            "hospital_master": "hospital_id",
            "department_master": "department_id",
            "staff_role_master": "role_id",
            "staff_master": "staff_id",
            "staff_roster": "roster_id",
            "staff_attendance": "attendance_id",
            "staffing_requirement": "requirement_id",
            "patient_encounters": "encounter_id",
            "patient_queue_records": "queue_id",
            "bed_capacity_records": "record_id",
            "patient_complaints": "complaint_id",
            "patient_surveys": "survey_id",
            "service_schedule": "schedule_id",
        }
        defects = self.config.defects
        for ds, pk_col in pk_map.items():
            if defects.get("duplicate_primary_keys") and ds in ("hospital_master", "patient_complaints"):
                continue
            df = self._data[ds]
            if df[pk_col].duplicated().any():
                dups = df[pk_col][df[pk_col].duplicated()].tolist()
                raise RuntimeError(f"Self-check failed: duplicate primary keys in {ds}: {dups[:5]}")

        # Foreign-key existence (lightweight spot checks)
        hosp_ids = set(self._data["hospital_master"]["hospital_id"])
        dept_ids = set(self._data["department_master"]["department_id"])
        role_ids = set(self._data["staff_role_master"]["role_id"])
        staff_ids = set(self._data["staff_master"]["staff_id"])

        for ds, fk_col in [("department_master", "hospital_id")]:
            if defects.get("unknown_hospital_reference") and ds == "department_master":
                continue
            orphan = set(self._data[ds][fk_col]) - hosp_ids
            if orphan:
                raise RuntimeError(f"Self-check failed: orphan hospital references in {ds}: {orphan}")

        for ds in ["staff_master", "staff_roster", "staff_attendance", "staffing_requirement",
                   "service_schedule", "patient_encounters", "patient_queue_records",
                   "bed_capacity_records", "patient_complaints", "patient_surveys"]:
            if "department_id" in self._data[ds].columns:
                if defects.get("unknown_department_reference"):
                    continue
                orphan = set(self._data[ds]["department_id"]) - dept_ids
                if orphan:
                    raise RuntimeError(f"Self-check failed: orphan department references in {ds}: {orphan}")

        # Role FK spot check
        if not defects.get("invalid_staff_role_reference"):
            orphan_role = set(self._data["staff_master"]["role_id"]) - role_ids
            if orphan_role:
                raise RuntimeError(f"Self-check failed: orphan role references in staff_master: {orphan_role}")

        # Roster FK spot check
        if not defects.get("attendance_without_roster"):
            roster_ids = set(self._data["staff_roster"]["roster_id"])
            orphan_roster = set(self._data["staff_attendance"]["roster_id"]) - roster_ids
            if orphan_roster:
                raise RuntimeError(f"Self-check failed: orphan roster references in staff_attendance: {orphan_roster}")

        # Date-range check
        for ds in ["staff_roster", "staff_attendance", "patient_encounters", "patient_queue_records",
                   "bed_capacity_records", "patient_complaints", "patient_surveys", "service_schedule",
                   "staffing_requirement"]:
            date_col = None
            for c in ["roster_date", "attendance_date", "encounter_date", "queue_date",
                      "record_date", "complaint_received_date", "survey_date", "service_date",
                      "requirement_date"]:
                if c in self._data[ds].columns:
                    date_col = c
                    break
            if date_col:
                min_d = self._data[ds][date_col].min()
                max_d = self._data[ds][date_col].max()
                if min_d < self.config.start_date or max_d > self.config.end_date:
                    raise RuntimeError(f"Self-check failed: date range violation in {ds}")

        # No PII fields populated
        staff_df = self._data["staff_master"]
        pii_cols = ["staff_name", "email", "phone_number", "ic_number", "address"]
        for col in pii_cols:
            if col in staff_df.columns and staff_df[col].notna().any():
                raise RuntimeError(f"Self-check failed: PII column '{col}' populated in staff_master")

        # Non-negative counts where required
        non_neg_cols = {
            "staffing_requirement": ["required_staff_count", "required_hours"],
            "patient_queue_records": ["arrivals_count", "served_count", "waiting_count"],
            "bed_capacity_records": ["bed_licensed", "bed_staffed", "bed_operational", "bed_occupied", "bed_unavailable", "bed_reserved"],
            "service_schedule": ["planned_capacity", "planned_hours"],
        }
        if not defects.get("negative_values"):
            for ds, cols in non_neg_cols.items():
                for col in cols:
                    if col in self._data[ds].columns and (self._data[ds][col] < 0).any():
                        raise RuntimeError(f"Self-check failed: negative value in {ds}.{col}")

        # Timestamp ordering for encounters
        if not defects.get("invalid_date_order"):
            enc = self._data["patient_encounters"]
            completed = enc[enc["status"] == "Completed"]
            if len(completed) > 0:
                invalid = completed[completed["service_start_datetime"] < completed["arrival_datetime"]]
                if len(invalid) > 0:
                    raise RuntimeError(f"Self-check failed: invalid timestamp order in patient_encounters ({len(invalid)} rows)")

        # Mandatory field nulls (spot check)
        if not defects.get("missing_required_values"):
            mandatory = {
                "staff_master": ["staff_id", "hospital_id", "department_id", "role_id"],
                "patient_encounters": ["encounter_id", "hospital_id", "department_id", "arrival_datetime"],
                "staff_attendance": ["attendance_id", "staff_id", "roster_id"],
            }
            for ds, cols in mandatory.items():
                for col in cols:
                    if col in self._data[ds].columns and self._data[ds][col].isna().any():
                        raise RuntimeError(f"Self-check failed: null values in mandatory {ds}.{col}")
