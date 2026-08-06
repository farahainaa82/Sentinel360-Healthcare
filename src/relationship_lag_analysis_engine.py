"""Relationship Lag Analysis Engine — Step 2B-4."""

import os
import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime, timedelta

from relationship_analysis_models import (
    TemporalInterpretation, KPI_NAMES, ALL_KPI_IDS, UNIQUE_PAIRS,
)


class RelationshipLagAnalysisEngine:
    """Analyse temporal precedence between KPI pairs."""

    def __init__(self, config_dir=None, inputs_dir=None, engine_run_id=None):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        self.config_dir = config_dir or os.path.join(project_root, "config")
        self.inputs_dir = inputs_dir or os.path.join(project_root, "data/analytical")
        self.engine_run_id = engine_run_id or f"LAG-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.processed_at = datetime.utcnow().isoformat()
        self._load_configs()
        self._load_inputs()

    def _load_configs(self):
        lag_cfg = pd.read_csv(os.path.join(self.config_dir, "relationship_lag_config.csv"))
        def get_param(df, name, default):
            mask = df["parameter_name"] == name
            return float(df.loc[mask, "parameter_value"].iloc[0]) if mask.any() else default
        self.lag_values = sorted([int(get_param(lag_cfg, f"lag_{v}_period", v)) for v in [0, 1, 2, 3]])
        self.lag_min_obs = int(get_param(lag_cfg, "lag_minimum_observations", 8))

    def _load_inputs(self):
        self.six_kpi = pd.read_csv(os.path.join(self.inputs_dir, "analytical_six_kpi_daily.csv"))
        self.six_kpi["reporting_date"] = pd.to_datetime(self.six_kpi["reporting_date"])
        self.classification = pd.read_csv(os.path.join(self.inputs_dir, "analytical_kpi_threshold_classification_daily.csv"))
        self.classification["reporting_date"] = pd.to_datetime(self.classification["reporting_date"])

    def _lag_correlation(self, src, tgt, lag_periods):
        """Shift target backward by lag_periods and correlate."""
        if lag_periods == 0:
            merged = pd.merge(src, tgt, on="reporting_date", suffixes=("_src", "_tgt"))
        else:
            tgt_shifted = tgt.copy()
            tgt_shifted["reporting_date"] = tgt_shifted["reporting_date"] - timedelta(days=lag_periods)
            merged = pd.merge(src, tgt_shifted, on="reporting_date", suffixes=("_src", "_tgt"))
        if len(merged) < self.lag_min_obs:
            return np.nan, len(merged)
        r, _ = stats.pearsonr(merged["kpi_value_src"].values, merged["kpi_value_tgt"].values)
        return round(r, 4), len(merged)

    def _temporal_precedence(self, src_cls, tgt_cls, lag_periods):
        """Count source-adverse before target-adverse at given lag."""
        if lag_periods == 0:
            merged = pd.merge(src_cls, tgt_cls, on="reporting_date", suffixes=("_src", "_tgt"))
        else:
            tgt_shifted = tgt_cls.copy()
            tgt_shifted["reporting_date"] = tgt_shifted["reporting_date"] - timedelta(days=lag_periods)
            merged = pd.merge(src_cls, tgt_shifted, on="reporting_date", suffixes=("_src", "_tgt"))
        if len(merged) == 0:
            return np.nan, 0, 0

        def adverse(state):
            return state in ["Amber", "Red", "Critical Capacity Pressure", "Low Utilisation"]

        src_adv = merged["threshold_state_src"].apply(adverse)
        tgt_adv = merged["threshold_state_tgt"].apply(adverse)
        src_before_tgt = (src_adv & ~tgt_adv).sum()  # simplified proxy
        total_adv = (src_adv | tgt_adv).sum()
        rate = src_before_tgt / total_adv if total_adv > 0 else np.nan
        return round(rate, 4), int(src_before_tgt), int(total_adv)

    def analyse_lag_relationships(self):
        records = []
        hospitals = self.six_kpi["hospital_id"].unique()
        for hid in hospitals:
            hdf = self.six_kpi[self.six_kpi["hospital_id"] == hid]
            hcls = self.classification[self.classification["hospital_id"] == hid]
            departments = hdf["department_id"].unique()

            for did in departments:
                ddf = hdf[hdf["department_id"] == did]
                dcls = hcls[hcls["department_id"] == did]
                for src_kpi, tgt_kpi in UNIQUE_PAIRS:
                    src = ddf[ddf["kpi_id"] == src_kpi][["reporting_date", "kpi_value"]].sort_values("reporting_date")
                    tgt = ddf[ddf["kpi_id"] == tgt_kpi][["reporting_date", "kpi_value"]].sort_values("reporting_date")
                    src_cls = dcls[dcls["kpi_id"] == src_kpi][["reporting_date", "threshold_state"]]
                    tgt_cls = dcls[dcls["kpi_id"] == tgt_kpi][["reporting_date", "threshold_state"]]
                    if src.empty or tgt.empty:
                        continue

                    best_lag = 0
                    best_corr = np.nan
                    best_n = 0
                    precedence_rates = {}
                    for lag in self.lag_values:
                        corr, n = self._lag_correlation(src, tgt, lag)
                        if not pd.isna(corr) and (pd.isna(best_corr) or abs(corr) > abs(best_corr)):
                            best_corr = corr
                            best_lag = lag
                            best_n = n
                        prec_rate, _, _ = self._temporal_precedence(src_cls, tgt_cls, lag)
                        precedence_rates[lag] = prec_rate

                    prec_best = precedence_rates.get(best_lag, np.nan)
                    # Reverse direction
                    rev_corr, rev_n = self._lag_correlation(tgt, src, best_lag)
                    rev_prec, _, _ = self._temporal_precedence(tgt_cls, src_cls, best_lag)

                    if not pd.isna(prec_best) and not pd.isna(rev_prec):
                        if prec_best > 0.55 and rev_prec <= 0.45:
                            interp = TemporalInterpretation.SOURCE_FREQUENTLY_PRECEDES_TARGET
                        elif rev_prec > 0.55 and prec_best <= 0.45:
                            interp = TemporalInterpretation.TARGET_FREQUENTLY_PRECEDES_SOURCE
                        elif prec_best > 0.55 and rev_prec > 0.55:
                            interp = TemporalInterpretation.BIDIRECTIONAL_OR_MIXED
                        elif best_lag == 0:
                            interp = TemporalInterpretation.SAME_PERIOD_ASSOCIATION
                        else:
                            interp = TemporalInterpretation.NO_TEMPORAL_PATTERN
                    elif best_lag == 0 and not pd.isna(best_corr):
                        interp = TemporalInterpretation.SAME_PERIOD_ASSOCIATION
                    else:
                        interp = TemporalInterpretation.INSUFFICIENT_EVIDENCE

                    records.append({
                        "lag_record_id": f"{self.engine_run_id}-{hid}-{did}-{src_kpi}-{tgt_kpi}",
                        "relationship_id": f"{src_kpi}_{tgt_kpi}",
                        "hospital_id": hid,
                        "department_id": did,
                        "source_kpi_id": src_kpi,
                        "source_kpi_name": KPI_NAMES.get(src_kpi, src_kpi),
                        "target_kpi_id": tgt_kpi,
                        "target_kpi_name": KPI_NAMES.get(tgt_kpi, tgt_kpi),
                        "best_supported_lag": best_lag,
                        "lag_unit": "days",
                        "lagged_correlation": best_corr,
                        "lagged_observation_count": best_n,
                        "reverse_lagged_correlation": rev_corr,
                        "temporal_precedence_rate": prec_best,
                        "reverse_temporal_precedence_rate": rev_prec,
                        "temporal_interpretation": interp.value,
                        "engine_run_id": self.engine_run_id,
                        "processed_at": self.processed_at,
                    })
        return pd.DataFrame(records)

    def run(self):
        return self.analyse_lag_relationships()
