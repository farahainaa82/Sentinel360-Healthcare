"""
Decision Status Engine for Phase 2D-1.

Assigns exactly one integrated decision status per approval package.
"""

import pandas as pd
import numpy as np


class DecisionStatusEngine:
    STATUS_CATEGORIES = [
        "Ready for Integrated Management Review",
        "Ready with Conditions",
        "Requires Assumption Validation",
        "Requires Baseline Validation",
        "Requires Financial Input",
        "Requires Stakeholder Validation",
        "Requires Additional Scenario Analysis",
        "Monitoring Only",
        "Non-Quantitative",
        "Not Suitable for Decision Use",
        "Rejected",
    ]

    def assign_status(self, df: pd.DataFrame) -> pd.DataFrame:
        """Assign one status per row based on governed rules."""
        records = []
        for _, row in df.iterrows():
            status = self._determine_status(row)
            records.append({
                "integrated_decision_id": row.get("integrated_decision_id", ""),
                "approval_package_id": row.get("approval_package_id", ""),
                "decision_status": status,
                "decision_status_reason": self._status_reason(row, status),
            })
        return pd.DataFrame(records)

    def _determine_status(self, row) -> str:
        closure = str(row.get("closure_category", ""))
        deferred = str(row.get("deferred_closure_category", ""))
        scenario_ready = str(row.get("scenario_readiness", ""))
        financial_ready = str(row.get("financial_readiness", ""))
        mgmt_pkg_id = row.get("management_scenario_package_id", "")
        comparator_comp = str(row.get("comparator_completeness", ""))
        gov_count = row.get("governance_issue_count", 0)
        if pd.isna(gov_count):
            gov_count = 0
        try:
            gov_count = int(gov_count)
        except (ValueError, TypeError):
            gov_count = 0

        # Rejected or excluded
        if "Rejected" in closure or "Rejected" in deferred:
            return "Rejected"
        if "Not Suitable" in closure or "Not Suitable" in deferred:
            return "Not Suitable for Decision Use"

        # Monitoring Only
        if "Monitoring" in closure or "Monitoring" in deferred or "Monitoring" in scenario_ready:
            return "Monitoring Only"

        # Non-Quantitative
        if "Non-Quantitative" in closure or "Non-Quantitative" in deferred:
            return "Non-Quantitative"

        # Requires Assumption Validation
        if "Assumption" in closure or "Assumption" in deferred or "Assumption" in scenario_ready:
            return "Requires Assumption Validation"

        # Requires Baseline Validation
        if "Baseline" in closure or "Baseline" in scenario_ready:
            return "Requires Baseline Validation"

        # Requires Additional Scenario Analysis
        if pd.isna(mgmt_pkg_id) or mgmt_pkg_id == "":
            if "Scenario" in closure or "Scenario" in deferred:
                return "Requires Additional Scenario Analysis"

        # Requires Financial Input
        if "financial" in financial_ready.lower() and "not ready" in financial_ready.lower():
            return "Requires Financial Input"

        # Requires Stakeholder Validation
        if "stakeholder" in str(row.get("stakeholder_validation_required", "")).lower():
            return "Requires Stakeholder Validation"

        # Ready for Integrated Management Review (strict)
        if (pd.notna(mgmt_pkg_id) and mgmt_pkg_id != "" and
            "Ready" in scenario_ready and
            ("Complete" in comparator_comp or "Sufficient" in comparator_comp) and
            gov_count == 0):
            return "Ready for Integrated Management Review"

        # Ready with Conditions (fallback for packages with some analysis but conditions remain)
        if pd.notna(mgmt_pkg_id) and mgmt_pkg_id != "":
            return "Ready with Conditions"

        # Default fallback
        return "Ready with Conditions"

    def _status_reason(self, row, status: str) -> str:
        reasons = {
            "Ready for Integrated Management Review": "All core analysis complete, comparator consistency verified, no material governance issues.",
            "Ready with Conditions": "Core analysis available with remaining validation or financial conditions.",
            "Requires Assumption Validation": "Scenario assumptions require stakeholder review before decision use.",
            "Requires Baseline Validation": "Baseline comparator requires validation.",
            "Requires Financial Input": "Financial analysis incomplete — missing cost or benefit inputs.",
            "Requires Stakeholder Validation": "Stakeholder validation required for assumptions or ranges.",
            "Requires Additional Scenario Analysis": "Management scenario package not yet built; additional scenario analysis needed.",
            "Monitoring Only": "Package does not justify active intervention; observation recommended.",
            "Non-Quantitative": "Cannot support quantitative scenario or financial comparison.",
            "Not Suitable for Decision Use": "Package excluded from decision use.",
            "Rejected": "Package rejected from decision process.",
        }
        return reasons.get(status, "Status assigned per governed rules.")
