"""
Decision Integration Key Validator for Phase 2D-1.

Validates join keys across upstream files to prevent Cartesian joins.
"""

import pandas as pd
from typing import Dict, List


class DecisionIntegrationKeyValidator:
    def validate_join_keys(self, inputs: Dict[str, pd.DataFrame]) -> Dict[str, dict]:
        """
        inputs: dict of {name: DataFrame}
        Returns: dict of validation results per key.
        """
        results = {}

        # Validate approval_package_id uniqueness where expected
        for name, df in inputs.items():
            if "approval_package_id" in df.columns:
                dup_count = df.duplicated(subset=["approval_package_id"], keep=False).sum()
                results[f"{name}.approval_package_id"] = {
                    "unique": dup_count == 0,
                    "duplicate_count": int(dup_count),
                    "total_rows": len(df),
                }

            if "scenario_run_id" in df.columns:
                dup_count = df.duplicated(subset=["scenario_run_id"], keep=False).sum()
                results[f"{name}.scenario_run_id"] = {
                    "unique": dup_count == 0,
                    "duplicate_count": int(dup_count),
                    "total_rows": len(df),
                }

            if "management_scenario_package_id" in df.columns:
                dup_count = df.duplicated(subset=["management_scenario_package_id"], keep=False).sum()
                results[f"{name}.management_scenario_package_id"] = {
                    "unique": dup_count == 0,
                    "duplicate_count": int(dup_count),
                    "total_rows": len(df),
                }

        return results

    def estimate_merge_size(self, left: pd.DataFrame, right: pd.DataFrame, left_on: str, right_on: str) -> int:
        """Estimate expected merge size to detect Cartesian explosion."""
        if left_on not in left.columns or right_on not in right.columns:
            return -1
        left_counts = left[left_on].value_counts()
        right_counts = right[right_on].value_counts()
        common_keys = set(left_counts.index) & set(right_counts.index)
        estimated = sum(left_counts[k] * right_counts[k] for k in common_keys)
        return int(estimated)
