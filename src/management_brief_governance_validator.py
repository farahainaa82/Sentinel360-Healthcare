"""Governance validation engine for Step 2D-7."""

import pandas as pd


PROHIBITED_WORDS = [
    "AI Recommendation", "Best Scenario", "Optimal Action", "Final Decision",
    "Guaranteed Savings", "Proven Cause", "Will Improve", "Will Save",
    "Action Selected", "Management Reviewed"
]
# "Approved" is checked separately to allow "not approved" / "no recommendation has been approved"
APPROVED_PATTERNS = ["approved", "approval"]
APPROVED_ALLOWED_PREFIXES = ["not ", "no ", "pending ", "awaiting ", "without "]


def validate_governance(briefs_df):
    """Validate governance constraints and return governance register."""
    records = []
    issues = []
    for _, row in briefs_df.iterrows():
        brief_id = row.get("integrated_management_brief_id", "")
        checks = {}
        checks["no_preferred_scenario_selected"] = str(row.get("selected_scenario", "")) == "" or str(row.get("selected_scenario", "")).lower() == "nan"
        checks["no_action_selected"] = str(row.get("selected_action", "")) == "" or str(row.get("selected_action", "")).lower() == "nan"
        checks["no_recommendation_approved"] = str(row.get("approval_status", "")) == "Pending Management Review"
        checks["no_budget_approved"] = str(row.get("budget_approved", "")) == "" or str(row.get("budget_approved", "")).lower() == "nan"
        checks["no_management_review_fabricated"] = str(row.get("review_status", "")) == "" or "Pending" in str(row.get("review_status", ""))
        checks["causality_not_confirmed"] = str(row.get("causality_status", "")) == "Not Confirmed"
        checks["approval_status_pending"] = str(row.get("approval_status", "")) == "Pending Management Review"

        # Check prohibited wording in text fields
        text_fields = ["brief_title", "executive_headline", "one_line_summary", "short_summary"]
        prohibited_found = []
        for field in text_fields:
            val = str(row.get(field, "")).lower()
            for word in PROHIBITED_WORDS:
                if word.lower() in val:
                    prohibited_found.append(word)
            # Check "approved" / "approval" only if not in a negated context
            for pat in APPROVED_PATTERNS:
                start = 0
                while True:
                    idx = val.find(pat, start)
                    if idx == -1:
                        break
                    prefix = val[max(0, idx - 30):idx]
                    negated = any(p in prefix for p in APPROVED_ALLOWED_PREFIXES) or "been " in prefix
                    if not negated:
                        prohibited_found.append(pat)
                        break
                    start = idx + len(pat)
        checks["no_prohibited_wording"] = len(prohibited_found) == 0

        all_passed = all(checks.values())
        records.append({
            "integrated_management_brief_id": brief_id,
            "decision_package_id": row.get("decision_package_id", ""),
            **checks,
            "governance_passed": all_passed,
            "prohibited_words_found": "; ".join(prohibited_found) if prohibited_found else "",
            "governance_note": "All governance checks passed" if all_passed else "Governance issues detected"
        })

        if not all_passed:
            issues.append({
                "integrated_management_brief_id": brief_id,
                "issue_type": "Governance Violation",
                "issue_description": "; ".join([k for k, v in checks.items() if not v]),
                "governance_note": "Requires review"
            })

    return pd.DataFrame(records), pd.DataFrame(issues)
