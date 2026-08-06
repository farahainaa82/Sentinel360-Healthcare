"""KPI Relationship Analysis Engine — Step 2B-4."""

import os
import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime

from relationship_analysis_models import (
    RelationshipDirection, RelationshipStrength, StabilityClassification,
    TemporalStability, DataSufficiency, ConfidenceLevel, ContradictionSeverity,
    KPI_ADVERSITY_DIRECTION, KPI_NAMES, ALL_KPI_IDS, UNIQUE_PAIRS,
)


class KPIRelationshipAnalysisEngine:
    """Analyse pairwise relationships among the six KPIs."""

    def __init__(self, config_dir=None, inputs_dir=None, engine_run_id=None):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        self.config_dir = config_dir or os.path.join(project_root, "config")
        self.inputs_dir = inputs_dir or os.path.join(project_root, "data/analytical")
        self.engine_run_id = engine_run_id or f"REL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.processed_at = datetime.utcnow().isoformat()
        self.configs = {}
        self._load_configs()
        self._load_inputs()

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    def _load_configs(self):
        self.configs["method"] = pd.read_csv(os.path.join(self.config_dir, "relationship_method_config.csv"))
        self.configs["strength"] = pd.read_csv(os.path.join(self.config_dir, "relationship_strength_config.csv"))
        self.configs["stability"] = pd.read_csv(os.path.join(self.config_dir, "relationship_stability_config.csv"))
        self.configs["confidence"] = pd.read_csv(os.path.join(self.config_dir, "relationship_confidence_config.csv"))
        self.configs["lag"] = pd.read_csv(os.path.join(self.config_dir, "relationship_lag_config.csv"))
        self.configs["contradiction"] = pd.read_csv(os.path.join(self.config_dir, "relationship_contradiction_rule_config.csv"))

        def get_param(df, name, default):
            if df is None or df.empty:
                return default
            mask = df["parameter_name"] == name
            if not mask.any():
                return default
            return float(df.loc[mask, "parameter_value"].iloc[0])

        self.min_paired_obs = int(get_param(self.configs["method"], "minimum_paired_observations", 10))
        self.min_paired_obs_limited = int(get_param(self.configs["method"], "minimum_paired_observations_limited", 5))
        self.sig_level = get_param(self.configs["method"], "significance_level", 0.05)

        self.str_none = get_param(self.configs["strength"], "strength_none_upper", 0.15)
        self.str_weak = get_param(self.configs["strength"], "strength_weak_upper", 0.35)
        self.str_mod = get_param(self.configs["strength"], "strength_moderate_upper", 0.55)
        self.str_strong = get_param(self.configs["strength"], "strength_strong_upper", 0.75)
        self.str_min_obs = int(get_param(self.configs["strength"], "strength_min_observations", 15))

        self.dept_min_depts = int(get_param(self.configs["stability"], "department_min_departments", 3))
        self.dept_consistency = get_param(self.configs["stability"], "department_consistency_threshold", 0.70)
        self.dept_moderate = get_param(self.configs["stability"], "department_moderate_threshold", 0.50)
        self.time_min_periods = int(get_param(self.configs["stability"], "time_min_periods", 2))
        self.time_consistency = get_param(self.configs["stability"], "time_consistency_threshold", 0.70)

        self.conf_high_min = int(get_param(self.configs["confidence"], "high_confidence_min_obs", 20))
        self.conf_high_agr = get_param(self.configs["confidence"], "high_confidence_method_agreement", 0.80)
        self.conf_mod_min = int(get_param(self.configs["confidence"], "moderate_confidence_min_obs", 10))
        self.conf_low_min = int(get_param(self.configs["confidence"], "low_confidence_min_obs", 5))

    # ------------------------------------------------------------------
    # Inputs
    # ------------------------------------------------------------------
    def _load_inputs(self):
        self.six_kpi = pd.read_csv(os.path.join(self.inputs_dir, "analytical_six_kpi_daily.csv"))
        self.six_kpi["reporting_date"] = pd.to_datetime(self.six_kpi["reporting_date"])
        self.classification = pd.read_csv(os.path.join(self.inputs_dir, "analytical_kpi_threshold_classification_daily.csv"))
        self.classification["reporting_date"] = pd.to_datetime(self.classification["reporting_date"])
        self.risk_scores = pd.read_csv(os.path.join(self.inputs_dir, "analytical_kpi_risk_scores_daily.csv"))
        self.risk_scores["reporting_date"] = pd.to_datetime(self.risk_scores["reporting_date"])
        self.trend_signals = pd.read_csv(os.path.join(self.inputs_dir, "analytical_kpi_trend_signals.csv"))
        self.trend_signals["reporting_date"] = pd.to_datetime(self.trend_signals["reporting_date"])
        self.dept_risk = pd.read_csv(os.path.join(self.inputs_dir, "analytical_department_risk_daily.csv"))
        self.dept_risk["reporting_date"] = pd.to_datetime(self.dept_risk["reporting_date"])
        self.governance = pd.read_csv(os.path.join(self.inputs_dir, "analytical_department_risk_governance.csv"))
        self.governance["reporting_date"] = pd.to_datetime(self.governance["reporting_date"])

    # ------------------------------------------------------------------
    # Adversity transformation
    # ------------------------------------------------------------------
    def _adversity_score(self, df):
        """Add adversity_score column: higher = worse operational condition."""
        # Merge risk scores for dual_sided KPIs
        risk = self.risk_scores[["hospital_id", "department_id", "reporting_date", "kpi_id", "kpi_risk_score_normalized"]].copy()
        df = df.merge(risk, on=["hospital_id", "department_id", "reporting_date", "kpi_id"], how="left")

        def transform(row):
            kpi = row["kpi_id"]
            direction = KPI_ADVERSITY_DIRECTION.get(kpi, "lower_is_better")
            val = row["kpi_value"]
            if direction == "lower_is_better":
                return val
            elif direction == "higher_is_better":
                return -val
            else:
                # dual_sided: use normalized risk score as adversity proxy
                return row.get("kpi_risk_score_normalized", 0.0)

        df = df.copy()
        df["adversity_score"] = df.apply(transform, axis=1)
        return df

    # ------------------------------------------------------------------
    # Pairwise correlation per grain
    # ------------------------------------------------------------------
    def _correlate_pair(self, merged):
        """Compute Pearson, Spearman, direction agreement for a merged pair dataframe."""
        # Drop rows with NaN in any key column before correlation
        merged = merged.dropna(subset=["kpi_value_src", "kpi_value_tgt", "adversity_score_src", "adversity_score_tgt"])
        n = len(merged)
        if n < self.min_paired_obs_limited:
            return {
                "pearson": np.nan, "spearman": np.nan,
                "direction_agreement_rate": np.nan,
                "adversity_pearson": np.nan, "adversity_spearman": np.nan,
                "pearson_pvalue": np.nan, "spearman_pvalue": np.nan,
                "paired_observations": n, "sufficiency": DataSufficiency.INSUFFICIENT,
            }

        try:
            pearson_r, pearson_p = stats.pearsonr(merged["kpi_value_src"].values, merged["kpi_value_tgt"].values)
        except Exception:
            pearson_r, pearson_p = np.nan, np.nan
        try:
            spearman_r, spearman_p = stats.spearmanr(merged["kpi_value_src"].values, merged["kpi_value_tgt"].values)
        except Exception:
            spearman_r, spearman_p = np.nan, np.nan

        try:
            adv_pearson_r, _ = stats.pearsonr(merged["adversity_score_src"].values, merged["adversity_score_tgt"].values)
        except Exception:
            adv_pearson_r = np.nan
        try:
            adv_spearman_r, _ = stats.spearmanr(merged["adversity_score_src"].values, merged["adversity_score_tgt"].values)
        except Exception:
            adv_spearman_r = np.nan

        # Direction agreement: same sign of day-to-day change
        src_diff = np.diff(merged["kpi_value_src"].values)
        tgt_diff = np.diff(merged["kpi_value_tgt"].values)
        agreement = np.mean((src_diff * tgt_diff) > 0) if len(src_diff) > 0 else np.nan

        if n >= self.min_paired_obs:
            suff = DataSufficiency.SUFFICIENT
        else:
            suff = DataSufficiency.LIMITED

        return {
            "pearson": round(pearson_r, 4),
            "spearman": round(spearman_r, 4),
            "pearson_pvalue": round(pearson_p, 6),
            "spearman_pvalue": round(spearman_p, 6),
            "direction_agreement_rate": round(agreement, 4),
            "adversity_pearson": round(adv_pearson_r, 4),
            "adversity_spearman": round(adv_spearman_r, 4),
            "paired_observations": n,
            "sufficiency": suff,
        }

    # ------------------------------------------------------------------
    # Main pairwise analysis
    # ------------------------------------------------------------------
    def analyse_pairwise_relationships(self):
        """Generate pairwise relationship records at department and pooled grains."""
        kpi_df = self._adversity_score(self.six_kpi.copy())
        records = []

        hospitals = kpi_df["hospital_id"].unique()
        for hid in hospitals:
            hdf = kpi_df[kpi_df["hospital_id"] == hid]
            departments = hdf["department_id"].unique()

            # Per-department analysis
            for did in departments:
                ddf = hdf[hdf["department_id"] == did]
                for src_kpi, tgt_kpi in UNIQUE_PAIRS:
                    src = ddf[ddf["kpi_id"] == src_kpi].sort_values("reporting_date")
                    tgt = ddf[ddf["kpi_id"] == tgt_kpi].sort_values("reporting_date")
                    merged = pd.merge(src, tgt, on="reporting_date", suffixes=("_src", "_tgt"))
                    if merged.empty:
                        continue
                    corr = self._correlate_pair(merged)
                    rec = self._build_relationship_record(
                        hid, did, src_kpi, tgt_kpi, corr, merged, grain="department"
                    )
                    records.append(rec)

            # Pooled across departments within hospital — merge on dept + date to prevent cross-dept leakage
            for src_kpi, tgt_kpi in UNIQUE_PAIRS:
                src = hdf[hdf["kpi_id"] == src_kpi][["department_id", "reporting_date", "kpi_value", "adversity_score"]].sort_values(["department_id", "reporting_date"])
                tgt = hdf[hdf["kpi_id"] == tgt_kpi][["department_id", "reporting_date", "kpi_value", "adversity_score"]].sort_values(["department_id", "reporting_date"])
                merged = pd.merge(src, tgt, on=["department_id", "reporting_date"], suffixes=("_src", "_tgt"), how="inner")
                if merged.empty:
                    continue
                corr = self._correlate_pair(merged)
                rec = self._build_relationship_record(
                    hid, "ALL", src_kpi, tgt_kpi, corr, merged, grain="hospital"
                )
                records.append(rec)

        return pd.DataFrame(records)

    def _build_relationship_record(self, hid, did, src_kpi, tgt_kpi, corr, merged, grain):
        pearson = corr.get("pearson", np.nan)
        spearman = corr.get("spearman", np.nan)
        adv_pearson = corr.get("adversity_pearson", np.nan)
        n = corr.get("paired_observations", 0)
        suff = corr.get("sufficiency", DataSufficiency.INSUFFICIENT)

        raw_dir = self._classify_direction(pearson, spearman, n)
        adv_dir = self._classify_direction(adv_pearson, adv_pearson, n)
        raw_str = self._classify_strength(pearson, n)
        adv_str = self._classify_strength(adv_pearson, n)

        # Adversity co-occurrence from threshold classifications
        cooc = self._cooccurrence_for_pair(hid, did, src_kpi, tgt_kpi, grain)
        trend = self._trend_for_pair(hid, did, src_kpi, tgt_kpi, grain)

        start_date = merged["reporting_date"].min().strftime("%Y-%m-%d") if not merged.empty else ""
        end_date = merged["reporting_date"].max().strftime("%Y-%m-%d") if not merged.empty else ""

        return {
            "relationship_record_id": f"{self.engine_run_id}-{hid}-{did}-{src_kpi}-{tgt_kpi}",
            "relationship_id": f"{src_kpi}_{tgt_kpi}",
            "hospital_id": hid,
            "department_id": did,
            "analysis_period_start": start_date,
            "analysis_period_end": end_date,
            "source_kpi_id": src_kpi,
            "source_kpi_name": KPI_NAMES.get(src_kpi, src_kpi),
            "target_kpi_id": tgt_kpi,
            "target_kpi_name": KPI_NAMES.get(tgt_kpi, tgt_kpi),
            "grain": grain,
            "possible_observation_count": len(merged),
            "paired_observation_count": n,
            "paired_availability_rate": round(n / max(len(merged), 1), 4),
            "sufficiency_status": suff.value,
            "pearson_correlation": pearson,
            "spearman_correlation": spearman,
            "pearson_pvalue": corr.get("pearson_pvalue", np.nan),
            "spearman_pvalue": corr.get("spearman_pvalue", np.nan),
            "raw_relationship_direction": raw_dir.value,
            "raw_relationship_strength": raw_str.value,
            "adversity_correlation": adv_pearson,
            "adversity_relationship_direction": adv_dir.value,
            "adversity_relationship_strength": adv_str.value,
            "direction_agreement_rate": corr.get("direction_agreement_rate", np.nan),
            "both_assessable_count": cooc.get("both_assessable", 0),
            "both_green_count": cooc.get("both_green", 0),
            "either_amber_count": cooc.get("either_amber", 0),
            "both_amber_or_worse_count": cooc.get("both_amber_or_worse", 0),
            "either_red_or_worse_count": cooc.get("either_red_or_worse", 0),
            "both_red_or_worse_count": cooc.get("both_red_or_worse", 0),
            "adverse_cooccurrence_rate": cooc.get("adverse_cooccurrence_rate", np.nan),
            "conditional_adverse_rate": cooc.get("conditional_adverse_rate", np.nan),
            "reverse_conditional_adverse_rate": cooc.get("reverse_conditional_adverse_rate", np.nan),
            "trend_agreement_rate": trend.get("trend_agreement_rate", np.nan),
            "both_deteriorating_count": trend.get("both_deteriorating", 0),
            "opposing_trend_count": trend.get("opposing_trend", 0),
            "engine_run_id": self.engine_run_id,
            "processed_at": self.processed_at,
            "issue_flag": False,
        }

    def _classify_direction(self, pearson, spearman, n):
        if n < self.min_paired_obs_limited or (pd.isna(pearson) and pd.isna(spearman)):
            return RelationshipDirection.INSUFFICIENT_EVIDENCE
        r = pearson if not pd.isna(pearson) else spearman
        if pd.isna(r):
            return RelationshipDirection.INSUFFICIENT_EVIDENCE
        if r > 0.2:
            return RelationshipDirection.POSITIVE
        if r < -0.2:
            return RelationshipDirection.NEGATIVE
        if abs(r) <= 0.2:
            return RelationshipDirection.NONE_DETECTED
        return RelationshipDirection.MIXED

    def _classify_strength(self, r, n):
        if n < self.min_paired_obs_limited or pd.isna(r):
            return RelationshipStrength.INSUFFICIENT_EVIDENCE
        a = abs(r)
        if n < self.str_min_obs and a >= self.str_strong:
            return RelationshipStrength.MODERATE
        if a <= self.str_none:
            return RelationshipStrength.NONE
        if a <= self.str_weak:
            return RelationshipStrength.WEAK
        if a <= self.str_mod:
            return RelationshipStrength.MODERATE
        if a <= self.str_strong:
            return RelationshipStrength.STRONG
        return RelationshipStrength.VERY_STRONG

    # ------------------------------------------------------------------
    # Co-occurrence
    # ------------------------------------------------------------------
    def _cooccurrence_for_pair(self, hid, did, src_kpi, tgt_kpi, grain):
        cdf = self.classification.copy()
        cdf = cdf[cdf["hospital_id"] == hid]
        if grain == "department":
            cdf = cdf[cdf["department_id"] == did]

        src = cdf[cdf["kpi_id"] == src_kpi][["reporting_date", "threshold_state"]].rename(columns={"threshold_state": "src_state"})
        tgt = cdf[cdf["kpi_id"] == tgt_kpi][["reporting_date", "threshold_state"]].rename(columns={"threshold_state": "tgt_state"})
        merged = pd.merge(src, tgt, on="reporting_date")
        if merged.empty:
            return {}

        def adverse(state):
            return state in ["Amber", "Red", "Critical Capacity Pressure", "Low Utilisation"]

        def red_or_worse(state):
            return state in ["Red", "Critical Capacity Pressure"]

        both_assessable = len(merged)
        both_green = ((merged["src_state"] == "Green") & (merged["tgt_state"] == "Green")).sum()
        either_amber = ((merged["src_state"] == "Amber") | (merged["tgt_state"] == "Amber")).sum()
        both_amber_or_worse = (merged["src_state"].apply(adverse) & merged["tgt_state"].apply(adverse)).sum()
        either_red = (merged["src_state"].apply(red_or_worse) | merged["tgt_state"].apply(red_or_worse)).sum()
        both_red = (merged["src_state"].apply(red_or_worse) & merged["tgt_state"].apply(red_or_worse)).sum()

        adverse_rate = both_amber_or_worse / both_assessable if both_assessable > 0 else np.nan
        cond_src = merged[merged["src_state"].apply(adverse)]
        cond_rate = (cond_src["tgt_state"].apply(adverse)).sum() / len(cond_src) if len(cond_src) > 0 else np.nan
        cond_tgt = merged[merged["tgt_state"].apply(adverse)]
        rev_rate = (cond_tgt["src_state"].apply(adverse)).sum() / len(cond_tgt) if len(cond_tgt) > 0 else np.nan

        return {
            "both_assessable": int(both_assessable),
            "both_green": int(both_green),
            "either_amber": int(either_amber),
            "both_amber_or_worse": int(both_amber_or_worse),
            "either_red_or_worse": int(either_red),
            "both_red_or_worse": int(both_red),
            "adverse_cooccurrence_rate": round(adverse_rate, 4),
            "conditional_adverse_rate": round(cond_rate, 4),
            "reverse_conditional_adverse_rate": round(rev_rate, 4),
        }

    # ------------------------------------------------------------------
    # Trend alignment
    # ------------------------------------------------------------------
    def _trend_for_pair(self, hid, did, src_kpi, tgt_kpi, grain):
        tdf = self.trend_signals.copy()
        tdf = tdf[tdf["hospital_id"] == hid]
        if grain == "department":
            tdf = tdf[tdf["department_id"] == did]

        src = tdf[tdf["kpi_id"] == src_kpi][["reporting_date", "signal_direction"]].rename(columns={"signal_direction": "src_trend"})
        tgt = tdf[tdf["kpi_id"] == tgt_kpi][["reporting_date", "signal_direction"]].rename(columns={"signal_direction": "tgt_trend"})
        merged = pd.merge(src, tgt, on="reporting_date")
        if merged.empty:
            return {}

        # Map signal_direction to adversity-aligned trend for agreement checking
        def to_adversity_trend(row, kpi):
            direction = KPI_ADVERSITY_DIRECTION.get(kpi, "lower_is_better")
            sig = row
            if sig in ["none", "", np.nan]:
                return "Stable"
            if direction == "lower_is_better":
                return "Deteriorating" if sig == "positive" else "Improving" if sig == "negative" else "Volatile"
            elif direction == "higher_is_better":
                return "Improving" if sig == "positive" else "Deteriorating" if sig == "negative" else "Volatile"
            else:
                return "Deteriorating" if sig == "positive" else "Improving" if sig == "negative" else "Volatile"

        merged["src_adv_trend"] = merged["src_trend"].apply(lambda x: to_adversity_trend(x, src_kpi))
        merged["tgt_adv_trend"] = merged["tgt_trend"].apply(lambda x: to_adversity_trend(x, tgt_kpi))

        both_deteriorating = ((merged["src_adv_trend"] == "Deteriorating") & (merged["tgt_adv_trend"] == "Deteriorating")).sum()
        both_improving = ((merged["src_adv_trend"] == "Improving") & (merged["tgt_adv_trend"] == "Improving")).sum()
        opposing = (
            ((merged["src_adv_trend"] == "Deteriorating") & (merged["tgt_adv_trend"] == "Improving")) |
            ((merged["src_adv_trend"] == "Improving") & (merged["tgt_adv_trend"] == "Deteriorating"))
        ).sum()
        agreement = (merged["src_adv_trend"] == merged["tgt_adv_trend"]).sum()
        rate = agreement / len(merged) if len(merged) > 0 else np.nan

        return {
            "both_deteriorating": int(both_deteriorating),
            "both_improving": int(both_improving),
            "opposing_trend": int(opposing),
            "trend_agreement_rate": round(rate, 4),
        }

    # ------------------------------------------------------------------
    # Department stability
    # ------------------------------------------------------------------
    def analyse_department_stability(self, pair_df):
        """Aggregate per-pair department results to assess stability."""
        dept_df = pair_df[pair_df["grain"] == "department"].copy()
        if dept_df.empty:
            return pd.DataFrame()

        results = []
        for rel_id, group in dept_df.groupby("relationship_id"):
            # Use adversity_correlation if available, else fall back to pearson_correlation
            group["corr_for_stability"] = group["adversity_correlation"].fillna(group["pearson_correlation"])
            group = group.dropna(subset=["corr_for_stability"])
            total = len(group)
            if total == 0:
                continue
            pos = (group["corr_for_stability"] > 0.1).sum()
            neg = (group["corr_for_stability"] < -0.1).sum()
            none_det = (group["corr_for_stability"].abs() <= 0.1).sum()

            majority_dir = "positive" if pos >= neg else "negative"
            same_dir = pos if majority_dir == "positive" else neg
            consistency = same_dir / total if total > 0 else 0

            if total >= self.dept_min_depts and consistency >= self.dept_consistency:
                stab = StabilityClassification.STABLE_ACROSS_DEPARTMENTS
            elif total >= self.dept_min_depts and consistency >= self.dept_moderate:
                stab = StabilityClassification.MODERATELY_STABLE
            elif total < self.dept_min_depts:
                stab = StabilityClassification.INSUFFICIENT_EVIDENCE
            elif consistency < 0.3:
                stab = StabilityClassification.UNSTABLE
            else:
                stab = StabilityClassification.DEPARTMENT_SPECIFIC

            simpsons = (group["raw_relationship_direction"] != group["adversity_relationship_direction"]).any()

            pooled = pair_df[(pair_df["relationship_id"] == rel_id) & (pair_df["grain"] == "hospital")]
            pooled_adv = pooled["adversity_correlation"].values[0] if not pooled.empty else np.nan
            if pd.isna(pooled_adv) and not pooled.empty:
                pooled_adv = pooled["pearson_correlation"].values[0]

            results.append({
                "relationship_id": rel_id,
                "source_kpi_id": group["source_kpi_id"].iloc[0],
                "target_kpi_id": group["target_kpi_id"].iloc[0],
                "departments_assessed": total,
                "departments_positive": int(pos),
                "departments_negative": int(neg),
                "departments_none_detected": int(none_det),
                "direction_consistency_rate": round(consistency, 4),
                "median_department_correlation": round(group["corr_for_stability"].median(), 4),
                "department_stability": stab.value,
                "simpsons_paradox_risk_flag": bool(simpsons),
                "pooled_correlation": round(pooled_adv, 4) if not pd.isna(pooled_adv) else np.nan,
                "engine_run_id": self.engine_run_id,
                "processed_at": self.processed_at,
            })
        return pd.DataFrame(results)

    # ------------------------------------------------------------------
    # Confidence
    # ------------------------------------------------------------------
    def assign_confidence(self, pair_df, stability_df):
        """Assign confidence levels to relationship records."""
        pair_df = pair_df.copy()
        confidences = []
        for _, row in pair_df.iterrows():
            n = row.get("paired_observation_count", 0)
            pearson = row.get("pearson_correlation", np.nan)
            spearman = row.get("spearman_correlation", np.nan)
            suff = row.get("sufficiency_status", "Insufficient")

            if n < self.conf_low_min or suff == "Not Assessable":
                confidences.append(ConfidenceLevel.INSUFFICIENT_EVIDENCE.value)
                continue

            method_agr = abs(pearson - spearman) if not (pd.isna(pearson) or pd.isna(spearman)) else 1.0
            method_agr_ok = method_agr <= (1 - self.conf_high_agr)

            if n >= self.conf_high_min and method_agr_ok:
                confidences.append(ConfidenceLevel.HIGH.value)
            elif n >= self.conf_mod_min:
                confidences.append(ConfidenceLevel.MODERATE.value)
            else:
                confidences.append(ConfidenceLevel.LOW.value)

        pair_df["confidence_level"] = confidences
        return pair_df

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------
    def run(self):
        pairwise = self.analyse_pairwise_relationships()
        stability = self.analyse_department_stability(pairwise)
        pairwise = self.assign_confidence(pairwise, stability)
        return pairwise, stability
