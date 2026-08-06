"""
Step 2C-2E Validation Scorecard Engine.
Generates transparent validation scorecards for all packages.
Computes Scenario Validation Index (SVI) from component scores.
"""

import pandas as pd
from scenario_validation_base_engine import ValidationEngineBase


class ValidationScorecardEngine(ValidationEngineBase):
    def __init__(self, **kwargs):
        super().__init__(engine_name="validation_scorecard", **kwargs)

    def run(
        self,
        baseline_validation: pd.DataFrame,
        assumption_challenge: pd.DataFrame,
        numerical_validation: pd.DataFrame,
        comparator_validation: pd.DataFrame,
        dominance_validation: pd.DataFrame,
        sensitivity_validation: pd.DataFrame,
        displacement_validation: pd.DataFrame,
        diminishing_returns_validation: pd.DataFrame,
        interpretation_validation: pd.DataFrame,
        runs: pd.DataFrame,
    ) -> pd.DataFrame:
        packages = runs["approval_package_id"].unique()
        results = []

        for pkg in packages:
            # Baseline score
            bl = baseline_validation[baseline_validation["approval_package_id"] == pkg]
            baseline_score = self._score_baseline(bl)

            # Assumption score
            ass = assumption_challenge[assumption_challenge["approval_package_id"] == pkg]
            assumption_score = self._score_assumption(ass)

            # Numerical score
            num = numerical_validation[numerical_validation["approval_package_id"] == pkg]
            numerical_score = self._score_numerical(num)

            # Comparator score
            comp = comparator_validation[comparator_validation["approval_package_id"] == pkg]
            comparator_score = self._score_comparator(comp)

            # Dominance score
            dom = dominance_validation[dominance_validation["approval_package_id"] == pkg]
            dominance_score = self._score_dominance(dom)

            # Sensitivity score
            sens = sensitivity_validation[sensitivity_validation["approval_package_id"] == pkg]
            sensitivity_score = self._score_sensitivity(sens)

            # Displacement score
            disp = displacement_validation[displacement_validation["approval_package_id"] == pkg]
            displacement_score = self._score_displacement(disp)

            # Diminishing returns score
            dr = diminishing_returns_validation[diminishing_returns_validation["approval_package_id"] == pkg]
            dr_score = self._score_diminishing_returns(dr)

            # Interpretation score
            interp = interpretation_validation[interpretation_validation["approval_package_id"] == pkg]
            interpretation_score = self._score_interpretation(interp)

            # Composite score (Scenario Validation Index)
            scores = [
                baseline_score, assumption_score, numerical_score,
                comparator_score, dominance_score, sensitivity_score,
                displacement_score, dr_score, interpretation_score
            ]
            svi = sum(scores) / len(scores)

            classification = self._classify_svi(svi)

            results.append({
                "approval_package_id": pkg,
                "scenario_validation_index": round(svi, 3),
                "baseline_validity_score": baseline_score,
                "assumption_plausibility_score": assumption_score,
                "numerical_integrity_score": numerical_score,
                "comparator_consistency_score": comparator_score,
                "dominance_validity_score": dominance_score,
                "sensitivity_robustness_score": sensitivity_score,
                "displacement_support_score": displacement_score,
                "diminishing_returns_validity_score": dr_score,
                "interpretation_validity_score": interpretation_score,
                "validation_classification": classification,
                "engine_name": self.engine_name,
                "engine_version": self.engine_version,
                "run_timestamp": self.run_timestamp,
            })

            self.add_lineage(None, "package", pkg, "analytical_scenario_runs.csv")

        df = pd.DataFrame(results)
        self.write_output(df, "analytical_scenario_validation_scorecard.csv")
        return df

    def _score_baseline(self, df: pd.DataFrame) -> float:
        if df.empty:
            return 0.0
        valid = df["validation_status"].isin(["Valid", "Valid with Conditions"]).sum()
        return valid / len(df)

    def _score_assumption(self, df: pd.DataFrame) -> float:
        if df.empty:
            return 0.0
        valid = df["challenge_status"].isin(["Passed", "Passed with Flags"]).sum()
        return valid / len(df)

    def _score_numerical(self, df: pd.DataFrame) -> float:
        if df.empty:
            return 0.0
        valid = df["validation_status"].isin(["Valid", "Valid with Conditions"]).sum()
        return valid / len(df)

    def _score_comparator(self, df: pd.DataFrame) -> float:
        if df.empty:
            return 0.0
        valid = df["validation_status"].isin(["Consistent", "Consistent with Flags"]).sum()
        return valid / len(df)

    def _score_dominance(self, df: pd.DataFrame) -> float:
        if df.empty:
            return 0.0
        valid = df["validation_status"].isin(["Valid", "Downgraded"]).sum()
        return valid / len(df)

    def _score_sensitivity(self, df: pd.DataFrame) -> float:
        if df.empty:
            return 0.0
        valid = df["validation_status"].isin(["Valid", "Flagged"]).sum()
        return valid / len(df)

    def _score_displacement(self, df: pd.DataFrame) -> float:
        if df.empty:
            return 0.0
        valid = df["validation_status"].isin(["Supported", "Plausible with Conditions"]).sum()
        return valid / len(df)

    def _score_diminishing_returns(self, df: pd.DataFrame) -> float:
        if df.empty:
            return 0.0
        valid = df["validation_status"].isin([
            "Confirmed Diminishing Improvement",
            "Confirmed Proportionate Improvement",
            "Confirmed Flat Response",
            "Confirmed Adverse Reversal",
        ]).sum()
        return valid / len(df)

    def _score_interpretation(self, df: pd.DataFrame) -> float:
        if df.empty:
            return 0.0
        valid = (df["validation_status"] == "Valid").sum()
        return valid / len(df)

    def _classify_svi(self, svi: float) -> str:
        if svi >= 0.85:
            return "Strong Validation"
        if svi >= 0.7:
            return "Acceptable with Conditions"
        if svi >= 0.5:
            return "Weak Validation"
        if svi > 0:
            return "Failed Validation"
        return "Not Assessable"
