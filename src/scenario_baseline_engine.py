"""Scenario baseline engine.

Constructs immutable baselines from observed analytical data for Phase 2C-2C.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.scenario_models import BaselineStatus, ScenarioBaseline
from src.scenario_config_loader import ScenarioConfigLoader


def _to_float(val: Any) -> Optional[float]:
    """Safely convert to float, returning None for invalid values."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        f = float(val)
        if pd.isna(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def _parse_date(val: Any) -> Optional[pd.Timestamp]:
    """Safely parse date string."""
    if val is None or str(val).strip() == "":
        return None
    try:
        return pd.to_datetime(str(val))
    except (ValueError, TypeError):
        return None


class ScenarioBaselineEngine:
    """Builds baselines from observed analytical data."""

    SUPPORTED_QUANTITATIVE_KPIS = {"kpi_001", "kpi_002", "kpi_004"}
    WORKFORCE_KPIS = {"kpi_001", "kpi_002"}
    PATIENT_FLOW_KPIS = {"kpi_004", "kpi_003", "kpi_005", "kpi_006"}

    def __init__(self, loader: ScenarioConfigLoader, aggregation_method: str = "episode-period mean"):
        self.loader = loader
        self.aggregation_method = aggregation_method
        self._workforce_df: Optional[pd.DataFrame] = None
        self._six_kpi_df: Optional[pd.DataFrame] = None
        self._patient_flow_df: Optional[pd.DataFrame] = None

    def _load_data(self) -> None:
        if self._workforce_df is None:
            self._workforce_df = self.loader.load_workforce_kpi_daily()
        if self._six_kpi_df is None:
            self._six_kpi_df = self.loader.load_six_kpi_daily()
        if self._patient_flow_df is None:
            self._patient_flow_df = self.loader.load_patient_flow_kpi_daily()

    def build_baseline(self, package: Dict[str, Any], episode: Dict[str, Any]) -> ScenarioBaseline:
        """Build a single baseline for a package-episode pair."""
        self._load_data()

        package_id = package.get("approval_package_id", "")
        episode_id = episode.get("episode_id", "")
        template_id = package.get("scenario_template_id", "")
        hospital_id = episode.get("hospital_id", "")
        department_id = episode.get("department_id", "")
        episode_start = str(episode.get("episode_start_date", ""))
        episode_end = str(episode.get("episode_end_date", ""))
        dominant_kpi_id = episode.get("dominant_kpi_id", "")
        dominant_kpi_name = episode.get("dominant_kpi_name", "")

        reference_date = episode_end if episode_end else episode_start

        # Determine baseline status and values
        baseline_status, baseline_values, observation_count, completeness, source_files, source_records = (
            self._compute_baseline_values(
                hospital_id, department_id, episode_start, episode_end, dominant_kpi_id
            )
        )

        baseline_id = self._make_baseline_id(
            package_id, episode_id, template_id, episode_start, episode_end
        )

        # Extract provisional and contradiction metadata from source data
        provisional_flag, contradiction_severity, confidence = self._extract_metadata(
            hospital_id, department_id, episode_start, episode_end, dominant_kpi_id
        )

        # Build required baseline fields from supporting KPIs
        req_staff = baseline_values.get("baseline_required_staff")
        avail_staff = baseline_values.get("baseline_available_staff")
        coverage = baseline_values.get("baseline_staffing_coverage_pct")
        absenteeism = baseline_values.get("baseline_absenteeism_rate")
        avg_wait = baseline_values.get("baseline_avg_wait_min")
        arrivals = baseline_values.get("baseline_arrivals")
        capacity = baseline_values.get("baseline_service_capacity")

        kpi_val = baseline_values.get("baseline_kpi_value")
        kpi_unit = baseline_values.get("baseline_kpi_unit", "Percent")

        return ScenarioBaseline(
            baseline_id=baseline_id,
            approval_package_id=package_id,
            episode_id=episode_id,
            scenario_template_id=template_id,
            hospital_id=hospital_id,
            department_id=department_id,
            episode_start_date=episode_start,
            episode_end_date=episode_end,
            dominant_kpi_id=dominant_kpi_id,
            dominant_kpi_name=dominant_kpi_name,
            baseline_kpi_value=kpi_val,
            baseline_kpi_unit=kpi_unit,
            supporting_kpi_values=baseline_values.get("supporting_kpi_values", {}),
            baseline_required_staff=req_staff,
            baseline_available_staff=avail_staff,
            baseline_staffing_coverage_pct=coverage,
            baseline_absenteeism_rate=absenteeism,
            baseline_avg_wait_min=avg_wait,
            baseline_arrivals=arrivals,
            baseline_service_capacity=capacity,
            source_file_list=sorted(list(set(source_files))),
            source_record_id_list=sorted(list(set(source_records))),
            baseline_observation_count=observation_count,
            baseline_data_completeness=completeness,
            baseline_confidence=confidence,
            baseline_provisional_flag=provisional_flag,
            baseline_contradiction_severity=contradiction_severity,
            baseline_status=baseline_status,
            baseline_reference_date=reference_date,
            baseline_window_start=episode_start,
            baseline_window_end=episode_end,
            baseline_aggregation_method=self.aggregation_method,
        )

    def _compute_baseline_values(
        self,
        hospital_id: str,
        department_id: str,
        start_date: str,
        end_date: str,
        dominant_kpi_id: str,
    ) -> Tuple[BaselineStatus, Dict[str, Any], int, float, List[str], List[str]]:
        """Compute baseline values from observed data."""
        start = _parse_date(start_date)
        end = _parse_date(end_date)
        if start is None and end is None:
            return BaselineStatus.UNAVAILABLE, {}, 0, 0.0, [], []
        if start is None:
            start = end
        if end is None:
            end = start

        baseline_values: Dict[str, Any] = {}
        source_files: List[str] = []
        source_records: List[str] = []
        observation_count = 0
        valid_count = 0

        if dominant_kpi_id in self.WORKFORCE_KPIS:
            # Use workforce KPI daily and six_kpi_daily as sources
            kpi_val, obs_count, val_count, files, records = self._aggregate_workforce_kpi(
                hospital_id, department_id, start, end, dominant_kpi_id
            )
            observation_count += obs_count
            valid_count += val_count
            source_files.extend(files)
            source_records.extend(records)
            baseline_values["baseline_kpi_value"] = kpi_val
            baseline_values["baseline_kpi_unit"] = "Percent"

            # Extract staffing components from kpi_001 if available
            if dominant_kpi_id == "kpi_001":
                req, avail, cov, obs, files2, records2 = self._extract_staffing_components(
                    hospital_id, department_id, start, end
                )
                baseline_values["baseline_required_staff"] = req
                baseline_values["baseline_available_staff"] = avail
                baseline_values["baseline_staffing_coverage_pct"] = cov
                observation_count += obs
                source_files.extend(files2)
                source_records.extend(records2)
            elif dominant_kpi_id == "kpi_002":
                abs_val, obs, files2, records2 = self._extract_absenteeism(
                    hospital_id, department_id, start, end
                )
                baseline_values["baseline_absenteeism_rate"] = abs_val
                observation_count += obs
                source_files.extend(files2)
                source_records.extend(records2)

        elif dominant_kpi_id == "kpi_004":
            # Patient flow - try six_kpi_daily first, then patient_flow_kpi_daily
            kpi_val, obs_count, val_count, files, records = self._aggregate_patient_flow_kpi(
                hospital_id, department_id, start, end, dominant_kpi_id
            )
            observation_count += obs_count
            valid_count += val_count
            source_files.extend(files)
            source_records.extend(records)
            baseline_values["baseline_kpi_value"] = kpi_val
            baseline_values["baseline_kpi_unit"] = "Minutes"
            # Wait time, arrivals, capacity - derive from six_kpi_daily numerator/denominator
            baseline_values["baseline_avg_wait_min"] = kpi_val
            # For kpi_004 in six_kpi_daily, numerator_value = total wait minutes, denominator_value = patient count
            if self._six_kpi_df is not None and not self._six_kpi_df.empty:
                mask = (
                    (self._six_kpi_df["hospital_id"] == hospital_id)
                    & (self._six_kpi_df["department_id"] == department_id)
                    & (self._six_kpi_df["kpi_id"] == "kpi_004")
                    & (self._six_kpi_df["reporting_date"] >= start.strftime("%Y-%m-%d"))
                    & (self._six_kpi_df["reporting_date"] <= end.strftime("%Y-%m-%d"))
                    & (self._six_kpi_df["calculation_status"].str.strip() == "Calculated")
                )
                subset = self._six_kpi_df[mask]
                if not subset.empty:
                    num_vals = subset["numerator_value"].apply(_to_float).dropna()
                    den_vals = subset["denominator_value"].apply(_to_float).dropna()
                    if not num_vals.empty and not den_vals.empty:
                        # total_wait = sum(numerator), total_patients = sum(denominator)
                        total_wait = float(num_vals.sum())
                        total_patients = float(den_vals.sum())
                        # arrivals = average daily patients (denominator mean)
                        avg_daily_patients = float(den_vals.mean()) if len(den_vals) > 0 else None
                        # capacity = total_patients / episode_days (approximate throughput)
                        episode_days = max(1, (end - start).days + 1)
                        capacity = total_patients / episode_days if total_patients > 0 else None
                        baseline_values["baseline_arrivals"] = avg_daily_patients
                        baseline_values["baseline_service_capacity"] = capacity
                    else:
                        baseline_values["baseline_arrivals"] = None
                        baseline_values["baseline_service_capacity"] = None
                else:
                    baseline_values["baseline_arrivals"] = None
                    baseline_values["baseline_service_capacity"] = None
            else:
                baseline_values["baseline_arrivals"] = None
                baseline_values["baseline_service_capacity"] = None

        else:
            # Not a supported quantitative KPI
            baseline_values["baseline_kpi_value"] = None
            baseline_values["baseline_kpi_unit"] = ""

        # Determine status
        if observation_count == 0 or baseline_values.get("baseline_kpi_value") is None:
            if dominant_kpi_id in self.SUPPORTED_QUANTITATIVE_KPIS:
                status = BaselineStatus.UNAVAILABLE
            else:
                status = BaselineStatus.BLOCKED
        elif valid_count == 0:
            status = BaselineStatus.PARTIAL
        elif valid_count < observation_count:
            status = BaselineStatus.AVAILABLE_WITH_CONDITIONS
        else:
            status = BaselineStatus.AVAILABLE

        completeness = (valid_count / observation_count * 100) if observation_count > 0 else 0.0
        return status, baseline_values, observation_count, completeness, source_files, source_records

    def _aggregate_workforce_kpi(
        self,
        hospital_id: str,
        department_id: str,
        start: pd.Timestamp,
        end: pd.Timestamp,
        kpi_id: str,
    ) -> Tuple[Optional[float], int, int, List[str], List[str]]:
        """Aggregate workforce KPI from observed data."""
        df = self._workforce_df
        if df is None or df.empty:
            return None, 0, 0, [], []

        mask = (
            (df["hospital_id"] == hospital_id)
            & (df["department_id"] == department_id)
            & (df["kpi_id"] == kpi_id)
            & (df["reporting_date"] >= start.strftime("%Y-%m-%d"))
            & (df["reporting_date"] <= end.strftime("%Y-%m-%d"))
        )
        subset = df[mask]
        if subset.empty:
            return None, 0, 0, [], []

        obs_count = len(subset)
        # Only count records with Calculated status as valid
        valid_mask = subset["calculation_status"].str.strip() == "Calculated"
        valid = subset[valid_mask]
        val_count = len(valid)

        source_files = ["analytical_workforce_kpi_daily.csv"] * obs_count
        source_records = subset["analytical_record_id"].tolist()

        if valid.empty:
            return None, obs_count, 0, source_files, source_records

        values = valid["kpi_value"].apply(_to_float).dropna()
        if values.empty:
            return None, obs_count, 0, source_files, source_records

        if self.aggregation_method == "episode-period mean":
            agg_val = float(values.mean())
        elif self.aggregation_method == "episode-period median":
            agg_val = float(values.median())
        elif self.aggregation_method == "episode-period maximum":
            agg_val = float(values.max())
        elif self.aggregation_method == "latest valid observation":
            agg_val = float(values.iloc[-1])
        else:
            agg_val = float(values.mean())

        return agg_val, obs_count, val_count, source_files, source_records

    def _extract_staffing_components(
        self,
        hospital_id: str,
        department_id: str,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> Tuple[Optional[float], Optional[float], Optional[float], int, List[str], List[str]]:
        """Extract required and available staff from kpi_001 records."""
        df = self._workforce_df
        if df is None or df.empty:
            return None, None, None, 0, [], []

        mask = (
            (df["hospital_id"] == hospital_id)
            & (df["department_id"] == department_id)
            & (df["kpi_id"] == "kpi_001")
            & (df["reporting_date"] >= start.strftime("%Y-%m-%d"))
            & (df["reporting_date"] <= end.strftime("%Y-%m-%d"))
            & (df["calculation_status"].str.strip() == "Calculated")
        )
        subset = df[mask]
        if subset.empty:
            return None, None, None, 0, [], []

        obs_count = len(subset)
        source_files = ["analytical_workforce_kpi_daily.csv"] * obs_count
        source_records = subset["analytical_record_id"].tolist()

        req_vals = subset["denominator_value"].apply(_to_float).dropna()
        avail_vals = subset["numerator_value"].apply(_to_float).dropna()
        kpi_vals = subset["kpi_value"].apply(_to_float).dropna()

        req = float(req_vals.mean()) if not req_vals.empty else None
        avail = float(avail_vals.mean()) if not avail_vals.empty else None
        cov = float(kpi_vals.mean()) if not kpi_vals.empty else None

        return req, avail, cov, obs_count, source_files, source_records

    def _extract_absenteeism(
        self,
        hospital_id: str,
        department_id: str,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> Tuple[Optional[float], int, List[str], List[str]]:
        """Extract absenteeism rate from kpi_002 records."""
        df = self._workforce_df
        if df is None or df.empty:
            return None, 0, [], []

        mask = (
            (df["hospital_id"] == hospital_id)
            & (df["department_id"] == department_id)
            & (df["kpi_id"] == "kpi_002")
            & (df["reporting_date"] >= start.strftime("%Y-%m-%d"))
            & (df["reporting_date"] <= end.strftime("%Y-%m-%d"))
            & (df["calculation_status"].str.strip() == "Calculated")
        )
        subset = df[mask]
        if subset.empty:
            return None, 0, [], []

        obs_count = len(subset)
        source_files = ["analytical_workforce_kpi_daily.csv"] * obs_count
        source_records = subset["analytical_record_id"].tolist()

        vals = subset["kpi_value"].apply(_to_float).dropna()
        if vals.empty:
            return None, obs_count, source_files, source_records

        return float(vals.mean()), obs_count, source_files, source_records

    def _aggregate_patient_flow_kpi(
        self,
        hospital_id: str,
        department_id: str,
        start: pd.Timestamp,
        end: pd.Timestamp,
        kpi_id: str,
    ) -> Tuple[Optional[float], int, int, List[str], List[str]]:
        """Aggregate patient flow KPI from observed data."""
        # Try six_kpi_daily first
        df = self._six_kpi_df
        if df is not None and not df.empty:
            mask = (
                (df["hospital_id"] == hospital_id)
                & (df["department_id"] == department_id)
                & (df["kpi_id"] == kpi_id)
                & (df["reporting_date"] >= start.strftime("%Y-%m-%d"))
                & (df["reporting_date"] <= end.strftime("%Y-%m-%d"))
            )
            subset = df[mask]
            if not subset.empty:
                obs_count = len(subset)
                valid_mask = subset["calculation_status"].str.strip() == "Calculated"
                valid = subset[valid_mask]
                val_count = len(valid)
                source_files = ["analytical_six_kpi_daily.csv"] * obs_count
                source_records = subset["integration_record_id"].tolist()
                if not valid.empty:
                    vals = valid["kpi_value"].apply(_to_float).dropna()
                    if not vals.empty:
                        if self.aggregation_method == "episode-period mean":
                            agg_val = float(vals.mean())
                        elif self.aggregation_method == "episode-period median":
                            agg_val = float(vals.median())
                        elif self.aggregation_method == "episode-period maximum":
                            agg_val = float(vals.max())
                        elif self.aggregation_method == "latest valid observation":
                            agg_val = float(vals.iloc[-1])
                        else:
                            agg_val = float(vals.mean())
                        return agg_val, obs_count, val_count, source_files, source_records
                return None, obs_count, val_count, source_files, source_records

        # Try patient_flow_kpi_daily
        df = self._patient_flow_df
        if df is not None and not df.empty:
            mask = (
                (df["hospital_id"] == hospital_id)
                & (df["department_id"] == department_id)
                & (df["kpi_id"] == kpi_id)
                & (df["reporting_date"] >= start.strftime("%Y-%m-%d"))
                & (df["reporting_date"] <= end.strftime("%Y-%m-%d"))
            )
            subset = df[mask]
            if not subset.empty:
                obs_count = len(subset)
                valid_mask = subset["calculation_status"].str.strip() == "Calculated"
                valid = subset[valid_mask]
                val_count = len(valid)
                source_files = ["analytical_patient_flow_kpi_daily.csv"] * obs_count
                source_records = subset["analytical_record_id"].tolist()
                if not valid.empty:
                    vals = valid["kpi_value"].apply(_to_float).dropna()
                    if not vals.empty:
                        agg_val = float(vals.mean())
                        return agg_val, obs_count, val_count, source_files, source_records
                return None, obs_count, val_count, source_files, source_records

        return None, 0, 0, [], []

    def _extract_metadata(
        self,
        hospital_id: str,
        department_id: str,
        start_date: str,
        end_date: str,
        kpi_id: str,
    ) -> Tuple[bool, str, str]:
        """Extract provisional flag, contradiction severity, and confidence from source data."""
        df = self._six_kpi_df
        if df is None or df.empty:
            return False, "No Contradiction", "Unavailable"

        start = _parse_date(start_date)
        end = _parse_date(end_date)
        if start is None and end is None:
            return False, "No Contradiction", "Unavailable"
        if start is None:
            start = end
        if end is None:
            end = start

        mask = (
            (df["hospital_id"] == hospital_id)
            & (df["department_id"] == department_id)
            & (df["kpi_id"] == kpi_id)
            & (df["reporting_date"] >= start.strftime("%Y-%m-%d"))
            & (df["reporting_date"] <= end.strftime("%Y-%m-%d"))
        )
        subset = df[mask]
        if subset.empty:
            return False, "No Contradiction", "Unavailable"

        # Check for provisional threshold
        provisional = False
        if "threshold_is_provisional" in subset.columns:
            prov_vals = subset["threshold_is_provisional"].apply(lambda x: str(x).lower() == "true")
            provisional = bool(prov_vals.any())

        # Use data_confidence_level as confidence indicator
        confidence = "Unavailable"
        if "data_confidence_level" in subset.columns:
            confs = subset["data_confidence_level"].dropna().unique()
            if len(confs) > 0:
                confidence = str(confs[0])

        return provisional, "No Contradiction", confidence

    def _make_baseline_id(
        self, package_id: str, episode_id: str, template_id: str, start_date: str, end_date: str
    ) -> str:
        """Generate deterministic baseline ID."""
        raw = f"{package_id}|{episode_id}|{template_id}|{start_date}|{end_date}|{self.aggregation_method}"
        return f"BL-{hashlib.sha256(raw.encode()).hexdigest()[:16].upper()}"

    def build_all_baselines(
        self, mapping_df: pd.DataFrame, episode_df: pd.DataFrame
    ) -> List[ScenarioBaseline]:
        """Build baselines for all required quantitative mappings."""
        baselines: List[ScenarioBaseline] = []
        if mapping_df.empty or episode_df.empty:
            return baselines

        # Only build for packages that are Required or Recommended
        eligible = mapping_df[
            mapping_df["review_status"].isin(["Required", "Recommended"])
        ].copy()

        for _, row in eligible.iterrows():
            package_id = row.get("approval_package_id", "")
            template_id = row.get("scenario_template_id", "")
            episode_id = row.get("episode_id", "")

            # Find episode
            ep_match = episode_df[episode_df["episode_id"] == episode_id]
            if ep_match.empty:
                continue

            episode = ep_match.iloc[0].to_dict()
            baseline = self.build_baseline(row.to_dict(), episode)
            baselines.append(baseline)

        return baselines

    def build_all_baselines_for_all_mappings(
        self, mapping_df: pd.DataFrame, episode_df: pd.DataFrame
    ) -> List[ScenarioBaseline]:
        """Build baselines for every mapped row (including monitoring-only)."""
        baselines: List[ScenarioBaseline] = []
        if mapping_df.empty or episode_df.empty:
            return baselines

        for _, row in mapping_df.iterrows():
            package_id = row.get("approval_package_id", "")
            template_id = row.get("scenario_template_id", "")
            episode_id = row.get("episode_id", "")

            ep_match = episode_df[episode_df["episode_id"] == episode_id]
            if ep_match.empty:
                continue

            episode = ep_match.iloc[0].to_dict()
            baseline = self.build_baseline(row.to_dict(), episode)
            baselines.append(baseline)

        return baselines

    def baselines_to_dataframe(self, baselines: List[ScenarioBaseline]) -> pd.DataFrame:
        """Convert baseline list to DataFrame."""
        if not baselines:
            return pd.DataFrame()
        rows = []
        for bl in baselines:
            rows.append({
                "baseline_id": bl.baseline_id,
                "approval_package_id": bl.approval_package_id,
                "episode_id": bl.episode_id,
                "scenario_template_id": bl.scenario_template_id,
                "hospital_id": bl.hospital_id,
                "department_id": bl.department_id,
                "episode_start_date": bl.episode_start_date,
                "episode_end_date": bl.episode_end_date,
                "dominant_kpi_id": bl.dominant_kpi_id,
                "dominant_kpi_name": bl.dominant_kpi_name,
                "baseline_kpi_value": bl.baseline_kpi_value,
                "baseline_kpi_unit": bl.baseline_kpi_unit,
                "supporting_kpi_values_json": json.dumps(bl.supporting_kpi_values),
                "baseline_required_staff": bl.baseline_required_staff,
                "baseline_available_staff": bl.baseline_available_staff,
                "baseline_staffing_coverage_pct": bl.baseline_staffing_coverage_pct,
                "baseline_absenteeism_rate": bl.baseline_absenteeism_rate,
                "baseline_avg_wait_min": bl.baseline_avg_wait_min,
                "baseline_arrivals": bl.baseline_arrivals,
                "baseline_service_capacity": bl.baseline_service_capacity,
                "source_file_list": ",".join(bl.source_file_list),
                "source_record_id_list": ",".join(bl.source_record_id_list),
                "baseline_observation_count": bl.baseline_observation_count,
                "baseline_data_completeness": round(bl.baseline_data_completeness, 2),
                "baseline_confidence": bl.baseline_confidence,
                "baseline_provisional_flag": bl.baseline_provisional_flag,
                "baseline_contradiction_severity": bl.baseline_contradiction_severity,
                "baseline_status": bl.baseline_status.value,
                "baseline_created_at": bl.baseline_created_at,
                "baseline_version": bl.baseline_version,
                "baseline_aggregation_method": bl.baseline_aggregation_method,
                "baseline_reference_date": bl.baseline_reference_date,
                "baseline_window_start": bl.baseline_window_start,
                "baseline_window_end": bl.baseline_window_end,
            })
        return pd.DataFrame(rows)
