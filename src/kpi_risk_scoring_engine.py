"""KPI Risk Scoring Engine for Step 2B-3.

Transforms Step 2B-2 watch, breach, trend and governance outputs into
KPI-level risk scores, priority tiers, urgency levels and confidence ratings.
"""

import os
import uuid
from datetime import datetime

import pandas as pd
import numpy as np


class KPIRiskScoringEngine:
    """Calculate risk scores for every hospital-department-date-KPI record."""

    def __init__(self, config_dir=None, inputs_dir=None, engine_run_id=None):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        self.config_dir = config_dir or os.path.join(project_root, "config")
        self.inputs_dir = inputs_dir or os.path.join(project_root, "data/analytical")
        self.engine_run_id = engine_run_id or f"RISKSCORE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.processed_at = datetime.now().isoformat()
        self.configs = {}
        self.issues = []

    # ------------------------------------------------------------------
    # Config loaders
    # ------------------------------------------------------------------
    def _load_config(self, filename):
        path = os.path.join(self.config_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing config: {path}")
        return pd.read_csv(path)

    def load_configs(self):
        """Load all governed configuration files into memory."""
        self.configs["weights"] = self._load_config("kpi_risk_weight_config.csv")
        self.configs["severity"] = self._load_config("risk_severity_weight_config.csv")
        self.configs["persistence"] = self._load_config("risk_persistence_weight_config.csv")
        self.configs["trend"] = self._load_config("risk_trend_weight_config.csv")
        self.configs["confidence"] = self._load_config("risk_confidence_config.csv")
        self.configs["governance"] = self._load_config("risk_governance_adjustment_config.csv")

        # Build quick lookup dicts
        self.severity_map = self._build_map(self.configs["severity"], "parameter_name", "parameter_value")
        self.persistence_map = self._build_map(self.configs["persistence"], "parameter_name", "parameter_value")
        self.trend_map = self._build_map(self.configs["trend"], "parameter_name", "parameter_value")
        self.gov_map = self._build_map(self.configs["governance"], "parameter_name", "parameter_value")
        self.conf_map = self._build_map(self.configs["confidence"], "parameter_name", "parameter_value")

    @staticmethod
    def _build_map(df, key_col, val_col):
        out = {}
        for _, row in df.iterrows():
            try:
                out[row[key_col]] = float(row[val_col])
            except (ValueError, TypeError):
                out[row[key_col]] = row[val_col]
        return out

    # ------------------------------------------------------------------
    # Input loader
    # ------------------------------------------------------------------
    def load_inputs(self):
        """Load Step 2B-2 authoritative outputs.

        The watch-conditions file already contains breach, trend, persistence,
        governance, evidence and lineage fields, so it serves as the primary
        input.  We merge classification for any supplementary boundary data.
        """
        watch_path = os.path.join(self.inputs_dir, "analytical_kpi_watch_conditions.csv")
        cls_path = os.path.join(self.inputs_dir, "analytical_kpi_threshold_classification_daily.csv")

        if not os.path.exists(watch_path):
            raise FileNotFoundError(f"Missing authoritative input: {watch_path}")

        df = pd.read_csv(watch_path)

        # Merge classification for threshold_state consistency and boundaries
        if os.path.exists(cls_path):
            cls = pd.read_csv(cls_path)
            keep = [
                "integration_record_id", "threshold_state", "calculation_status",
                "lower_red_boundary", "lower_amber_boundary", "green_lower_boundary",
                "green_upper_boundary", "upper_amber_boundary", "upper_red_boundary",
            ]
            cls = cls[[c for c in keep if c in cls.columns]].drop_duplicates("integration_record_id")
            df = df.merge(cls, on="integration_record_id", how="left", suffixes=("", "_cls"))
            # Prefer classification threshold_state if watch lacks it
            if "threshold_state_cls" in df.columns:
                df["threshold_state"] = df["threshold_state"].fillna(df["threshold_state_cls"])
                df.drop(columns=["threshold_state_cls"], inplace=True)

        # Override threshold_is_provisional from authoritative active config
        # (Step 2B-2 watch output may contain incorrect values)
        active_config_path = os.path.join(self.inputs_dir, "..", "..", "config", "kpi_threshold_config.csv")
        if os.path.exists(active_config_path):
            active_cfg = pd.read_csv(active_config_path)
            if "kpi_id" in active_cfg.columns and "threshold_is_provisional" in active_cfg.columns:
                prov_map = dict(zip(active_cfg["kpi_id"], active_cfg["threshold_is_provisional"]))
                df["threshold_is_provisional"] = df["kpi_id"].map(prov_map)

        return df

    # ------------------------------------------------------------------
    # Component scoring
    # ------------------------------------------------------------------
    def calculate_threshold_component(self, df):
        """Score based on threshold_state."""
        sm = self.severity_map

        def _score(state):
            if pd.isna(state):
                return np.nan
            state = str(state).replace(" ", "_")
            mapping = {
                "Green": sm.get("Green", 0.0),
                "Normal_Operating_Band": sm.get("Normal_Operating_Band", 0.0),
                "Amber": sm.get("Amber", 25.0),
                "Upper_Amber": sm.get("Upper_Amber", 25.0),
                "Lower_Amber": sm.get("Lower_Amber", 20.0),
                "Red": sm.get("Red", 60.0),
                "Critical_Capacity_Pressure": sm.get("Critical_Capacity_Pressure", 80.0),
                "Low_Utilisation": sm.get("Low_Utilisation", 15.0),
                "Unavailable": np.nan,
            }
            return mapping.get(state, 0.0)

        df["threshold_component_score"] = df["threshold_state"].apply(_score)
        return df

    def calculate_breach_component(self, df):
        """Score based on breach_type."""
        sm = self.severity_map

        def _score(bt):
            if pd.isna(bt):
                return np.nan
            bt = str(bt).replace(" ", "_")
            mapping = {
                "No_Breach": sm.get("No_Breach", 0.0),
                "Provisional_Breach": sm.get("Provisional_Breach", 50.0),
                "Unavailable": np.nan,
            }
            return mapping.get(bt, 0.0)

        df["breach_component_score"] = df["breach_type"].apply(_score)
        return df

    def calculate_watch_component(self, df):
        """Score based on watch_severity."""
        sm = self.severity_map

        def _score(sev):
            if pd.isna(sev):
                return 0.0
            sev = str(sev).replace(" ", "_")
            mapping = {
                "None": sm.get("None", 0.0),
                "Informational": sm.get("Informational", 5.0),
                "Low": sm.get("Low", 10.0),
                "Moderate": sm.get("Moderate", 20.0),
                "High": sm.get("High", 40.0),
                "Critical": sm.get("Critical", 70.0),
            }
            return mapping.get(sev, 0.0)

        df["watch_component_score"] = df["watch_severity"].apply(_score)
        return df

    def calculate_persistence_component(self, df):
        """Score based on persistence flags and counts."""
        pm = self.persistence_map
        base = np.where(df["persistence_count"] >= 1, pm.get("persistence_count_1plus", 5.0), 0.0)
        amber_add = np.where(df["repeated_amber_flag"] == True, pm.get("repeated_amber_flag", 10.0), 0.0)
        red_add = np.where(df["repeated_red_flag"] == True, pm.get("repeated_red_flag", 20.0), 0.0)
        ccp_add = np.where(
            (df["threshold_state"] == "Critical Capacity Pressure") & (df["persistence_count"] >= 1),
            pm.get("persistent_critical_capacity", 15.0), 0.0
        )
        df["persistence_component_score"] = base + amber_add + red_add + ccp_add
        return df

    def calculate_trend_component(self, df):
        """Score based on operational_trend_interpretation."""
        tm = self.trend_map

        def _score(trend):
            if pd.isna(trend):
                return 0.0
            trend = str(trend).replace(" ", "_")
            mapping = {
                "Improving": tm.get("Improving", -5.0),
                "Stable": tm.get("Stable", 0.0),
                "Deteriorating": tm.get("Deteriorating", 15.0),
                "Volatile": tm.get("Volatile", 10.0),
                "Insufficient_Evidence": tm.get("Insufficient_Evidence", 0.0),
            }
            return mapping.get(trend, 0.0)

        df["trend_component_score"] = df["operational_trend_interpretation"].apply(_score)
        return df

    def calculate_sustained_movement_component(self, df):
        df["sustained_movement_component_score"] = np.where(df["sustained_movement_flag"] == True, 10.0, 0.0)
        return df

    def calculate_statistical_signal_component(self, df):
        df["statistical_signal_component_score"] = np.where(df["statistical_signal_flag"] == True, 10.0, 0.0)
        return df

    # ------------------------------------------------------------------
    # Confidence
    # ------------------------------------------------------------------
    def assign_confidence(self, df):
        """Assign confidence level based on data quality and evidence completeness."""

        def _level(row):
            if row["calculation_status"] != "Calculated":
                return "Insufficient Evidence"

            has_evidence = pd.notna(row.get("evidence_record_id"))
            has_lineage = pd.notna(row.get("lineage_record_id"))

            # Map string trend_confidence to numeric
            tc_raw = row.get("trend_confidence")
            tc_map = {"High": 0.95, "Medium": 0.70, "Low": 0.40}
            tc = tc_map.get(tc_raw, 0.0) if pd.notna(tc_raw) else 0.0

            if row["threshold_is_provisional"]:
                if tc >= 0.7 and has_evidence:
                    return "Moderate"
                return "Low"

            if tc >= 0.7 and has_evidence and has_lineage:
                return "High"
            if has_evidence:
                return "Moderate"
            return "Low"

        df["confidence_level"] = df.apply(_level, axis=1)

        # numeric confidence score for sorting
        mapping = {"High": 0.95, "Moderate": 0.70, "Low": 0.40, "Insufficient Evidence": 0.0}
        df["confidence_score"] = df["confidence_level"].map(mapping)
        return df

    # ------------------------------------------------------------------
    # Governance adjustment
    # ------------------------------------------------------------------
    def apply_governance_adjustment(self, df):
        """Apply provisional and review-due adjustments."""
        gm = self.gov_map
        prov_mult = float(gm.get("provisional_multiplier", 0.9))
        due_mult = float(gm.get("review_due_soon_adjustment", 0.95))

        df["governance_adjustment"] = 1.0
        prov_mask = df["threshold_is_provisional"] == True
        df.loc[prov_mask, "governance_adjustment"] *= prov_mult

        due_mask = df["review_due_status"].isin(["DUE_SOON", "OVERDUE"])
        df.loc[due_mask, "governance_adjustment"] *= due_mult
        return df

    # ------------------------------------------------------------------
    # Raw and normalised scores
    # ------------------------------------------------------------------
    def compute_raw_score(self, df):
        """Sum all component scores for assessable records."""
        comp_cols = [
            "threshold_component_score", "breach_component_score", "watch_component_score",
            "persistence_component_score", "trend_component_score",
            "sustained_movement_component_score", "statistical_signal_component_score",
        ]

        # For unavailable records, components are NaN -> raw stays NaN
        df["kpi_risk_score_raw"] = df[comp_cols].sum(axis=1, skipna=False)

        # Apply confidence and governance adjustments
        conf_mult = df["confidence_level"].map({
            "High": float(self.conf_map.get("high_adjustment_multiplier", 1.0)),
            "Moderate": float(self.conf_map.get("moderate_adjustment_multiplier", 0.95)),
            "Low": float(self.conf_map.get("low_adjustment_multiplier", 0.85)),
            "Insufficient Evidence": float(self.conf_map.get("insufficient_adjustment_multiplier", 0.7)),
        })
        df["confidence_adjustment"] = conf_mult
        df["kpi_risk_score_raw"] = df["kpi_risk_score_raw"] * df["confidence_adjustment"] * df["governance_adjustment"]
        return df

    def normalize_scores(self, df):
        """Normalise assessable raw scores to 0-100."""
        assessable = df["calculation_status"] == "Calculated"
        raw_vals = df.loc[assessable, "kpi_risk_score_raw"]

        if len(raw_vals) > 0 and raw_vals.notna().any():
            rmin = raw_vals.min()
            rmax = raw_vals.max()
            rng = rmax - rmin
            if rng > 0:
                df.loc[assessable, "kpi_risk_score_normalized"] = ((raw_vals - rmin) / rng * 100.0).round(4)
            else:
                df.loc[assessable, "kpi_risk_score_normalized"] = 0.0
        else:
            df["kpi_risk_score_normalized"] = np.nan

        # Unavailable / not-assessed
        df.loc[~assessable, "kpi_risk_score_normalized"] = np.nan
        return df

    # ------------------------------------------------------------------
    # Priority tier and urgency
    # ------------------------------------------------------------------
    def assign_priority_tier(self, df):
        """Map normalised score to priority tier."""

        def _tier(row):
            if row["calculation_status"] != "Calculated" or pd.isna(row["kpi_risk_score_normalized"]):
                return "Not Assessable"
            s = row["kpi_risk_score_normalized"]
            if s <= 15:
                return "No Current Risk"
            if s <= 35:
                return "Monitor"
            if s <= 55:
                return "Attention Required"
            if s <= 75:
                return "High Priority"
            return "Critical Priority"

        df["kpi_priority_tier"] = df.apply(_tier, axis=1)
        return df

    def assign_urgency(self, df):
        """Assign urgency based on score, triggers and state."""

        def _urgency(row):
            if row["calculation_status"] != "Calculated" or pd.isna(row["kpi_risk_score_normalized"]):
                return "Not Assessable"

            s = row["kpi_risk_score_normalized"]
            state = str(row.get("threshold_state", ""))
            watch = str(row.get("watch_severity", ""))

            # Immediate triggers
            if state == "Critical Capacity Pressure" or watch == "Critical":
                return "Immediate Review"
            if row.get("breach_type") == "Provisional Breach" and state == "Red":
                return "Immediate Review"

            if s > 70:
                return "Immediate Review"
            if s > 45 or row.get("breach_type") == "Provisional Breach":
                return "Prompt Review"
            if s > 25 or row.get("repeated_amber_flag") == True:
                return "Review Soon"
            return "Routine Monitoring"

        df["urgency_level"] = df.apply(_urgency, axis=1)
        return df

    # ------------------------------------------------------------------
    # Evidence / lineage enrichment
    # ------------------------------------------------------------------
    def build_evidence(self, df):
        """Generate evidence_pack_id and risk_record_id."""
        df["kpi_risk_record_id"] = [f"KRS-{uuid.uuid4().hex[:12].upper()}" for _ in range(len(df))]
        df["evidence_pack_id"] = [f"EP-{uuid.uuid4().hex[:12].upper()}" for _ in range(len(df))]
        df["engine_run_id"] = self.engine_run_id
        df["processed_at"] = self.processed_at

        # Risk reason
        def _reason(row):
            parts = []
            if row["threshold_state"] not in ["Green", "Normal Operating Band", np.nan, "Unavailable"]:
                parts.append(f"threshold={row['threshold_state']}")
            if row.get("breach_type") not in ["No Breach", np.nan, "Unavailable"]:
                parts.append(f"breach={row['breach_type']}")
            if pd.notna(row.get("watch_severity")) and row["watch_severity"] not in ["None", np.nan]:
                parts.append(f"watch={row['watch_severity']}")
            if row.get("operational_trend_interpretation") == "Deteriorating":
                parts.append("trend=deteriorating")
            if not parts:
                return "No current adverse indicators"
            return "; ".join(parts)

        df["risk_reason"] = df.apply(_reason, axis=1)
        return df

    # ------------------------------------------------------------------
    # Run pipeline
    # ------------------------------------------------------------------
    def run(self):
        self.load_configs()
        df = self.load_inputs()
        df = self.calculate_threshold_component(df)
        df = self.calculate_breach_component(df)
        df = self.calculate_watch_component(df)
        df = self.calculate_persistence_component(df)
        df = self.calculate_trend_component(df)
        df = self.calculate_sustained_movement_component(df)
        df = self.calculate_statistical_signal_component(df)
        df = self.assign_confidence(df)
        df = self.apply_governance_adjustment(df)
        df = self.compute_raw_score(df)
        df = self.normalize_scores(df)
        df = self.assign_priority_tier(df)
        df = self.assign_urgency(df)
        df = self.build_evidence(df)
        return df

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------
    def to_kpi_risk_dataframe(self, df):
        """Return the standard KPI risk score DataFrame."""
        core = [
            "kpi_risk_record_id", "hospital_id", "department_id", "reporting_date",
            "kpi_id", "kpi_name", "kpi_value", "calculation_status", "threshold_state", "breach_type",
            "breach_flag", "watch_condition_type", "watch_severity", "persistence_count",
            "repeated_amber_flag", "repeated_red_flag",
            "operational_trend_interpretation", "trend_confidence", "sustained_movement_flag",
            "statistical_signal_flag", "threshold_component_score", "breach_component_score",
            "watch_component_score", "persistence_component_score", "trend_component_score",
            "sustained_movement_component_score", "statistical_signal_component_score",
            "confidence_adjustment", "governance_adjustment", "kpi_risk_score_raw",
            "kpi_risk_score_normalized", "kpi_priority_tier", "urgency_level", "risk_reason",
            "confidence_level", "confidence_score", "approval_status",
            "threshold_is_provisional", "operational_use_status", "governance_warning",
            "required_review_date", "review_due_status", "evidence_record_id",
            "lineage_record_id", "evidence_pack_id", "engine_run_id", "processed_at",
        ]
        available = [c for c in core if c in df.columns]
        return df[available].copy()

    def to_component_dataframe(self, df):
        """Return component-level breakdown for audit."""
        cols = [
            "kpi_risk_record_id", "hospital_id", "department_id", "reporting_date",
            "kpi_id", "kpi_name", "threshold_component_score", "breach_component_score",
            "watch_component_score", "persistence_component_score", "trend_component_score",
            "sustained_movement_component_score", "statistical_signal_component_score",
            "confidence_adjustment", "governance_adjustment", "kpi_risk_score_raw",
            "kpi_risk_score_normalized", "engine_run_id", "processed_at",
        ]
        available = [c for c in cols if c in df.columns]
        return df[available].copy()
