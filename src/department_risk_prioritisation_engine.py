"""Department Risk Prioritisation Engine for Step 2B-3.

Aggregates KPI-level risk scores into department-date risk records,
identifies dominant drivers, evaluates multi-KPI concurrence,
and produces deterministic rankings.
"""

import os
import uuid
from datetime import datetime

import pandas as pd
import numpy as np


class DepartmentRiskPrioritisationEngine:
    """Aggregate KPI risks and produce department-level prioritisation."""

    def __init__(self, config_dir=None, engine_run_id=None):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        self.config_dir = config_dir or os.path.join(project_root, "config")
        self.engine_run_id = engine_run_id or f"DEPT-RISK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.processed_at = datetime.now().isoformat()
        self.configs = {}

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------
    def load_configs(self):
        self.configs["aggregation"] = pd.read_csv(os.path.join(self.config_dir, "department_risk_aggregation_config.csv"))
        self.configs["tiers"] = pd.read_csv(os.path.join(self.config_dir, "risk_priority_tier_config.csv"))
        self.configs["urgency"] = pd.read_csv(os.path.join(self.config_dir, "risk_urgency_rule_config.csv"))
        self.configs["tiebreaker"] = pd.read_csv(os.path.join(self.config_dir, "risk_ranking_tiebreaker_config.csv"))
        self.configs["governance"] = pd.read_csv(os.path.join(self.config_dir, "risk_governance_adjustment_config.csv"))

        agg = {}
        for _, row in self.configs["aggregation"].iterrows():
            agg[row["parameter_name"]] = float(row["parameter_value"])
        self.agg_weights = agg

        gov = self.configs["governance"]
        self.provisional_materiality_threshold = self._get_gov_param(gov, "provisional_materiality_threshold", 15.0)
        self.provisional_minor_threshold = self._get_gov_param(gov, "provisional_minor_threshold", 5.0)

    def _get_gov_param(self, gov_df, param_name, default):
        """Safely extract a float governance parameter."""
        if gov_df is None or gov_df.empty:
            return default
        mask = gov_df["parameter_name"] == param_name
        if not mask.any():
            return default
        return float(gov_df.loc[mask, "parameter_value"].iloc[0])

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------
    def aggregate(self, kpi_df):
        """Produce one department-date risk record from KPI risk scores."""
        # Only assessable KPIs contribute to numeric aggregation
        assessable = kpi_df["calculation_status"] == "Calculated"
        df_work = kpi_df.copy()
        df_work.loc[~assessable, "kpi_risk_score_normalized"] = np.nan

        grp = df_work.groupby(["hospital_id", "department_id", "reporting_date"])

        # Basic counts
        counts = grp["kpi_id"].count().rename("kpi_count")
        assessable_counts = grp.apply(lambda g: g["calculation_status"].eq("Calculated").sum(), include_groups=False).rename("assessable_kpi_count")
        unavailable_counts = grp.apply(lambda g: g["calculation_status"].ne("Calculated").sum(), include_groups=False).rename("unavailable_kpi_count")

        # State counts
        green_counts = grp.apply(lambda g: (g["threshold_state"].isin(["Green", "Normal Operating Band"])).sum(), include_groups=False).rename("green_kpi_count")
        amber_counts = grp.apply(lambda g: (g["threshold_state"].isin(["Amber", "Lower Amber", "Upper Amber"])).sum(), include_groups=False).rename("amber_kpi_count")
        red_counts = grp.apply(lambda g: (g["threshold_state"] == "Red").sum(), include_groups=False).rename("red_kpi_count")
        critical_counts = grp.apply(lambda g: (g["threshold_state"] == "Critical Capacity Pressure").sum(), include_groups=False).rename("critical_kpi_count")
        low_util_counts = grp.apply(lambda g: (g["threshold_state"] == "Low Utilisation").sum(), include_groups=False).rename("low_utilisation_count")

        # Watch / breach / trend counts
        watch_counts = grp.apply(lambda g: (g["watch_condition_flag"] == True).sum(), include_groups=False).rename("watch_condition_count")
        high_watch_counts = grp.apply(lambda g: (g["watch_severity"] == "High").sum(), include_groups=False).rename("high_watch_count")
        critical_watch_counts = grp.apply(lambda g: (g["watch_severity"] == "Critical").sum(), include_groups=False).rename("critical_watch_count")
        repeated_breach_counts = grp.apply(
            lambda g: ((g["repeated_red_flag"] == True) | (g["repeated_amber_flag"] == True)).sum(),
            include_groups=False
        ).rename("repeated_breach_count")
        deteriorating_counts = grp.apply(
            lambda g: (g["operational_trend_interpretation"] == "Deteriorating").sum(),
            include_groups=False
        ).rename("deteriorating_kpi_count")
        provisional_counts = grp.apply(
            lambda g: (g["threshold_is_provisional"] == True).sum(),
            include_groups=False
        ).rename("provisional_kpi_count")

        # Max / average risk scores
        max_scores = grp["kpi_risk_score_normalized"].max().rename("maximum_kpi_risk_score")
        avg_scores = grp["kpi_risk_score_normalized"].mean().rename("average_assessable_kpi_risk_score")

        dept = pd.concat([
            counts, assessable_counts, unavailable_counts,
            green_counts, amber_counts, red_counts, critical_counts, low_util_counts,
            watch_counts, high_watch_counts, critical_watch_counts,
            repeated_breach_counts, deteriorating_counts, provisional_counts,
            max_scores, avg_scores,
        ], axis=1).reset_index()

        # Fill NaN averages with 0 where there are no assessable KPIs
        dept["average_assessable_kpi_risk_score"] = dept["average_assessable_kpi_risk_score"].fillna(0.0)
        dept["maximum_kpi_risk_score"] = dept["maximum_kpi_risk_score"].fillna(0.0)

        # Data availability rate
        dept["department_data_availability_rate"] = (
            dept["assessable_kpi_count"] / dept["kpi_count"]
        ).fillna(0.0)

        return dept

    # ------------------------------------------------------------------
    # Concurrence
    # ------------------------------------------------------------------
    def calculate_concurrence(self, dept_df, kpi_df):
        """Detect concurrent KPI risk within each department-date."""
        # Define concurrence rules as KPI pairs
        concurrence_rules = [
            ("kpi_001", "kpi_002", "Workforce Pressure"),
            ("kpi_003", "kpi_004", "Capacity-Flow Pressure"),
            ("kpi_004", "kpi_005", "Flow-Complaint Pressure"),
            ("kpi_005", "kpi_006", "Complaint-Satisfaction Pressure"),
            ("kpi_001", "kpi_004", "Staffing-Flow Pressure"),
        ]

        concurrence_rows = []
        for _, drow in dept_df.iterrows():
            hid, did, rdate = drow["hospital_id"], drow["department_id"], drow["reporting_date"]
            kpi_subset = kpi_df[
                (kpi_df["hospital_id"] == hid) &
                (kpi_df["department_id"] == did) &
                (kpi_df["reporting_date"] == rdate) &
                (kpi_df["calculation_status"] == "Calculated")
            ]

            active_kpis = set(kpi_subset[kpi_subset["kpi_risk_score_normalized"] > 15]["kpi_id"].tolist())
            matched_rules = []
            score = 0.0
            for a, b, name in concurrence_rules:
                if a in active_kpis and b in active_kpis:
                    matched_rules.append(name)
                    score += 5.0

            concurrence_rows.append({
                "hospital_id": hid,
                "department_id": did,
                "reporting_date": rdate,
                "concurrent_risk_flag": len(matched_rules) > 0,
                "concurrent_kpi_count": len(active_kpis),
                "concurrent_kpi_list": "; ".join(sorted(active_kpis)) if active_kpis else "",
                "concurrence_score": score,
                "concurrence_rule_id": "; ".join(matched_rules) if matched_rules else "",
            })

        conc_df = pd.DataFrame(concurrence_rows)
        dept_df = dept_df.merge(conc_df, on=["hospital_id", "department_id", "reporting_date"], how="left")
        return dept_df

    # ------------------------------------------------------------------
    # Escalation component
    # ------------------------------------------------------------------
    def calculate_escalation(self, dept_df):
        """Score escalation based on repeated severe conditions."""
        dept_df["escalation_score"] = (
            dept_df["repeated_breach_count"] * 3.0 +
            dept_df["deteriorating_kpi_count"] * 2.0 +
            dept_df["critical_kpi_count"] * 5.0
        )
        return dept_df

    # ------------------------------------------------------------------
    # Department risk score
    # ------------------------------------------------------------------
    def compute_department_risk(self, dept_df):
        """Combine max, average, concurrence and escalation into department risk."""
        w = self.agg_weights
        dept_df["department_risk_score_raw"] = (
            w.get("max_kpi_weight", 0.45) * dept_df["maximum_kpi_risk_score"].fillna(0) +
            w.get("average_kpi_weight", 0.30) * dept_df["average_assessable_kpi_risk_score"].fillna(0) +
            w.get("concurrence_weight", 0.15) * dept_df["concurrence_score"].fillna(0) +
            w.get("escalation_weight", 0.10) * dept_df["escalation_score"].fillna(0)
        )

        # Normalise 0-100 using dataset min/max
        raw = dept_df["department_risk_score_raw"]
        rmin, rmax = raw.min(), raw.max()
        rng = rmax - rmin
        if rng > 0:
            dept_df["department_risk_score_normalized"] = ((raw - rmin) / rng * 100.0).round(4)
        else:
            dept_df["department_risk_score_normalized"] = 0.0
        return dept_df

    # ------------------------------------------------------------------
    # Dominant / secondary driver identification
    # ------------------------------------------------------------------
    def identify_drivers(self, dept_df, kpi_df):
        """Find dominant and secondary KPI drivers per department-date."""
        dominant_rows = []
        for _, drow in dept_df.iterrows():
            hid, did, rdate = drow["hospital_id"], drow["department_id"], drow["reporting_date"]
            kpi_subset = kpi_df[
                (kpi_df["hospital_id"] == hid) &
                (kpi_df["department_id"] == did) &
                (kpi_df["reporting_date"] == rdate) &
                (kpi_df["calculation_status"] == "Calculated")
            ].copy()

            if kpi_subset.empty:
                dominant_rows.append({
                    "hospital_id": hid, "department_id": did, "reporting_date": rdate,
                    "dominant_kpi_id": None, "dominant_kpi_name": None,
                    "dominant_kpi_score": None, "dominant_driver_reason": "No assessable KPIs",
                    "dominant_driver_is_provisional": None,
                    "secondary_driver_1": None, "secondary_driver_2": None,
                    "contributing_kpi_count": 0, "contributing_kpi_list": "",
                })
                continue

            # Sort by risk score desc, then deterministic tie-break
            kpi_subset = kpi_subset.sort_values(
                by=["kpi_risk_score_normalized", "confidence_score", "kpi_id"],
                ascending=[False, False, True]
            )

            top = kpi_subset.iloc[0]
            second = kpi_subset.iloc[1] if len(kpi_subset) > 1 else None
            third = kpi_subset.iloc[2] if len(kpi_subset) > 2 else None

            contributing = kpi_subset[kpi_subset["kpi_risk_score_normalized"] > 15]

            dominant_rows.append({
                "hospital_id": hid, "department_id": did, "reporting_date": rdate,
                "dominant_kpi_id": top["kpi_id"],
                "dominant_kpi_name": top.get("kpi_name", top["kpi_id"]),
                "dominant_kpi_score": top["kpi_risk_score_normalized"],
                "dominant_driver_reason": top.get("risk_reason", ""),
                "dominant_driver_is_provisional": top.get("threshold_is_provisional", False),
                "secondary_driver_1": second["kpi_id"] if second is not None else None,
                "secondary_driver_2": third["kpi_id"] if third is not None else None,
                "contributing_kpi_count": len(contributing),
                "contributing_kpi_list": "; ".join(contributing["kpi_id"].tolist()),
            })

        dom_df = pd.DataFrame(dominant_rows)
        dept_df = dept_df.merge(
            dom_df, on=["hospital_id", "department_id", "reporting_date"], how="left"
        )
        return dept_df

    # ------------------------------------------------------------------
    # Priority tier and urgency
    # ------------------------------------------------------------------
    def assign_department_tier(self, dept_df):
        """Map department normalised score to tier."""

        def _tier(row):
            if row["assessable_kpi_count"] == 0:
                return "Not Assessable"
            s = row["department_risk_score_normalized"]
            if s <= 15:
                return "Stable"
            if s <= 35:
                return "Monitor"
            if s <= 55:
                return "Elevated"
            if s <= 75:
                return "High"
            return "Critical"

        dept_df["department_priority_tier"] = dept_df.apply(_tier, axis=1)
        return dept_df

    def assign_department_urgency(self, dept_df):
        """Assign department urgency based on score and triggers."""

        def _urgency(row):
            if row["assessable_kpi_count"] == 0:
                return "Not Assessable"
            s = row["department_risk_score_normalized"]
            if row["critical_kpi_count"] > 0 or row["critical_watch_count"] > 0:
                return "Immediate Review"
            if row["red_kpi_count"] > 0 or s > 70:
                return "Immediate Review"
            if s > 45 or row["repeated_breach_count"] > 0:
                return "Prompt Review"
            if s > 25 or row["amber_kpi_count"] > 1:
                return "Review Soon"
            return "Routine Monitoring"

        dept_df["urgency_level"] = dept_df.apply(_urgency, axis=1)
        return dept_df

    # ------------------------------------------------------------------
    # Confidence and governance at department level
    # ------------------------------------------------------------------
    def assign_department_confidence(self, dept_df, kpi_df):
        """Derive department confidence from KPI confidences."""
        conf_map = {"High": 3, "Moderate": 2, "Low": 1, "Insufficient Evidence": 0}
        inv_map = {3: "High", 2: "Moderate", 1: "Low", 0: "Insufficient Evidence"}

        dept_conf = []
        for _, drow in dept_df.iterrows():
            hid, did, rdate = drow["hospital_id"], drow["department_id"], drow["reporting_date"]
            kpi_subset = kpi_df[
                (kpi_df["hospital_id"] == hid) &
                (kpi_df["department_id"] == did) &
                (kpi_df["reporting_date"] == rdate) &
                (kpi_df["calculation_status"] == "Calculated")
            ]
            if kpi_subset.empty:
                dept_conf.append("Insufficient Evidence")
                continue
            scores = kpi_subset["confidence_level"].map(conf_map)
            min_score = scores.min()
            dept_conf.append(inv_map.get(min_score, "Low"))

        dept_df["confidence_level"] = dept_conf
        return dept_df

    def assign_department_governance(self, dept_df, kpi_df):
        """Propagate provisional flags to department level with materiality-aware refinement."""
        contains_provisional = []
        prov_risk_flags = []
        prov_drivers = []
        gov_warnings = []
        prov_contributions = []
        prov_materialities = []

        for _, drow in dept_df.iterrows():
            hid, did, rdate = drow["hospital_id"], drow["department_id"], drow["reporting_date"]
            kpi_subset = kpi_df[
                (kpi_df["hospital_id"] == hid) &
                (kpi_df["department_id"] == did) &
                (kpi_df["reporting_date"] == rdate)
            ]

            # All provisional KPIs present (assessable or not)
            all_prov = kpi_subset[kpi_subset["threshold_is_provisional"] == True]
            has_any_provisional = len(all_prov) > 0
            contains_provisional.append(has_any_provisional)
            prov_drivers.append("; ".join(all_prov["kpi_id"].unique().tolist()))

            # Assessable provisional KPIs and their contribution
            assessable_prov = kpi_subset[
                (kpi_subset["threshold_is_provisional"] == True) &
                (kpi_subset["calculation_status"] == "Calculated")
            ]
            prov_score_sum = assessable_prov["kpi_risk_score_normalized"].sum() if not assessable_prov.empty else 0.0
            prov_contributions.append(round(prov_score_sum, 4))

            # Dominant driver provisional status already identified in identify_drivers
            dominant_is_prov = drow.get("dominant_driver_is_provisional", False)

            # Materiality classification
            if assessable_prov.empty or prov_score_sum <= 0:
                materiality = "None"
            elif dominant_is_prov:
                materiality = "Dominant"
            elif prov_score_sum < self.provisional_minor_threshold:
                materiality = "Minor"
            elif prov_score_sum >= self.provisional_materiality_threshold:
                materiality = "Material"
            else:
                # Between minor and material thresholds: classify as Minor unless
                # a provisional KPI is in the contributing list with score > 15
                contributing_list = drow.get("contributing_kpi_list", "")
                contributing_ids = [k.strip() for k in str(contributing_list).split(";") if k.strip()]
                prov_contributing = assessable_prov[assessable_prov["kpi_id"].isin(contributing_ids)]
                if not prov_contributing.empty and (prov_contributing["kpi_risk_score_normalized"] > 15).any():
                    materiality = "Material"
                else:
                    materiality = "Minor"

            prov_materialities.append(materiality)

            # Refined provisional_risk_flag: only Material or Dominant contributions
            risk_flag = materiality in ("Material", "Dominant")
            prov_risk_flags.append(risk_flag)

            warnings = []
            if has_any_provisional:
                warnings.append("Department contains provisional threshold KPIs")
            if materiality == "Material":
                warnings.append("Provisional KPI materially affects department risk")
            if materiality == "Dominant":
                warnings.append("Provisional KPI is dominant risk driver")
            if drow.get("review_due_status") in ["DUE_SOON", "OVERDUE"]:
                warnings.append("Review due soon or overdue")
            gov_warnings.append("; ".join(warnings) if warnings else "")

        dept_df["contains_provisional_kpi"] = contains_provisional
        dept_df["provisional_risk_flag"] = prov_risk_flags
        dept_df["provisional_risk_contribution"] = prov_contributions
        dept_df["provisional_contribution_materiality"] = prov_materialities
        dept_df["provisional_driver_list"] = prov_drivers
        dept_df["governance_warning"] = gov_warnings
        return dept_df

    # ------------------------------------------------------------------
    # Data availability status
    # ------------------------------------------------------------------
    def assign_data_availability_status(self, dept_df):
        """Categorise data availability per department-date."""
        min_required = 4  # configurable minimum

        def _status(row):
            rate = row["department_data_availability_rate"]
            count = row["assessable_kpi_count"]
            if rate >= 1.0:
                return "Complete"
            if count >= min_required:
                return "Sufficient"
            if count >= 2:
                return "Limited"
            return "Insufficient"

        dept_df["data_availability_status"] = dept_df.apply(_status, axis=1)
        dept_df["minimum_assessable_kpi_requirement"] = min_required
        return dept_df

    # ------------------------------------------------------------------
    # Evidence pack
    # ------------------------------------------------------------------
    def build_evidence(self, dept_df):
        dept_df["department_risk_record_id"] = [f"DRS-{uuid.uuid4().hex[:12].upper()}" for _ in range(len(dept_df))]
        dept_df["evidence_pack_id"] = [f"DEP-EP-{uuid.uuid4().hex[:12].upper()}" for _ in range(len(dept_df))]
        dept_df["engine_run_id"] = self.engine_run_id
        dept_df["processed_at"] = self.processed_at
        return dept_df

    # ------------------------------------------------------------------
    # Ranking
    # ------------------------------------------------------------------
    def rank_departments(self, dept_df):
        """Deterministic ranking within each hospital-date."""
        tier_order = {"Critical": 5, "High": 4, "Elevated": 3, "Monitor": 2, "Stable": 1, "Not Assessable": 0}
        urgency_order = {"Immediate Review": 4, "Prompt Review": 3, "Review Soon": 2, "Routine Monitoring": 1, "Not Assessable": 0}

        dept_df["_tier_rank"] = dept_df["department_priority_tier"].map(tier_order)
        dept_df["_urgency_rank"] = dept_df["urgency_level"].map(urgency_order)

        # Sort within each hospital-date
        dept_df = dept_df.sort_values(
            by=["hospital_id", "reporting_date", "_tier_rank", "_urgency_rank",
                "department_risk_score_normalized", "department_id"],
            ascending=[True, True, False, False, False, True]
        )

        dept_df["rank_within_hospital"] = dept_df.groupby(["hospital_id", "reporting_date"]).cumcount() + 1
        dept_df.drop(columns=["_tier_rank", "_urgency_rank"], inplace=True, errors="ignore")
        return dept_df

    # ------------------------------------------------------------------
    # Run pipeline
    # ------------------------------------------------------------------
    def run(self, kpi_df):
        self.load_configs()
        dept_df = self.aggregate(kpi_df)
        dept_df = self.calculate_concurrence(dept_df, kpi_df)
        dept_df = self.calculate_escalation(dept_df)
        dept_df = self.compute_department_risk(dept_df)
        dept_df = self.identify_drivers(dept_df, kpi_df)
        dept_df = self.assign_department_tier(dept_df)
        dept_df = self.assign_department_urgency(dept_df)
        dept_df = self.assign_department_confidence(dept_df, kpi_df)
        dept_df = self.assign_department_governance(dept_df, kpi_df)
        dept_df = self.assign_data_availability_status(dept_df)
        dept_df = self.build_evidence(dept_df)
        dept_df = self.rank_departments(dept_df)
        return dept_df

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------
    def to_department_risk_dataframe(self, dept_df):
        cols = [
            "department_risk_record_id", "hospital_id", "department_id", "reporting_date",
            "assessable_kpi_count", "unavailable_kpi_count", "green_kpi_count", "amber_kpi_count",
            "red_kpi_count", "critical_kpi_count", "low_utilisation_count", "watch_condition_count",
            "repeated_breach_count", "deteriorating_kpi_count", "provisional_kpi_count",
            "maximum_kpi_risk_score", "average_assessable_kpi_risk_score",
            "concurrent_risk_flag", "concurrent_kpi_count", "concurrent_kpi_list",
            "concurrence_score", "concurrence_rule_id", "escalation_score", "department_risk_score_raw",
            "department_risk_score_normalized", "department_priority_tier", "urgency_level",
            "dominant_kpi_id", "dominant_kpi_name", "dominant_kpi_score", "dominant_driver_reason",
            "dominant_driver_is_provisional", "secondary_driver_1", "secondary_driver_2",
            "contributing_kpi_count", "contributing_kpi_list", "confidence_level",
            "contains_provisional_kpi", "provisional_risk_flag",
            "provisional_risk_contribution", "provisional_contribution_materiality",
            "governance_warning", "evidence_pack_id",
            "data_availability_status", "department_data_availability_rate",
            "minimum_assessable_kpi_requirement", "engine_run_id", "processed_at",
        ]
        available = [c for c in cols if c in dept_df.columns]
        return dept_df[available].copy()

    def to_ranking_dataframe(self, dept_df):
        cols = [
            "reporting_date", "hospital_id", "department_id",
            "department_risk_score_normalized", "department_priority_tier", "urgency_level",
            "rank_within_hospital", "dominant_kpi_id", "dominant_kpi_name",
            "dominant_driver_reason", "secondary_driver_1", "secondary_driver_2",
            "assessable_kpi_count", "provisional_risk_flag", "confidence_level",
            "evidence_pack_id", "engine_run_id", "processed_at",
        ]
        available = [c for c in cols if c in dept_df.columns]
        return dept_df[available].copy()

    def to_driver_dataframe(self, dept_df):
        cols = [
            "hospital_id", "department_id", "reporting_date",
            "dominant_kpi_id", "dominant_kpi_name", "dominant_kpi_score",
            "dominant_driver_reason", "dominant_driver_is_provisional",
            "secondary_driver_1", "secondary_driver_2",
            "contributing_kpi_count", "contributing_kpi_list",
            "engine_run_id", "processed_at",
        ]
        available = [c for c in cols if c in dept_df.columns]
        return dept_df[available].copy()

    def to_concurrence_dataframe(self, dept_df):
        cols = [
            "hospital_id", "department_id", "reporting_date",
            "concurrent_risk_flag", "concurrent_kpi_count", "concurrent_kpi_list",
            "concurrence_score", "concurrence_rule_id",
            "engine_run_id", "processed_at",
        ]
        available = [c for c in cols if c in dept_df.columns]
        return dept_df[available].copy()

    def to_governance_dataframe(self, dept_df):
        cols = [
            "hospital_id", "department_id", "reporting_date",
            "contains_provisional_kpi", "provisional_risk_flag",
            "dominant_driver_is_provisional", "provisional_risk_contribution",
            "provisional_contribution_materiality", "provisional_kpi_count",
            "provisional_driver_list", "governance_warning",
            "engine_run_id", "processed_at",
        ]
        available = [c for c in cols if c in dept_df.columns]
        return dept_df[available].copy()
